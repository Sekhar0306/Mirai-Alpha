"""
LLM extraction using GPT-4o mini
This handles weird PDF formats that the other methods struggle with
"""
import logging
from typing import List, Dict, Optional
from pathlib import Path
import pdfplumber
from openai import OpenAI
import json
import re

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_MAX_TOKENS, USE_LLM_EXTRACTION

# Also try loading from .env directly as fallback
try:
    from dotenv import load_dotenv
    import os
    load_dotenv()
    # Use .env value if config didn't load it
    if not OPENAI_API_KEY:
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
except:
    pass

logger = logging.getLogger(__name__)


class LLMExtractor:
    """Extracts holdings data using GPT-4o mini"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.client = None
        
        if not USE_LLM_EXTRACTION:
            logger.debug("LLM extraction is disabled in config")
            return
        
        # Get API key - try multiple sources
        api_key = OPENAI_API_KEY
        if not api_key or api_key == "":
            # Try loading from .env directly
            try:
                from dotenv import load_dotenv
                import os
                load_dotenv()
                api_key = os.getenv("OPENAI_API_KEY", "")
            except:
                pass
        
        if not api_key or api_key == "":
            logger.warning("OpenAI API key not configured")
            return
            
        try:
            # Initialize OpenAI client
            self.client = OpenAI(api_key=api_key)
            logger.debug("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            self.client = None
        
    def extract(self) -> List[Dict]:
        """
        Extract holdings using LLM
        Returns list of holdings dictionaries
        """
        if not self.client:
            logger.warning("OpenAI API key not configured, skipping LLM extraction")
            return []
        
        try:
            logger.info(f"Starting LLM extraction for {self.pdf_path.name}")
            
            # Extract text from PDF
            text_content = self._extract_pdf_text()
            
            if not text_content:
                logger.warning("No text content extracted from PDF")
                return []
            
            # Use LLM to extract holdings
            holdings = self._extract_with_llm(text_content)
            
            if holdings:
                logger.info(f"Successfully extracted {len(holdings)} holdings using LLM")
                return holdings
            else:
                logger.warning("LLM extraction returned no holdings")
                return []
                
        except Exception as e:
            logger.error(f"LLM extraction failed: {str(e)}")
            return []
    
    def _extract_pdf_text(self) -> str:
        """Get text from PDF - only first 10 pages to save tokens"""
        try:
            text_parts = []
            with pdfplumber.open(self.pdf_path) as pdf:
                # Usually holdings are in first few pages, no need to process everything
                for page in pdf.pages[:10]:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"Couldn't extract text: {str(e)}")
            return ""
    
    def _extract_with_llm(self, text_content: str) -> List[Dict]:
        """Use GPT-4o mini to extract holdings from text"""
        try:
            # Truncate text if too long (keep first part which usually has holdings)
            max_chars = 15000  # Leave room for prompt and response
            if len(text_content) > max_chars:
                text_content = text_content[:max_chars] + "\n\n[... content truncated ...]"
            
            prompt = self._create_extraction_prompt(text_content)
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at extracting mutual fund portfolio holdings data from factsheets. Extract holdings in structured JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=OPENAI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            # Extract holdings from response
            holdings = self._parse_llm_response(result_json)
            
            return holdings
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {str(e)}")
            # Try to extract JSON from text if it's wrapped
            try:
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group(0))
                    return self._parse_llm_response(result_json)
            except:
                pass
            return []
        except Exception as e:
            logger.error(f"Error in LLM extraction: {str(e)}")
            return []
    
    def _create_extraction_prompt(self, text_content: str) -> str:
        """Build the prompt for the LLM"""
        return f"""Extract mutual fund portfolio holdings from this factsheet.

What to look for:
- Portfolio Holdings table with individual stocks/securities
- Company/security names
- Sectors
- Market values (in rupees)
- Percentage of AUM
- ISIN codes (if present)
- Quantities (if present)

If this is just a summary with sector allocations (not individual holdings), return empty holdings array.

Return JSON in this format:
{{
    "holdings": [
        {{
            "security_name": "Company Name",
            "isin": "ISIN if available",
            "sector": "Sector",
            "market_value": 12345678.90,
            "%_of_aum": 5.5,
            "quantity": 1000000
        }}
    ],
    "metadata": {{
        "date": "YYYY-MM-DD",
        "amc": "AMC name",
        "fund_name": "Fund name",
        "note": "Any notes"
    }}
}}

PDF text:
{text_content}

Extract all holdings. If no individual holdings table, return empty array."""
    
    def _parse_llm_response(self, result_json: Dict) -> List[Dict]:
        """Parse LLM JSON response into holdings list"""
        holdings = []
        
        if "holdings" in result_json and isinstance(result_json["holdings"], list):
            for holding in result_json["holdings"]:
                if isinstance(holding, dict):
                    # Normalize the holding data
                    normalized = {
                        "security_name": holding.get("security_name", ""),
                        "isin": holding.get("isin", ""),
                        "sector": holding.get("sector", "Unknown"),
                        "market_value": self._safe_float(holding.get("market_value")),
                        "%_of_aum": self._safe_float(holding.get("%_of_aum")),
                        "quantity": self._safe_float(holding.get("quantity")),
                        "extraction_method": "llm",
                        "confidence": 0.95  # High confidence for LLM extraction
                    }
                    
                    # Only add if we have at least security name
                    if normalized["security_name"]:
                        holdings.append(normalized)
        
        return holdings
    
    def _safe_float(self, value: any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove commas and other formatting
                cleaned = value.replace(',', '').replace('₹', '').replace('Rs.', '').replace('%', '').strip()
                return float(cleaned)
            return None
        except:
            return None


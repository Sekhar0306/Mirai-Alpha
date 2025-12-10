"""
PDF extraction module - handles various factsheet formats
Tried multiple libraries because different AMCs format their PDFs differently
"""
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path
import pdfplumber  # Works well for most text-based PDFs
import pandas as pd
from tabula import read_pdf  # Good fallback, but needs Java
import fitz  # PyMuPDF - sometimes better than pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)

# Try to import LLM extractor - optional dependency
try:
    from extractors.llm_extractor import LLMExtractor
    LLM_AVAILABLE = True
except ImportError as e:
    LLM_AVAILABLE = False
    # Not critical if LLM isn't available, we have other methods
    logger.debug(f"LLM extractor not available: {str(e)}")


class PDFExtractor:
    """Extracts holdings data from mutual fund factsheet PDFs using multiple methods"""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.extraction_log = []
        
    def extract(self) -> List[Dict]:
        """
        Main extraction method - tries different approaches until one works
        Returns list of holdings or empty list if nothing found
        """
        logger.info(f"Processing: {self.pdf_path.name}")
        
        # LLM works great for weird formats, but costs money so try others first
        # Actually, let's try LLM first since it handles complex cases better
        if LLM_AVAILABLE:
            try:
                llm_extractor = LLMExtractor(str(self.pdf_path))
                result = llm_extractor.extract()
                if result and len(result) > 0 and self._validate_extraction(result):
                    logger.info(f"Got {len(result)} holdings using LLM")
                    return result
            except Exception as e:
                logger.debug(f"LLM didn't work: {e}, trying other methods")
        
        # pdfplumber is usually reliable for standard tables
        result = self._extract_with_pdfplumber()
        if result and len(result) > 0 and self._validate_extraction(result):
            logger.info(f"Extracted {len(result)} holdings with pdfplumber")
            return result
        
        # tabula sometimes catches tables that pdfplumber misses
        result = self._extract_with_tabula()
        if result and len(result) > 0 and self._validate_extraction(result):
            logger.info(f"Extracted {len(result)} holdings with tabula")
            return result
        
        # Last resort - OCR for scanned PDFs (slow and less accurate)
        result = self._extract_with_ocr()
        if result and len(result) > 0:
            logger.warning(f"Used OCR - got {len(result)} holdings (may have errors)")
            return result
        
        # Nothing worked
        logger.error(f"Couldn't extract from {self.pdf_path.name}")
        logger.info("Tip: Make sure it's a complete factsheet with holdings table, not just a summary")
        return []
    
    def _extract_with_pdfplumber(self) -> List[Dict]:
        """Extract using pdfplumber - usually works well"""
        try:
            holdings = []
            with pdfplumber.open(self.pdf_path) as pdf:
                # Check first few pages (holdings are usually at the start or end)
                # Some PDFs have 50+ pages but holdings might be on page 2-5
                pages_to_check = min(len(pdf.pages), 10)  # Don't waste time on huge PDFs
                
                for page_num in range(pages_to_check):
                    page = pdf.pages[page_num]
                    tables = page.extract_tables()
                    
                    # Process each table found
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        parsed = self._parse_table_pdfplumber(table, page_num)
                        if parsed:
                            holdings.extend(parsed)
                    
                    # Sometimes tables don't extract cleanly, try text parsing
                    text = page.extract_text()
                    if text and 'holding' in text.lower():
                        text_holdings = self._parse_text_for_holdings(text, page_num)
                        if text_holdings:
                            holdings.extend(text_holdings)
            
            # Remove duplicates (sometimes same holding appears multiple times)
            return self._deduplicate_holdings(holdings)
        except Exception as e:
            logger.error(f"pdfplumber error: {str(e)}")
            return []
    
    def _extract_with_tabula(self) -> List[Dict]:
        """Extract using tabula-py - good for table detection"""
        try:
            all_holdings = []
            
            # Try to extract all tables
            tables = read_pdf(str(self.pdf_path), pages='all', multiple_tables=True)
            
            for table in tables:
                if table is None or table.empty:
                    continue
                
                parsed = self._parse_table_tabula(table)
                if parsed:
                    all_holdings.extend(parsed)
            
            return self._deduplicate_holdings(all_holdings)
        except Exception as e:
            logger.error(f"tabula extraction failed: {str(e)}")
            return []
    
    def _extract_with_ocr(self) -> List[Dict]:
        """Fallback OCR extraction for scanned PDFs"""
        try:
            # Convert PDF to images
            images = convert_from_path(str(self.pdf_path), dpi=300)
            
            all_text = []
            for img in images:
                text = pytesseract.image_to_string(img)
                all_text.append(text)
            
            # Parse OCR text for holdings
            holdings = []
            for page_num, text in enumerate(all_text):
                parsed = self._parse_text_for_holdings(text, page_num)
                if parsed:
                    holdings.extend(parsed)
            
            # Mark as low confidence
            for holding in holdings:
                holding['extraction_method'] = 'ocr'
                holding['confidence'] = 0.5
            
            return self._deduplicate_holdings(holdings)
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return []
    
    def _parse_table_pdfplumber(self, table: List[List], page_num: int) -> List[Dict]:
        """Parse a table extracted by pdfplumber"""
        if not table or len(table) < 2:
            return []
        
        # Check if this looks like a holdings table
        table_text = ' '.join([str(cell) for row in table[:3] for cell in row if cell]).lower()
        
        # Skip if it's clearly not a holdings table (performance, attribution, etc.)
        skip_keywords = ['performance', 'attribution', 'quartile', 'cagr', 'benchmark', 
                         'months', 'years', 'contributors', 'detractors', 'entries', 'exits']
        if any(keyword in table_text for keyword in skip_keywords):
            return []
        
        # Try to identify header row
        header_row = None
        for i, row in enumerate(table[:5]):  # Check first 5 rows
            if any(self._is_header_cell(cell) for cell in row if cell):
                header_row = i
                break
        
        if header_row is None:
            header_row = 0
        
        headers = [self._clean_cell(cell) for cell in table[header_row]]
        
        # Map headers to our standard fields
        field_mapping = self._map_headers(headers)
        
        # If no good mapping found, try to extract from sector allocation tables
        if not any(field_mapping.values()) and 'sector' in table_text:
            return self._parse_sector_table(table, page_num)
        
        holdings = []
        for row in table[header_row + 1:]:
            if not any(cell for cell in row):  # Skip empty rows
                continue
            
            holding = self._parse_row(row, field_mapping, headers)
            if holding:
                holding['page'] = page_num + 1
                holding['extraction_method'] = 'pdfplumber'
                holding['confidence'] = 0.9
                holdings.append(holding)
        
        return holdings
    
    def _parse_sector_table(self, table: List[List], page_num: int) -> List[Dict]:
        """Parse sector allocation tables when full holdings aren't available"""
        holdings = []
        try:
            # Look for sector allocation pattern: Sector name, percentage
            for row in table[1:]:  # Skip header
                if not row or len(row) < 2:
                    continue
                
                # Try to find sector name and percentage
                sector_name = None
                percentage = None
                
                for cell in row:
                    if not cell:
                        continue
                    cell_str = str(cell).strip()
                    
                    # Check if it's a percentage
                    if '%' in cell_str or (cell_str.replace('.', '').replace('-', '').isdigit() and 
                                           float(cell_str.replace('%', '').replace('--', '0')) < 100):
                        try:
                            pct_val = float(cell_str.replace('%', '').replace('--', '0').strip())
                            if 0 < pct_val <= 100:
                                percentage = pct_val
                        except:
                            pass
                    
                    # Check if it's a sector name (not a number, not empty, reasonable length)
                    elif (len(cell_str) > 3 and len(cell_str) < 50 and 
                          not cell_str.replace('.', '').replace('-', '').isdigit() and
                          cell_str.lower() not in ['sector', 'apr', 'oct', 'ow/uw']):
                        sector_name = cell_str
                
                if sector_name and percentage:
                    holdings.append({
                        'security_name': f'Sector: {sector_name}',
                        'sector': sector_name,
                        '%_of_aum': percentage,
                        'page': page_num + 1,
                        'extraction_method': 'pdfplumber',
                        'confidence': 0.7,
                        'note': 'Sector allocation - full holdings not available in this factsheet'
                    })
        except Exception as e:
            logger.debug(f"Error parsing sector table: {e}")
        
        return holdings
    
    def _parse_table_tabula(self, df: pd.DataFrame) -> List[Dict]:
        """Parse a DataFrame extracted by tabula"""
        if df.empty or len(df.columns) < 3:
            return []
        
        # Clean column names
        df.columns = [self._clean_cell(str(col)) for col in df.columns]
        
        # Map headers
        field_mapping = self._map_headers(list(df.columns))
        
        holdings = []
        for _, row in df.iterrows():
            holding = self._parse_row(list(row), field_mapping, list(df.columns))
            if holding:
                holding['extraction_method'] = 'tabula'
                holding['confidence'] = 0.85
                holdings.append(holding)
        
        return holdings
    
    def _parse_text_for_holdings(self, text: str, page_num: int) -> List[Dict]:
        """Parse free-form text to extract holdings information"""
        holdings = []
        
        # Look for patterns like: "Company Name", "Sector", "%", "Value"
        lines = text.split('\n')
        
        # Try to find holdings section
        holdings_start = -1
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['holdings', 'portfolio', 'equity', 'debt']):
                holdings_start = i
                break
        
        if holdings_start == -1:
            return []
        
        # Parse lines after holdings section
        for line in lines[holdings_start + 1:holdings_start + 100]:
            # Look for patterns with numbers (likely holdings)
            if re.search(r'\d+\.\d+%', line) or re.search(r'\d+,\d+', line):
                # Try to extract holding info
                holding = self._parse_holding_line(line)
                if holding:
                    holding['page'] = page_num + 1
                    holdings.append(holding)
        
        return holdings
    
    def _parse_holding_line(self, line: str) -> Optional[Dict]:
        """Parse a single line that might contain holding information"""
        # This is a simplified parser - can be enhanced
        parts = line.split()
        if len(parts) < 3:
            return None
        
        holding = {}
        
        # Try to extract percentage
        pct_match = re.search(r'(\d+\.\d+)%', line)
        if pct_match:
            holding['%_of_aum'] = float(pct_match.group(1))
        
        # Try to extract value
        value_match = re.search(r'[\d,]+\.?\d*', line)
        if value_match:
            value_str = value_match.group(0).replace(',', '')
            try:
                holding['market_value'] = float(value_str)
            except:
                pass
        
        # Company name is usually at the start
        if parts:
            holding['security_name'] = ' '.join(parts[:3])  # First few words
        
        return holding if holding else None
    
    def _parse_row(self, row: List, field_mapping: Dict, headers: List) -> Optional[Dict]:
        """Parse a single table row into a holding dictionary"""
        holding = {}
        
        for field, col_indices in field_mapping.items():
            for idx in col_indices:
                if idx < len(row) and row[idx]:
                    value = self._clean_cell(row[idx])
                    if value:
                        holding[field] = self._normalize_value(field, value)
                        break
        
        # Must have at least security name and some value
        if 'security_name' in holding and ('%_of_aum' in holding or 'market_value' in holding):
            return holding
        
        return None
    
    def _map_headers(self, headers: List[str]) -> Dict[str, List[int]]:
        """Figure out which column is which - AMCs use different column names"""
        mapping = {
            'security_name': [],
            'isin': [],
            'sector': [],
            'market_value': [],
            '%_of_aum': [],
            'quantity': []
        }
        
        # Common variations I've seen in different factsheets
        header_keywords = {
            'security_name': ['security', 'company', 'name', 'instrument', 'holding', 'stock', 'scrip'],
            'isin': ['isin'],
            'sector': ['sector', 'industry'],
            'market_value': ['value', 'market value', 'amount', 'rupees', 'rs', 'market cap'],
            '%_of_aum': ['%', 'percent', 'percentage', 'weight', 'allocation', 'aum'],
            'quantity': ['quantity', 'qty', 'shares', 'units', 'nos']
        }
        
        for idx, header in enumerate(headers):
            if not header:
                continue
            header_lower = str(header).lower().strip()
            
            # Check if this header matches any of our field keywords
            for field, keywords in header_keywords.items():
                if any(keyword in header_lower for keyword in keywords):
                    mapping[field].append(idx)
                    break  # Found a match, move to next header
        
        return mapping
    
    def _normalize_value(self, field: str, value: str) -> any:
        """Normalize values based on field type"""
        if not value or value == '':
            return None
        
        # Remove common formatting
        value = str(value).strip()
        value = value.replace(',', '').replace('₹', '').replace('Rs.', '').replace('Rs', '')
        value = value.replace('$', '').replace('USD', '').strip()
        
        if field in ['%_of_aum', 'market_value', 'quantity']:
            try:
                # Remove percentage sign if present
                if '%' in value:
                    value = value.replace('%', '').strip()
                return float(value)
            except:
                return None
        
        return value
    
    def _clean_cell(self, cell: any) -> str:
        """Clean a table cell value"""
        if cell is None:
            return ''
        return str(cell).strip()
    
    def _is_header_cell(self, cell: any) -> bool:
        """Check if a cell looks like a header"""
        if not cell:
            return False
        cell_str = str(cell).lower()
        header_keywords = ['security', 'company', 'name', 'sector', '%', 'value', 'isin']
        return any(keyword in cell_str for keyword in header_keywords)
    
    def _deduplicate_holdings(self, holdings: List[Dict]) -> List[Dict]:
        """Remove duplicate holdings based on security name"""
        seen = set()
        unique = []
        
        for holding in holdings:
            key = holding.get('security_name', '').lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(holding)
        
        return unique
    
    def _validate_extraction(self, holdings: List[Dict]) -> bool:
        """Quick check if we got something useful"""
        if not holdings or len(holdings) == 0:
            return False
        
        # Count how many have at least a name and some value
        valid_count = 0
        for h in holdings:
            has_name = h.get('security_name') and len(str(h.get('security_name', '')).strip()) > 2
            has_value = h.get('%_of_aum') or h.get('market_value')
            if has_name and has_value:
                valid_count += 1
        
        # Need at least 1 valid holding (some summary factsheets have very few)
        return valid_count >= 1


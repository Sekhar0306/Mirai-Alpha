"""
Extract AMC name, fund name, and date from PDF filename/content
Tries to be smart about different naming conventions
"""
import re
from typing import Dict, Optional
from pathlib import Path
import pdfplumber
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Tries to figure out AMC, fund name, and date from filename/content"""
    
    # List of common AMC names I've seen
    AMC_PATTERNS = [
        r'(HDFC|ICICI|SBI|Axis|Kotak|Aditya Birla|Franklin|DSP|Nippon|UTI|Reliance|Invesco|Mirae|Motilal|Tata|IDFC|HSBC|PGIM|Edelweiss|Canara|Union|Baroda|BOI|PNB|LIC|Sundaram|Mahindra|Quantum|PPFAS|IIFL|JM|Indiabulls|Essel|L&T|Taurus|Escorts|IDBI|Principal)',
    ]
    
    def extract_from_filename(self, filename: str) -> Dict:
        """Extract metadata from filename pattern: AMC_FundName_YYYYMM.pdf"""
        metadata = {
            'amc': None,
            'fund_name': None,
            'date': None,
            'filename': filename
        }
        
        # Remove extension
        name = Path(filename).stem
        
        # Try to extract date (YYYYMM format)
        date_match = re.search(r'(\d{4})(\d{2})', name)
        if date_match:
            year, month = date_match.groups()
            metadata['date'] = f"{year}-{month}-01"
            name = name[:date_match.start()].strip()
        
        # Split by underscore or other separators
        parts = re.split(r'[_\-\s]+', name)
        
        # First part is usually AMC
        if parts:
            metadata['amc'] = self._normalize_amc_name(parts[0])
        
        # Rest is fund name
        if len(parts) > 1:
            metadata['fund_name'] = ' '.join(parts[1:])
        
        return metadata
    
    def extract_from_content(self, pdf_path: str) -> Dict:
        """Extract metadata from PDF content"""
        metadata = {}
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Read first few pages
                text = ""
                for page in pdf.pages[:3]:
                    text += page.extract_text() or ""
                
                # Extract AMC name
                amc = self._extract_amc_from_text(text)
                if amc:
                    metadata['amc'] = amc
                
                # Extract fund name
                fund_name = self._extract_fund_name_from_text(text)
                if fund_name:
                    metadata['fund_name'] = fund_name
                
                # Extract date
                date = self._extract_date_from_text(text)
                if date:
                    metadata['date'] = date
                
        except Exception as e:
            logger.warning(f"Could not extract metadata from content: {str(e)}")
        
        return metadata
    
    def _extract_amc_from_text(self, text: str) -> Optional[str]:
        """Extract AMC name from text"""
        text_upper = text.upper()
        
        for pattern in self.AMC_PATTERNS:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                return self._normalize_amc_name(match.group(1))
        
        return None
    
    def _extract_fund_name_from_text(self, text: str) -> Optional[str]:
        """Extract fund name from text"""
        # Look for patterns like "Fund Name:", "Scheme Name:"
        patterns = [
            r'(?:Fund|Scheme)\s+Name[:\s]+([A-Z][^\n]{5,50})',
            r'Name of the (?:Fund|Scheme)[:\s]+([A-Z][^\n]{5,50})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract date from text"""
        # Look for date patterns
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Try to parse and format
                try:
                    # This is simplified - can be enhanced
                    return match.group(0)  # Return as found for now
                except:
                    pass
        
        return None
    
    def _normalize_amc_name(self, name: str) -> str:
        """Normalize AMC name"""
        if not name:
            return ''
        
        # Common normalizations
        normalizations = {
            'HDFC': 'HDFC Mutual Fund',
            'ICICI': 'ICICI Prudential Mutual Fund',
            'SBI': 'SBI Mutual Fund',
            'Axis': 'Axis Mutual Fund',
            'Kotak': 'Kotak Mahindra Mutual Fund',
            'Aditya Birla': 'Aditya Birla Sun Life Mutual Fund',
            'Franklin': 'Franklin Templeton Mutual Fund',
            'DSP': 'DSP Mutual Fund',
            'Nippon': 'Nippon India Mutual Fund',
            'UTI': 'UTI Mutual Fund',
            'Reliance': 'Reliance Mutual Fund',
            'Invesco': 'Invesco Mutual Fund',
            'Mirae': 'Mirae Asset Mutual Fund',
            'Motilal': 'Motilal Oswal Mutual Fund',
            'Tata': 'Tata Mutual Fund',
            'IDFC': 'IDFC Mutual Fund',
            'HSBC': 'HSBC Mutual Fund',
            'PGIM': 'PGIM India Mutual Fund',
            'Edelweiss': 'Edelweiss Mutual Fund',
            'Canara': 'Canara Robeco Mutual Fund',
            'Union': 'Union Mutual Fund',
            'Baroda': 'Baroda Mutual Fund',
            'BOI': 'BOI AXA Mutual Fund',
            'PNB': 'PNB Mutual Fund',
            'LIC': 'LIC Mutual Fund',
            'Sundaram': 'Sundaram Mutual Fund',
            'Mahindra': 'Mahindra Mutual Fund',
            'Quantum': 'Quantum Mutual Fund',
            'PPFAS': 'PPFAS Mutual Fund',
            'IIFL': 'IIFL Mutual Fund',
            'JM': 'JM Financial Mutual Fund',
            'Indiabulls': 'Indiabulls Mutual Fund',
            'Essel': 'Essel Mutual Fund',
            'L&T': 'L&T Mutual Fund',
            'Taurus': 'Taurus Mutual Fund',
            'Escorts': 'Escorts Mutual Fund',
            'IDBI': 'IDBI Mutual Fund',
            'Principal': 'Principal Mutual Fund',
        }
        
        name_clean = name.strip().title()
        return normalizations.get(name_clean, name_clean + ' Mutual Fund')


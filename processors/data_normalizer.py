"""
Data normalization - clean up the messy data we extract from PDFs
Different AMCs format things differently, so we need to standardize
"""
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd
import json

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes and validates extracted factsheet data"""
    
    def __init__(self, sector_mapping_path: Optional[str] = None, 
                 isin_mapping_path: Optional[str] = None):
        self.sector_mapping = self._load_sector_mapping(sector_mapping_path)
        self.isin_mapping = self._load_isin_mapping(isin_mapping_path)
    
    def normalize(self, holdings: List[Dict], metadata: Dict) -> List[Dict]:
        """
        Clean up and standardize the extracted holdings
        Adds metadata and normalizes all the fields
        """
        normalized = []
        
        # Fix date format if it has weird spacing
        clean_date = metadata.get('date', '')
        if clean_date:
            clean_date = ' '.join(str(clean_date).split())  # Remove extra whitespace
        
        for holding in holdings:
            # Build normalized holding record
            normalized_holding = {
                'date': clean_date or None,
                'amc': metadata.get('amc'),
                'fund_name': metadata.get('fund_name'),
                'security_name': self._normalize_security_name(holding.get('security_name', '')),
                'isin': self._normalize_isin(holding.get('isin', '')),
                'sector': self._normalize_sector(holding.get('sector', '')),
                'market_value': self._normalize_number(holding.get('market_value')),
                '%_of_aum': self._normalize_number(holding.get('%_of_aum')),
                'quantity': self._normalize_number(holding.get('quantity')),
                'extraction_method': holding.get('extraction_method', 'unknown'),
                'confidence': holding.get('confidence', 0.0)
            }
            
            # Skip if no security name (not useful)
            if normalized_holding['security_name']:
                normalized.append(normalized_holding)
        
        return normalized
    
    def _normalize_security_name(self, name: str) -> str:
        """Clean up company names - remove extra spaces, standardize format"""
        if not name:
            return ''
        
        # Clean up whitespace
        name = ' '.join(name.split())
        
        # Some AMCs write "Ltd" others write "Limited" - standardize
        name = re.sub(r'\s+(Ltd|Limited|Inc|Incorporated|Corp|Corporation)\.?$', '', name, flags=re.IGNORECASE)
        
        # Common variations
        replacements = {
            '&': 'and',
            'Pvt': 'Private',
            'Ltd': 'Limited'
        }
        
        for old, new in replacements.items():
            name = name.replace(old, new)
        
        return name.strip().title()
    
    def _normalize_isin(self, isin: str) -> str:
        """Normalize ISIN codes"""
        if not isin:
            return ''
        
        # ISIN format: 2 letters + 9 alphanumeric + 1 check digit
        isin = str(isin).strip().upper()
        
        # Remove spaces and hyphens
        isin = re.sub(r'[\s-]', '', isin)
        
        # Validate format
        if re.match(r'^[A-Z]{2}[A-Z0-9]{9}\d$', isin):
            return isin
        
        # Try to find ISIN in mapping
        if isin in self.isin_mapping:
            return self.isin_mapping[isin]
        
        return isin
    
    def _normalize_sector(self, sector: str) -> str:
        """Normalize sector names using mapping"""
        if not sector:
            return 'Unknown'
        
        sector = str(sector).strip().title()
        
        # Direct mapping
        if sector in self.sector_mapping:
            return self.sector_mapping[sector]
        
        # Fuzzy matching
        sector_lower = sector.lower()
        for mapped_sector, aliases in self.sector_mapping.items():
            if isinstance(aliases, list):
                if any(alias.lower() in sector_lower or sector_lower in alias.lower() 
                       for alias in aliases):
                    return mapped_sector
        
        # Return original if no mapping found
        return sector
    
    def _normalize_number(self, value: any) -> Optional[float]:
        """Normalize numeric values"""
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        # Convert string to number
        value_str = str(value).strip()
        value_str = value_str.replace(',', '').replace('₹', '').replace('Rs.', '')
        value_str = value_str.replace('$', '').replace('%', '').strip()
        
        try:
            return float(value_str)
        except:
            return None
    
    def validate_aum(self, holdings: List[Dict], expected_aum: Optional[float] = None) -> Dict:
        """
        Check if the percentages add up correctly
        Should be around 100% (give or take 5% for rounding errors)
        """
        total_pct = sum(h.get('%_of_aum', 0) or 0 for h in holdings)
        total_value = sum(h.get('market_value', 0) or 0 for h in holdings)
        
        result = {
            'is_valid': True,
            'total_percentage': total_pct,
            'total_value': total_value,
            'holdings_count': len(holdings),
            'warnings': []
        }
        
        # Check if percentages sum to ~100%
        if total_pct > 0:
            diff = abs(total_pct - 100)
            if diff > 5:  # Allow 5% tolerance for rounding
                result['is_valid'] = False
                result['warnings'].append(
                    f"Total % of AUM is {total_pct:.2f}% (expected ~100%)"
                )
        
        # Warn if no market values (but not critical)
        if total_value == 0 and expected_aum:
            result['warnings'].append("No market values found in holdings")
        
        return result
    
    def _load_sector_mapping(self, path: Optional[str]) -> Dict:
        """Load sector mapping from file or use default"""
        if path and Path(path).exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                logger.warning(f"Could not load sector mapping from {path}")
        
        # Default sector mapping
        return {
            "Financial Services": ["Banking", "Financial", "NBFC", "Insurance"],
            "Technology": ["IT", "Software", "Technology", "Telecom"],
            "Healthcare": ["Pharma", "Pharmaceutical", "Healthcare", "Medical"],
            "Consumer Goods": ["FMCG", "Consumer", "Retail"],
            "Energy": ["Oil", "Gas", "Power", "Energy"],
            "Industrials": ["Industrial", "Engineering", "Infrastructure"],
            "Materials": ["Cement", "Steel", "Metals", "Chemicals"],
            "Automotive": ["Auto", "Automobile", "Transportation"],
            "Real Estate": ["Realty", "Real Estate", "Construction"],
            "Utilities": ["Utilities", "Power", "Electric"],
            "Telecommunications": ["Telecom", "Telecommunications"],
            "Consumer Services": ["Services", "Hospitality", "Entertainment"]
        }
    
    def _load_isin_mapping(self, path: Optional[str]) -> Dict:
        """Load ISIN mapping from file"""
        if path and Path(path).exists():
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except:
                logger.warning(f"Could not load ISIN mapping from {path}")
        
        return {}


class DataAggregator:
    """Aggregates and structures data for analysis"""
    
    @staticmethod
    def to_dataframe(holdings_list: List[List[Dict]]) -> pd.DataFrame:
        """Convert list of holdings lists to a single DataFrame"""
        all_holdings = []
        for holdings in holdings_list:
            all_holdings.extend(holdings)
        
        if not all_holdings:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_holdings)
        
        # Ensure date is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        return df
    
    @staticmethod
    def export_to_csv(df: pd.DataFrame, output_path: str):
        """Export DataFrame to CSV"""
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(df)} records to {output_path}")
    
    @staticmethod
    def export_to_json(df: pd.DataFrame, output_path: str):
        """Export DataFrame to JSON"""
        df.to_json(output_path, orient='records', date_format='iso', indent=2)
        logger.info(f"Exported {len(df)} records to {output_path}")


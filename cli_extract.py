#!/usr/bin/env python3
"""
Command-line tool to extract holdings from PDFs
Usage: python3 cli_extract.py <pdf_file> [options]
"""
import argparse
import sys
from pathlib import Path
import logging
from datetime import datetime

from extractors.pdf_extractor import PDFExtractor
from processors.data_normalizer import DataNormalizer, DataAggregator
from processors.metadata_extractor import MetadataExtractor
from config import OUTPUT_DIR, MAPPINGS_DIR, LOGS_DIR

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'cli_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def process_pdf(pdf_path: Path, normalizer: DataNormalizer, 
                metadata_extractor: MetadataExtractor) -> list:
    """Process one PDF file"""
    try:
        logger.info(f"Processing: {pdf_path.name}")
        
        # Get metadata from filename and PDF content
        metadata = metadata_extractor.extract_from_filename(pdf_path.name)
        content_metadata = metadata_extractor.extract_from_content(str(pdf_path))
        metadata.update({k: v for k, v in content_metadata.items() if v})
        
        # Extract holdings
        extractor = PDFExtractor(str(pdf_path))
        holdings = extractor.extract()
        
        if holdings:
            normalized_holdings = normalizer.normalize(holdings, metadata)
            logger.info(f"Got {len(normalized_holdings)} holdings")
            return normalized_holdings
        else:
            logger.warning(f"No holdings found in {pdf_path.name}")
            return []
    
    except Exception as e:
        logger.error(f"Error with {pdf_path.name}: {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description='Extract holdings data from mutual fund factsheet PDFs'
    )
    parser.add_argument(
        'input',
        type=str,
        help='PDF file path or directory containing PDF files'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(OUTPUT_DIR),
        help='Output directory for extracted data (default: output/)'
    )
    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'both'],
        default='both',
        help='Output format (default: both)'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)
    
    # Initialize processors
    normalizer = DataNormalizer(
        sector_mapping_path=str(MAPPINGS_DIR / "sector_mapping.json"),
        isin_mapping_path=str(MAPPINGS_DIR / "isin_mapping.json")
    )
    metadata_extractor = MetadataExtractor()
    
    # Find PDF files
    if input_path.is_file():
        pdf_files = [input_path] if input_path.suffix.lower() == '.pdf' else []
    else:
        pdf_files = list(input_path.glob("*.pdf"))
    
    if not pdf_files:
        logger.error("No PDF files found")
        sys.exit(1)
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to process")
    
    # Process all PDFs
    all_holdings = []
    for pdf_file in pdf_files:
        holdings = process_pdf(pdf_file, normalizer, metadata_extractor)
        all_holdings.extend(holdings)
    
    if not all_holdings:
        logger.error("No holdings extracted from any files")
        sys.exit(1)
    
    # Create DataFrame
    import pandas as pd
    df = pd.DataFrame(all_holdings)
    
    # Export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.format in ['csv', 'both']:
        csv_path = output_dir / f"holdings_{timestamp}.csv"
        DataAggregator.export_to_csv(df, str(csv_path))
        logger.info(f"✓ CSV exported to: {csv_path}")
    
    if args.format in ['json', 'both']:
        json_path = output_dir / f"holdings_{timestamp}.json"
        DataAggregator.export_to_json(df, str(json_path))
        logger.info(f"✓ JSON exported to: {json_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("EXTRACTION SUMMARY")
    print("="*60)
    print(f"Total Holdings: {len(df)}")
    print(f"Unique Securities: {df['security_name'].nunique()}")
    print(f"AMCs: {df['amc'].nunique()}")
    print(f"Funds: {df['fund_name'].nunique()}")
    if 'date' in df.columns and df['date'].notna().any():
        print(f"Date Range: {df['date'].min()} to {df['date'].max()}")
    print("="*60)


if __name__ == "__main__":
    main()


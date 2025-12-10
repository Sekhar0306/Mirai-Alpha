"""
API server for the extraction system
Built with FastAPI - pretty straightforward REST endpoints
"""
import logging
import sys
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Need this for imports to work
sys.path.insert(0, str(Path(__file__).parent.parent))

from extractors.pdf_extractor import PDFExtractor
from processors.data_normalizer import DataNormalizer, DataAggregator
from processors.metadata_extractor import MetadataExtractor
from config import UPLOAD_DIR, OUTPUT_DIR, LOGS_DIR, MAPPINGS_DIR
import pandas as pd
from datetime import datetime

# Setup logging - write to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Factsheet Extraction API",
    description="Extract holdings data from mutual fund factsheet PDFs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
normalizer = DataNormalizer(
    sector_mapping_path=str(MAPPINGS_DIR / "sector_mapping.json"),
    isin_mapping_path=str(MAPPINGS_DIR / "isin_mapping.json")
)
metadata_extractor = MetadataExtractor()


class ExtractionResponse(BaseModel):
    success: bool
    message: str
    holdings_count: int
    output_files: List[str]
    validation_result: Optional[dict] = None
    warnings: List[str] = []


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Automated Factsheet Extraction System API",
        "version": "1.0.0",
        "endpoints": {
            "extract": "/extract (POST) - Upload PDF and extract holdings",
            "batch_extract": "/batch_extract (POST) - Upload multiple PDFs",
            "health": "/health (GET) - Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/extract", response_model=ExtractionResponse)
async def extract_single_pdf(file: UploadFile = File(..., description="PDF factsheet file")):
    """
    Extract holdings from a single PDF
    """
    try:
        # Save the uploaded file temporarily
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Processing: {file.filename}")
        
        # Try to get metadata from filename and PDF content
        metadata = metadata_extractor.extract_from_filename(file.filename)
        content_metadata = metadata_extractor.extract_from_content(str(file_path))
        metadata.update({k: v for k, v in content_metadata.items() if v})  # Merge both
        
        # Extract the actual holdings
        extractor = PDFExtractor(str(file_path))
        holdings = extractor.extract()
        
        if not holdings:
            # Provide more helpful error message
            error_detail = "Could not extract holdings from PDF.\n\n"
            error_detail += "Possible reasons:\n"
            error_detail += "1. This might be a summary/update factsheet without full holdings table\n"
            error_detail += "2. Missing dependencies (Java for tabula, Poppler for OCR)\n"
            error_detail += "3. OpenAI API key not configured (LLM extraction unavailable)\n\n"
            error_detail += "Solutions:\n"
            error_detail += "- Download the complete monthly factsheet from the AMC website (should have 'Portfolio Holdings' table)\n"
            error_detail += "- Set OPENAI_API_KEY environment variable for LLM extraction\n"
            error_detail += "- Install Java: brew install openjdk (for tabula extraction)\n"
            error_detail += "- Install Poppler: brew install poppler (for OCR extraction)"
            raise HTTPException(status_code=400, detail=error_detail)
        
        # Clean up and normalize the data
        normalized_holdings = normalizer.normalize(holdings, metadata)
        
        # Check if data looks reasonable
        validation = normalizer.validate_aum(normalized_holdings)
        
        # Convert to DataFrame for export
        df = pd.DataFrame(normalized_holdings)
        
        # Save to CSV and JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = OUTPUT_DIR / f"holdings_{timestamp}.csv"
        json_path = OUTPUT_DIR / f"holdings_{timestamp}.json"
        
        DataAggregator.export_to_csv(df, str(csv_path))
        DataAggregator.export_to_json(df, str(json_path))
        
        warnings = []
        if not validation['is_valid']:
            warnings.extend(validation['warnings'])
        
        return ExtractionResponse(
            success=True,
            message=f"Extracted {len(normalized_holdings)} holdings",
            holdings_count=len(normalized_holdings),
            output_files=[csv_path.name, json_path.name],
            validation_result=validation,
            warnings=warnings
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch_extract", response_model=ExtractionResponse)
async def batch_extract(files: List[UploadFile] = File(...)):
    """
    Extract holdings from multiple PDF factsheets
    """
    try:
        all_holdings = []
        warnings = []
        
        for file in files:
            try:
                # Save uploaded file
                file_path = UPLOAD_DIR / file.filename
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                
                logger.info(f"Processing file: {file.filename}")
                
                # Extract metadata
                metadata = metadata_extractor.extract_from_filename(file.filename)
                content_metadata = metadata_extractor.extract_from_content(str(file_path))
                metadata.update({k: v for k, v in content_metadata.items() if v})
                
                # Extract holdings
                extractor = PDFExtractor(str(file_path))
                holdings = extractor.extract()
                
                if holdings:
                    # Normalize data
                    normalized_holdings = normalizer.normalize(holdings, metadata)
                    all_holdings.extend(normalized_holdings)
                else:
                    warnings.append(f"Could not extract data from {file.filename}")
            
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                warnings.append(f"Error processing {file.filename}: {str(e)}")
        
        if not all_holdings:
            raise HTTPException(
                status_code=400,
                detail="Could not extract holdings from any PDF files."
            )
        
        # Create combined DataFrame
        df = pd.DataFrame(all_holdings)
        
        # Generate output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = OUTPUT_DIR / f"holdings_batch_{timestamp}.csv"
        json_path = OUTPUT_DIR / f"holdings_batch_{timestamp}.json"
        
        DataAggregator.export_to_csv(df, str(csv_path))
        DataAggregator.export_to_json(df, str(json_path))
        
        return ExtractionResponse(
            success=True,
            message=f"Successfully extracted {len(all_holdings)} holdings from {len(files)} files",
            holdings_count=len(all_holdings),
            output_files=[csv_path.name, json_path.name],
            warnings=warnings
        )
    
    except Exception as e:
        logger.error(f"Batch extraction failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download extracted data file"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


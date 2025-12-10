"""
Config file - all the paths and settings in one place
"""
import os
from pathlib import Path

# Directory paths
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"
ARCHIVE_DIR = BASE_DIR / "factsheet_archive"
MAPPINGS_DIR = BASE_DIR / "mappings"

# Make sure directories exist
for directory in [UPLOAD_DIR, OUTPUT_DIR, LOGS_DIR, ARCHIVE_DIR, MAPPINGS_DIR]:
    directory.mkdir(exist_ok=True)

# Extraction settings
EXTRACTION_METHODS = ["llm", "pdfplumber", "tabula", "ocr"]  # Order matters - try LLM first
MIN_CONFIDENCE_THRESHOLD = 0.7  # Below this, might want to review manually
MAX_PAGES_TO_PROCESS = 50  # Don't process huge PDFs (usually not needed)

# OpenAI API - using GPT-4o mini (cheaper than GPT-4)
# Set OPENAI_API_KEY environment variable or create .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 4000
USE_LLM_EXTRACTION = True  # Can disable if you don't want to use LLM

# Validation settings
MAX_AUM_TOLERANCE = 0.05  # Allow 5% difference from 100% (rounding errors)
REQUIRED_FIELDS = ["date", "amc", "fund_name", "security_name", "sector", "market_value", "%_of_aum"]

# Supported file formats
ALLOWED_EXTENSIONS = {".pdf"}

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB


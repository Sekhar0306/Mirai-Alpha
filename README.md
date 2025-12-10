# Automated Factsheet Extraction System

A system I built to extract mutual fund holdings data from PDF factsheets. Different AMCs format their PDFs differently, so I tried multiple extraction methods to handle various formats. The output is structured CSV/JSON that you can use directly for analysis.

## What It Does

- **Extracts holdings from PDFs**: Tries multiple methods (pdfplumber, tabula, OCR, and LLM) until one works
- **Normalizes the data**: Maps sectors consistently, cleans up company names, validates percentages
- **Multiple ways to use it**: Web interface, CLI script, Jupyter notebook, or API
- **Outputs clean data**: CSV and JSON files ready for analysis

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Web Interface](#web-interface)
  - [Jupyter Notebook](#jupyter-notebook)
  - [CLI Script](#cli-script)
  - [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Data Format](#data-format)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Installation

### What You Need

- Python 3.8+ (I used 3.9)
- Java (for tabula-py - some PDFs work better with it)
- Tesseract OCR (optional - only needed for scanned PDFs)

### Install Dependencies

**macOS/Linux:**
```bash
pip3 install -r requirements.txt
```

**Windows:**
```bash
pip install -r requirements.txt
```

Note: If you get errors, you might need to install some dependencies separately. The setup script will check this.

### Step 2: Install Java (for tabula-py)

**macOS:**
```bash
brew install openjdk
```

**Linux:**
```bash
sudo apt-get install default-jre
```

**Windows:**
Download and install from [Oracle Java](https://www.oracle.com/java/technologies/downloads/)

### Step 3: Install Tesseract OCR (Optional)

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

### Verify Everything Works

Run the setup script to check:
```bash
python3 setup.py
```

It'll tell you what's missing if anything.

## 🏃 Quick Start

### Option 1: Web Interface (Recommended)

1. **Start the API server:**
   ```bash
   python3 start_server.py
   # or
   python3 -m api.main
   ```

2. **Open the web interface:**
   - Open `frontend/index.html` in your browser
   - Or serve it with a local server:
     ```bash
     cd frontend && python -m http.server 8080
     ```
   - Navigate to `http://localhost:8080`

3. **Upload PDFs and extract:**
   - Drag and drop or select PDF files
   - Click "Extract Holdings Data"
   - Download the structured CSV/JSON output

### Option 2: Jupyter Notebook

1. **Start Jupyter:**
   ```bash
   jupyter notebook
   ```

2. **Open the notebook:**
   - Navigate to `notebooks/extraction_pipeline.ipynb`

3. **Place PDFs:**
   - Copy your PDF factsheets to `factsheet_archive/` directory

4. **Run all cells:**
   - The notebook will process all PDFs and export results

### Option 3: CLI Script

```bash
# Extract from a single PDF
python cli_extract.py path/to/factsheet.pdf

# Extract from a directory
python cli_extract.py path/to/factsheets/

# Specify output directory
python cli_extract.py path/to/factsheet.pdf --output-dir ./my_output

# Export only CSV
python cli_extract.py path/to/factsheet.pdf --format csv
```

## 📖 Usage

### Web Interface

The web interface provides an intuitive drag-and-drop interface for PDF upload and extraction.

**Features:**
- Multiple file upload
- Real-time progress tracking
- Validation results display
- Direct download of extracted data
- Warning and error notifications

### Jupyter Notebook

The notebook (`notebooks/extraction_pipeline.ipynb`) provides an interactive environment for:

- Batch processing multiple PDFs
- Data exploration and validation
- Custom analysis workflows
- Visualization of extraction results

**Usage:**
1. Place PDFs in `factsheet_archive/` directory
2. Run all cells sequentially
3. Review extraction summary and logs
4. Download output files from `output/` directory

### CLI Script

The CLI script (`cli_extract.py`) is ideal for:

- Automated batch processing
- Integration into pipelines
- Server-side processing
- Scripted workflows

**Examples:**
```bash
# Process single file
python3 cli_extract.py HDFC_LargeCap_202401.pdf

# Process directory
python3 cli_extract.py ./factsheets/ --output-dir ./results

# Export JSON only
python3 cli_extract.py ./factsheets/ --format json
```

### API Endpoints

The FastAPI backend provides REST endpoints for programmatic access:

**Base URL:** `http://localhost:8000`

#### 1. Extract Single PDF
```bash
POST /extract
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/extract" \
  -F "file=@factsheet.pdf"
```

#### 2. Batch Extract
```bash
POST /batch_extract
Content-Type: multipart/form-data

curl -X POST "http://localhost:8000/batch_extract" \
  -F "files=@file1.pdf" \
  -F "files=@file2.pdf"
```

#### 3. Download Results
```bash
GET /download/{filename}

curl "http://localhost:8000/download/holdings_20240101_120000.csv" \
  -o holdings.csv
```

#### 4. Health Check
```bash
GET /health

curl "http://localhost:8000/health"
```

## 📁 Project Structure

```
Automated Financals/
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI backend
├── extractors/
│   ├── __init__.py
│   └── pdf_extractor.py        # Multi-method PDF extraction
├── processors/
│   ├── __init__.py
│   ├── data_normalizer.py      # Data normalization & validation
│   └── metadata_extractor.py   # Metadata extraction
├── frontend/
│   └── index.html              # Web UI
├── notebooks/
│   └── extraction_pipeline.ipynb  # Jupyter notebook
├── mappings/
│   ├── sector_mapping.json      # Sector normalization mapping
│   └── isin_mapping.json       # ISIN mapping
├── uploads/                    # Temporary upload directory
├── output/                     # Extracted data output
├── logs/                       # Log files
├── factsheet_archive/          # Archive for PDF factsheets
├── config.py                   # Configuration
├── cli_extract.py              # CLI script
├── requirements.txt             # Python dependencies
├── category_summary.md         # Category documentation
└── README.md                   # This file
```

## 📊 Data Format

### Output Structure

The extracted data is structured with the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `date` | string | Date of factsheet (YYYY-MM-DD) |
| `amc` | string | Asset Management Company name |
| `fund_name` | string | Fund name |
| `security_name` | string | Security/Stock name |
| `isin` | string | ISIN code |
| `sector` | string | Normalized sector name |
| `market_value` | float | Market value in rupees |
| `%_of_aum` | float | Percentage of AUM |
| `quantity` | float | Quantity held |
| `extraction_method` | string | Method used (pdfplumber/tabula/ocr) |
| `confidence` | float | Extraction confidence (0-1) |

### Example Output

```csv
date,amc,fund_name,security_name,isin,sector,market_value,%_of_aum,quantity
2024-01-01,HDFC Mutual Fund,HDFC Large Cap Fund,Reliance Industries Limited,INE002A01018,Energy,1250000000,8.5,5000000
2024-01-01,HDFC Mutual Fund,HDFC Large Cap Fund,TCS Limited,INE467B01029,Technology,1500000000,10.2,3000000
```

## ⚙️ Configuration

Edit `config.py` to customize:

- **Extraction Methods**: Priority order of extraction methods
- **Confidence Threshold**: Minimum confidence for extraction
- **AUM Tolerance**: Tolerance for AUM validation (default: 5%)
- **File Paths**: Directory paths for uploads, output, logs, etc.

### Sector Mapping

Customize sector normalization in `mappings/sector_mapping.json`:

```json
{
  "Financial Services": ["Banking", "Financial", "NBFC"],
  "Technology": ["IT", "Software", "Technology"]
}
```

### ISIN Mapping

Add ISIN mappings in `mappings/isin_mapping.json` for handling variations:

```json
{
  "IN0020101010": "IN0020101010",
  "INE002A01018": "INE002A01018"
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. "No holdings extracted"

**Possible causes:**
- PDF format not supported
- Tables not detected correctly
- PDF is scanned (requires OCR)

**Solutions:**
- Check if PDF is text-based (try copying text)
- Ensure Tesseract OCR is installed for scanned PDFs
- Check logs in `logs/extraction.log` for details

#### 2. "Java not found" (tabula-py error)

**Solution:**
```bash
# Install Java
brew install openjdk  # macOS
sudo apt-get install default-jre  # Linux
```

#### 3. Low extraction confidence

**Solutions:**
- Check PDF quality
- Verify table structure in PDF
- Review extraction logs
- Try different extraction method manually

#### 4. AUM validation fails

**Possible causes:**
- Incomplete extraction
- Multiple tables not merged
- Percentage values not extracted correctly

**Solutions:**
- Check if all holdings pages are processed
- Review extraction logs
- Manually verify PDF content

### Logs

Check logs for detailed error information:

- **API logs**: `logs/extraction.log`
- **CLI logs**: `logs/cli_extraction.log`

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Analysis Capabilities

With the extracted structured data, you can compute:

1. **Sector Exposure Trends**: How sector allocations changed over time
2. **Top Holdings Analysis**: Most common holdings across funds/AMCs
3. **Churn Analysis**: Turnover of holdings month-over-month
4. **Concentration Risk**: Portfolio concentration metrics
5. **Common Holdings**: Securities held across multiple funds/AMCs
6. **Performance Attribution**: Contribution of holdings to fund performance
7. **Persistence Analysis**: How long securities are held
8. **AMC Comparison**: Compare strategies across different AMCs

### Example Analysis Queries

```python
import pandas as pd

# Load extracted data
df = pd.read_csv('output/holdings_20240101_120000.csv')

# Which AMC had highest allocation to Technology in 2020?
tech_2020 = df[(df['sector'] == 'Technology') & 
               (df['date'].str.startswith('2020'))]
tech_2020.groupby('amc')['%_of_aum'].sum().sort_values(ascending=False)

# Common holdings across funds
common_holdings = df.groupby('security_name')['fund_name'].nunique()
common_holdings[common_holdings > 1].sort_values(ascending=False)

# Sector exposure changes over time
sector_trends = df.groupby(['date', 'sector'])['%_of_aum'].sum().unstack()
```

## 🎓 Category Summary

See `category_summary.md` for detailed information about:
- SEBI regulations for equity mutual funds
- Portfolio construction expectations
- Typical holdings styles across AMCs
- Common challenges in extraction

## 📝 File Naming Convention

For best results, name your PDF files as:
```
AMC_FundName_YYYYMM.pdf
```

Examples:
- `HDFC_LargeCap_202401.pdf`
- `ICICI_Prudential_MultiCap_202312.pdf`
- `SBI_BlueChip_202311.pdf`

## 🤝 Contributing

This system is designed to be modular and extensible. Key areas for enhancement:

1. **Extraction Methods**: Add new PDF extraction techniques
2. **Sector Mapping**: Improve sector classification accuracy
3. **Validation**: Add more data quality checks
4. **Visualization**: Add data visualization capabilities

## 📄 License

This project is provided as-is for the purpose of automated factsheet extraction.

## 🆘 Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review the troubleshooting section
3. Verify PDF format and structure
4. Check extraction confidence scores in output

---

**Built for automated extraction of 5 years of historical monthly factsheet data with production-ready quality and comprehensive analysis capabilities.**


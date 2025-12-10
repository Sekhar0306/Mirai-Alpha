#!/usr/bin/env python3
"""
Quick setup check - makes sure everything is installed
"""
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is okay"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Need Python 3.8+")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check if all the Python packages are installed"""
    required = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'pdfplumber': 'pdfplumber',
        'tabula': 'tabula',
        'pandas': 'pandas',
        'pydantic': 'pydantic',
        'pymupdf': 'fitz'  # PyMuPDF uses 'fitz' as import name
    }
    missing = []
    
    for package_name, import_name in required.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - missing")
            missing.append(package_name)
    
    return len(missing) == 0, missing

def check_java():
    """Check if Java is installed (required for tabula-py)"""
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("✓ Java is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  Java is not installed (required for tabula-py)")
    print("   Install with: brew install openjdk (macOS) or apt-get install default-jre (Linux)")
    return False

def check_tesseract():
    """Check if Tesseract OCR is installed (optional)"""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            print("✓ Tesseract OCR is installed")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  Tesseract OCR is not installed (optional, for scanned PDFs)")
    print("   Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)")
    return False

def create_directories():
    """Create required directories"""
    from config import UPLOAD_DIR, OUTPUT_DIR, LOGS_DIR, ARCHIVE_DIR, MAPPINGS_DIR
    
    directories = {
        'Uploads': UPLOAD_DIR,
        'Output': OUTPUT_DIR,
        'Logs': LOGS_DIR,
        'Factsheet Archive': ARCHIVE_DIR,
        'Mappings': MAPPINGS_DIR
    }
    
    for name, path in directories.items():
        path.mkdir(exist_ok=True)
        # Create .gitkeep files
        gitkeep = path / '.gitkeep'
        if not gitkeep.exists():
            gitkeep.touch()
        print(f"✓ {name} directory: {path}")

def main():
    print("="*60)
    print("Automated Factsheet Extraction System - Setup Verification")
    print("="*60)
    print()
    
    all_good = True
    
    print("1. Checking Python version...")
    if not check_python_version():
        all_good = False
    print()
    
    print("2. Checking Python dependencies...")
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        print(f"\n   Install missing packages with: pip install {' '.join(missing)}")
        all_good = False
    print()
    
    print("3. Checking Java...")
    java_ok = check_java()
    if not java_ok:
        all_good = False
    print()
    
    print("4. Checking Tesseract OCR (optional)...")
    check_tesseract()
    print()
    
    print("5. Creating directories...")
    try:
        create_directories()
    except Exception as e:
        print(f"❌ Error creating directories: {e}")
        all_good = False
    print()
    
    print("="*60)
    if all_good:
        print("✓ Setup verification complete! System is ready to use.")
        print("\nNext steps:")
        print("  1. Start the API server: python start_server.py")
        print("  2. Open frontend/index.html in your browser")
        print("  3. Or use the CLI: python cli_extract.py <pdf_file>")
    else:
        print("⚠️  Setup incomplete. Please fix the issues above.")
    print("="*60)

if __name__ == "__main__":
    main()


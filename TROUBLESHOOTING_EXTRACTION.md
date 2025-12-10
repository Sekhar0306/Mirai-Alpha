# Troubleshooting Extraction Failures

## Common Error: "Could not extract holdings from PDF"

This error occurs when the system cannot find portfolio holdings in the PDF. Here's how to fix it:

### 1. Check Your PDF Type

**Problem:** You might be using a summary/update factsheet instead of a complete factsheet.

**Solution:**
- Look for PDFs with names like "Monthly Factsheet" or "Portfolio Holdings"
- Avoid "Update", "Summary", "NFO Presentation" documents
- Complete factsheets usually have a "Portfolio Holdings" or "Top Holdings" table with individual securities

**How to identify a complete factsheet:**
- Should have a table with columns like: Security Name, ISIN, Sector, Market Value, % of AUM
- Usually 20-100+ individual holdings listed
- Not just sector allocations or top 5 holdings

### 2. Set Up OpenAI API Key (Recommended)

**Problem:** LLM extraction is the most reliable method but requires an API key.

**Solution:**
```bash
# Option 1: Environment variable
export OPENAI_API_KEY="sk-proj-your-key-here"

# Option 2: Create .env file
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=sk-proj-your-key-here
```

**Get API key:** https://platform.openai.com/api-keys

### 3. Install Missing Dependencies

**Java (for tabula extraction):**
```bash
# macOS
brew install openjdk

# Linux
sudo apt-get install default-jre

# Verify
java -version
```

**Poppler (for OCR extraction):**
```bash
# macOS
brew install poppler

# Linux
sudo apt-get install poppler-utils

# Verify
pdftoppm -h
```

### 4. Check PDF Format

**Problem:** PDF might be scanned (image-based) or have unusual formatting.

**Solutions:**
- Try opening the PDF and copying text - if you can't, it's likely scanned
- For scanned PDFs, OCR extraction is needed (requires Poppler)
- Some PDFs have tables that aren't properly structured

### 5. Verify PDF Content

**Quick test:**
1. Open the PDF in a PDF viewer
2. Search for "Portfolio Holdings" or "Top Holdings"
3. Check if there's a table with individual securities
4. If you only see sector allocations or summary data, it's not a complete factsheet

### 6. Try Different Extraction Methods

The system tries methods in this order:
1. **LLM** (best, but requires API key)
2. **pdfplumber** (works for most text-based PDFs)
3. **tabula** (good for complex tables, requires Java)
4. **OCR** (for scanned PDFs, requires Poppler)

If one fails, the system automatically tries the next.

### 7. Check Logs

View detailed error information:
```bash
tail -50 logs/extraction.log
```

This will show:
- Which extraction methods were tried
- Why each method failed
- Any specific errors

### Example: Good Factsheet vs Summary

**Good Factsheet (will work):**
```
Portfolio Holdings (as on 31-Oct-2025)
Security Name              ISIN              Sector        % of AUM
Reliance Industries Ltd.   INE002A01018      Energy        8.50
TCS Limited                INE467B01029      Technology    6.80
HDFC Bank Limited          INE040A01034      Financial     5.20
... (20-100+ more holdings)
```

**Summary/Update (won't work):**
```
Top 5 Holdings
1. Reliance Industries - 8.5%
2. TCS - 6.8%
... (only 5-10 holdings)

Sector Allocation
Financial Services - 25%
Technology - 20%
... (no individual securities)
```

### Still Having Issues?

1. **Check the PDF manually** - Open it and verify it has a full holdings table
2. **Try a different PDF** - Test with a known complete factsheet
3. **Review logs** - Check `logs/extraction.log` for detailed errors
4. **Set up API key** - LLM extraction handles most edge cases

### Quick Setup Checklist

- [ ] Using complete monthly factsheet (not summary)
- [ ] OpenAI API key set (for LLM extraction)
- [ ] Java installed (for tabula extraction)
- [ ] Poppler installed (for OCR extraction)
- [ ] PDF is text-based (not scanned image)


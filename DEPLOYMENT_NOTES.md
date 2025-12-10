# Vercel Deployment Notes

## Large File Issue

If you get "Serverless Function exceeded 250 MB" error:

### Problem
Large PDF files in `factsheet_archive/` are being included in deployment.

### Solution
1. **PDFs are excluded** via `.vercelignore` and `.gitignore`
2. **Don't commit PDFs** - they should be uploaded by users at runtime
3. **Only deploy code**, not data files

### Files Excluded from Deployment
- `factsheet_archive/*.pdf` - Sample PDFs (users upload their own)
- `uploads/*` - Temporary uploads
- `output/*` - Generated data
- `logs/*.log` - Log files

### What Gets Deployed
- Python code (api/, extractors/, processors/)
- Frontend (frontend/index.html)
- Configuration files
- Requirements and setup files
- **NOT** PDF files or data

### For Vercel
The `.vercelignore` file ensures large files are excluded from the build.

### Alternative: Use Vercel's File System
If you need to include sample PDFs:
1. Use Vercel's `/tmp` directory (ephemeral)
2. Store PDFs in external storage (S3, etc.)
3. Download PDFs at runtime from a CDN

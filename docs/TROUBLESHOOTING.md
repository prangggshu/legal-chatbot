# Troubleshooting Guide - Common Issues & Solutions

Comprehensive troubleshooting guide for the Legal AI Chatbot system.

## Quick Diagnostics

### Is the System Running?

```powershell
# Check backend on port 8000
curl http://localhost:8000/

# Expected: {"status":"Legal AI Backend Running"}
# If error: Backend not started
```

```bash
# Check frontend on port 5173
curl http://localhost:5173/

# Expected: HTML + React app
# If error: Frontend not started
```

### Full System Status Check

```bash
# 1. Backend health
curl http://localhost:8000/

# 2. FAISS index exists
ls -la d:\legal-chatbot\backend\vector_db\

# 3. Local users file exists  
ls -la d:\legal-chatbot\backend\local_users.json

# 4. Check for errors in terminal where backend runs
# Should see: "Application startup complete"
```

---

## Error Reference

### Authentication Errors

#### ❌ "Invalid username or password"

**Symptoms**: Login fails even with correct credentials

**Likely Causes**:
1. CAPS LOCK is on
2. Username/password changed automatically
3. local_users.json corrupted
4. Backend restarted (invalidates old tokens)

**Solutions** (try in order):
```powershell
# 1. Verify credentials
# Try default: admin / admin123

# 2. Check if file exists
Test-Path "d:\legal-chatbot\backend\local_users.json"

# 3. Reset users file
# Delete and re-initialize
Remove-Item "d:\legal-chatbot\backend\local_users.json"
# Restart backend - will auto-create with admin/admin123

# 4. Check backend logs for auth errors
# Look at terminal where backend runs for error messages
```

**Prevention**:
- Use password manager to store credentials
- Don't share credentials
- Change default admin password after first login

---

#### ❌ "Unable to connect to authentication service"

**Symptoms**: Login page shows error when attempting login

**Likely Causes**:
1. Backend not running
2. Wrong port configuration  
3. CORS issue (frontend can't reach backend)
4. Firewall blocking connection

**Solutions** (try in order):
```powershell
# 1. Check if backend is running
netstat -ano | findstr "8000"
# Should see: LISTENING

# 2. If not running, start backend
cd d:\legal-chatbot\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn rag_engine.main:app --app-dir backend --reload

# 3. Check frontend config
# Check frontend/src/services/api.ts
# Should have: const API_BASE = "http://localhost:8000"

# 4. Check CORS in backend
# main.py should have:
# app.add_middleware(CORSMiddleware, allow_origins=["*"])

# 5. Firewall exception
# Add Python to Windows Firewall exceptions
```

**Test Connection**:
```bash
# From browser console:
fetch('http://localhost:8000/').then(r => r.json()).then(console.log)
# Should work if connected
```

---

#### ❌ Token Expired Error

**Symptoms**: "Invalid or expired token" after some idle time

**Expected Behavior**: Tokens expire after 1 hour

**Solutions**:
1. **Login Again**: Click "Logout" then "Login"
2. **Clear Browser Storage**: Dev Tools → Application → Clear localStorage
3. **Restart Frontend**: Refresh page (F5)

**To Extend Token TTL**:
```python
# In backend/rag_engine/auth_local.py
# Find: TOKEN_TTL_SECONDS = 3600  # 1 hour
# Change to: TOKEN_TTL_SECONDS = 86400  # 24 hours
```

---

### Upload & Document Processing Errors

#### ❌ "Failed to upload document"

**Symptoms**: Upload button shows error, file not processed

**Likely Causes**:
1. Backend crashed during upload
2. File format not PDF
3. File size too large (> 50MB)
4. Disk space full
5. FAISS index corrupted

**Solutions** (try in order):
```powershell
# 1. Check file format
$file = "contract.pdf"
if ($file -match "\.pdf$") { Write-Host "✓ PDF format" } else { Write-Host "✗ Not PDF" }

# 2. Check file size
(Get-Item $file).length / 1MB  # Should be < 50
# If huge, the PDF might be corrupt

# 3. Check disk space
Get-Volume C: | Select-Object SizeRemaining  # Should be > 5GB free

# 4. Check uploads folder exists
New-Item -ItemType Directory -Force -Path "d:\legal-chatbot\backend\uploads"

# 5. Check FAISS index health
Get-Item d:\legal-chatbot\backend\vector_db\legal_qa.index
# If missing, rebuild:
# Delete /vector_db/ folder
# Re-upload a document
```

**Prevention**:
- Ensure file is actual PDF (not renamed image)
- Extract text from scanned PDFs first
- Keep only important documents (avoid 100MB files)

---

#### ❌ "Document uploaded but no chunks created"

**Symptoms**: Upload succeeds but returns `chunks_created: 0`

**Likely Causes**:
1. PDF is scanned image (no text)
2. Corrupted PDF file
3. Unsupported PDF encoding
4. Text extraction failed

**Solutions**:
```powershell
# 1. Test PDF extraction
# In PowerShell, from d:\legal-chatbot\backend
python << 'EOF'
import pdfplumber
with pdfplumber.open("uploads/your_file.pdf") as pdf:
    print(f"Pages: {len(pdf.pages)}")
    text = pdf.pages[0].extract_text()
    print(f"Text length: {len(text)}")
    print(f"First 200 chars: {text[:200]}")
EOF

# If text is empty: PDF is scanned image

# 2. Try OCR conversion
# Use free online converter: https://pdf.io/
# Convert scanned PDF to text PDF
# Then re-upload

# 3. Try different PDF
# Test with known-good PDF to verify system works
```

**Prevention**:
- Use text-based PDFs, not scanned images
- Verify PDF opens in Adobe Reader with selectable text
- Validate PDF before uploading

---

#### ❌ "Analyze returns no risk sections"

**Symptoms**: Risk analysis runs but finds 0 risks

**Likely Causes**:
1. Document has no risk keywords
2. Document too small after chunking
3. Risk detection keyword list incomplete

**Solutions**:
```powershell
# 1. Check if document has risk keywords
# Search for: "terminate", "penalty", "damages", "liable"
# Use PDF viewer to verify content is there

# 2. Try asking questions instead
# POST /ask with: "What are the penalties?"
# This uses semantic search (better than keyword matching)

# 3. Add custom risk keyword
# Edit: backend/rag_engine/risk_engine.py
# Find: HIGH_RISK_KEYWORDS = ["terminate without notice", ...]
# Add your keyword to the list

# 4. Check chunk contents
python << 'EOF'
import json
with open("backend/vector_db/legal_qa_chunks.json") as f:
    chunks = json.load(f)
    print(f"Total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks[:5]):
        print(f"\nChunk {i}:\n{chunk[:200]}")
EOF
```

---

### Question & Answer Errors

#### ❌ "No document uploaded"

**Symptoms**: Click "Ask" but get error "No document uploaded"

**Expected**: Must upload PDF before asking questions

**Solutions**:
```
1. Click "Upload Document" button
2. Select PDF file from computer
3. Wait for "Document uploaded" message
4. Then try asking question again
```

---

#### ❌ "Answers are irrelevant or wrong"

**Symptoms**: Asking "What is penalty?" but getting unrelated answer

**Likely Causes**:
1. Confidence score too low (< 0.60)
2. Answer is "gemini_fallback" (not from document)
3. Document doesn't contain answer
4. Chunk context too small
5. Query phrased differently than document text

**Check Confidence Score**:
```json
{
  "answer": "...",
  "confidence_score": 0.45,  ← Low! 
  "answer_source": "retrieval"
}
// Confidence < 0.60 means uncertain
```

**Solutions**:
```
1. Rephrase question using document keywords
   ✗ "What about money?" 
   ✓ "What is the salary amount?"

2. Ask more specific questions
   ✗ "What is this?"
   ✓ "What is the employment duration?"

3. Try related questions
   "What is liability?" 
   → If no answer, try:
   "What about damages?"
   "What about responsibilities?"

4. Re-upload document
   Maybe chunking had issues
```

**If Answer Source is "gemini_fallback"**:
- Answer is from general knowledge, not your document
- Your document may not contain information
- Check if document actually has relevant content

---

#### ❌ "Questions timeout or no response"

**Symptoms**: Hit "Send" and spinner keeps spinning

**Likely Causes**:
1. Backend crashed
2. Ollama or Gemini unreachable
3. Internet connection lost
4. Very large document causing slow FAISS search

**Solutions** (try in order):
```powershell
# 1. Wait 10 seconds (Gemini may just be slow)

# 2. Check backend is running
curl http://localhost:8000/
# If error: Start backend again

# 3. Check Ollama status
curl http://localhost:11434/api/tags
# If error: Start Ollama or ignore (will use Gemini)

# 4. Check internet connection
ping google.com
# If error: Internet down, Gemini unavailable

# 5. Restart backend
# Stop backend (Ctrl+C in terminal)
# Start again: python -m uvicorn rag_engine.main:app --app-dir backend --reload

# 6. Check backend logs for errors
# Look at terminal output for exceptions
```

**Timeout Mechanism**:
- Ollama has 4 second timeout
- If no response in 4s → Falls back to Gemini
- If Gemini times out too → Returns error

---

### Risk Analysis Errors

#### ❌ "Risk analysis fails with error"

**Symptoms**: Click "Analyze" and get error message

**Likely Causes**:
1. FAISS index missing or corrupted
2. No document uploaded yet
3. Backend out of memory

**Solutions**:
```powershell
# 1. Verify document uploaded
# Should see chunks_created > 0

# 2. Check FAISS index
ls d:\legal-chatbot\backend\vector_db\

# Expected files:
# - legal_qa.index
# - legal_qa_chunks.json
# - legal_qa_metadata.json
# - legal_qa_sources.json

# If missing, re-upload document

# 3. If corrupted, rebuild:
# Delete entire vector_db folder
Remove-Item d:\legal-chatbot\backend\vector_db\ -Recurse
# Create new folder
New-Item -ItemType Directory d:\legal-chatbot\backend\vector_db\
# Re-upload a document
```

---

### Summarization Errors

#### ❌ "Failed to generate summary"

**Symptoms**: Click "Get Summary" and error appears

**Likely Causes**:
1. GEMINI_API_KEY not configured
2. Gemini API quota exceeded
3. Network timeout
4. No document uploaded

**Solutions**:
```powershell
# 1. Check GEMINI_API_KEY
# Open d:\legal-chatbot\backend\.env
# Should contain: GEMINI_API_KEY=sk-...

# If missing:
# 1. Get key from https://makersuite.google.com/
# 2. Add to .env file
# 3. Restart backend for env to reload

# 2. Check API key valid
python << 'EOF'
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv("GEMINI_API_KEY")
if key and len(key) > 10:
    print(f"✓ API Key loaded (length: {len(key)})")
else:
    print("✗ API Key missing or invalid")
EOF

# 3. Check Gemini API quota
# Visit https://console.cloud.google.com/
# Check API usage and quota limits

# 4. Test Gemini connection
python << 'EOF'
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content("Test")
    print("✓ Gemini API working")
except Exception as e:
    print(f"✗ Gemini Error: {e}")
EOF
```

**Prevention**:
- Set up free Gemini API key early
- Monitor usage to avoid quota limits
- Test API connection after setup

---

## Backend Runtime Issues

### Backend Crashing / Not Starting

#### ❌ "Python module not found"

**Error**: `ModuleNotFoundError: No module named 'uvicorn'`

**Cause**: Virtual environment not activated or dependencies not installed

**Solution**:
```powershell
cd d:\legal-chatbot\backend

# Create venv
python -m venv .venv

# Activate venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r rag_engine/requirements.txt

# Start backend
python -m uvicorn rag_engine.main:app --app-dir backend --reload
```

**Windows Execution Policy Issue**:
```powershell
# If you get "execution policy" error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try activation again
.venv\Scripts\Activate.ps1
```

---

#### ❌ Backend Crashes on Startup

**Error**: `Exception on startup` or `RuntimeError`

**Likely Causes**:
1. Port 8000 already in use
2. Missing .env file with GEMINI_API_KEY
3. Corrupted FAISS index
4. Import error in code

**Solutions**:
```powershell
# 1. Check if port 8000 is in use
netstat -ano | findstr "8000"

# If in use, either:
# a) Kill existing process
Stop-Process -Id <PID> -Force

# b) Use different port
python -m uvicorn rag_engine.main:app --app-dir backend --port 8001

# 2. Create .env file
$env_content = @"
GEMINI_API_KEY=your-api-key-here
"@
$env_content | Out-File "d:\legal-chatbot\backend\.env" -Encoding utf8

# 3. Rebuild FAISS index
Remove-Item d:\legal-chatbot\backend\vector_db\ -Recurse -Force
New-Item -ItemType Directory d:\legal-chatbot\backend\vector_db\

# 4. Check logs for import errors
# Look at terminal output carefully
# May need to install extra dependencies:
pip install pdfplumber faiss-cpu sentence-transformers google-generativeai
```

---

#### ❌ "Address already in use" Error

**Error**: `OSError: [WinError 48] Address already in use`

**Cause**: Port 8000 already occupied by another process

**Solutions**:
```powershell
# Option 1: Kill the existing process
netstat -ano | findstr "8000"
# Note the PID (process ID)
Stop-Process -Id <PID> -Force

# Then restart backend:
python -m uvicorn rag_engine.main:app --app-dir backend

# Option 2: Use different port
python -m uvicorn rag_engine.main:app --app-dir backend --port 8001

# Then in frontend/src/services/api.ts:
# Change: const API_BASE = "http://localhost:8001"
```

---

#### ❌ Backend Very Slow / Spikes to 100% CPU

**Symptoms**: Backend responsive but very slow, CPU maxed out

**Likely Causes**:
1. FAISS index being rebuilt
2. Ollama model loading for first time
3. Large document processing
4. Memory swapping

**Solutions**:
```powershell
# 1. Check what's using CPU
tasklist /v | Select-String python

# 2. Give it time if:
# - First time running (models downloading)
# - Large document (> 10MB) being processed
# - FAISS index being built

# 3. Monitor memory usage
Get-Process python | Select-Object name, WorkingSet

# If > 4GB: System is swapping, close other apps

# 4. Optimize document processing
# Split large PDF into smaller parts
# Upload one section at a time

# 5. Increase RAM available
# Close other applications
# Consider adding more RAM if persistent issue
```

---

## Frontend Issues

### Layout / UI Problems

#### ❌ Chat interface looks broken / misaligned

**Symptoms**: Text overlapping, buttons in wrong place, colors weird

**Likely Causes**:
1. Browser cache with old CSS
2. Tailwind CSS not loading
3. Browser zoom issue
4. Mobile viewport

**Solutions**:
```
1. Clear browser cache
   - Press Ctrl+Shift+Delete
   - Clear all cached images/files
   - Refresh page (F5)

2. Hard refresh (ignore cache)
   - Press Ctrl+F5 (Chrome/Firefox)
   - Cmd+Shift+R (Mac)

3. Check browser zoom
   - Press Ctrl+0 to reset zoom to 100%
   - Should be: "100%"

4. Try different browser
   - Test on Chrome, Firefox, Edge
   - Identify if browser-specific

5. Rebuild frontend
   cd d:\legal-chatbot\frontend
   npm install
   npm run dev
```

---

#### ❌ Buttons Not Responding

**Symptoms**: Click button but nothing happens

**Likely Causes**:
1. Backend not running
2. Event handlers broken
3. State management issue
4. Browser dev tools blocking

**Solutions**:
```
1. Check backend
   - Verify backend is running
   - Try: curl http://localhost:8000/

2. Check browser console for errors
   - Press F12 to open dev tools
   - Click "Console" tab
   - Look for red error messages
   - Note the error

3. Try hard refresh
   - Ctrl+F5

4. Restart frontend
   # In terminal where frontend runs:
   # Ctrl+C to stop
   # npm run dev to restart

5. Check for JavaScript errors
   # Look at terminal where frontend runs
   # Should see: "No issues found"
   # If errors, fix them or restart
```

---

#### ❌ Mobile View Broken

**Symptoms**: Using phone/tablet but layout is wrong

**Expected**: Should be responsive (works on mobile)

**Solutions**:
```
1. Check viewport meta tag
   - Open frontend/index.html
   - Should have: <meta name="viewport" ...>

2. Test in mobile emulation
   - Press F12 in Chrome
   - Click device toggle icon
   - Select iPhone 12 / Pixel 5
   - Check if layout works

3. Layout may be responsive but not perfect
   - Using mobile is not primary use case
   - Desktop recommended for complicated legal review

4. For better mobile experience
   - Could be future enhancement
   - File as feature request
```

---

### API Connection Issues

#### ❌ CORS Error in Browser Console

**Error**: `Access to XMLHttpRequest blocked by CORS policy`

**Cause**: Browser security blocking frontend→backend communication

**Solutions**:
```
1. Verify backend CORS is enabled
   # In main.py, should have:
   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  ← This should be ["*"] for dev
       ...
   )

2. Restart backend to apply changes
   # Kill old process, start new

3. Clear browser cache (old configuration cached)
   # Press Ctrl+Shift+Delete

4. Check API URL matches
   # frontend/src/services/api.ts
   # Should have: const API_BASE = "http://localhost:8000"
   # Match the port where backend runs
```

**Production Note**:
```
For production, restrict CORS:
allow_origins=["https://yourdomain.com"]
```

---

## Data Issues

### Lost Progress / Data

#### ❌ Messages Disappeared After Refresh

**Symptoms**: Had chat history, refreshed page, messages gone

**Expected Behavior**: LocalStorage should persist, but can be cleared

**Solutions**:
```
1. Permanent loss if:
   - Cleared browser data manually
   - Browser private/incognito mode (auto-cleared on close)
   - localStorage quota exceeded

2. Prevent future losses:
   - Use regular mode (not private/incognito)
   - Don't manually clear browser data
   - Export conversation before clearing

3. Current system stores:
   - Chat messages in localStorage
   - Session list in localStorage
   - Documents NOT persisted (re-upload to test)

4. Future improvement:
   - Server-side conversation storage
   - Database backup
   - Export/import conversations
```

---

#### ❌ File Not Saving to Uploads Folder

**Symptoms**: Document claims uploaded, but file not in `backend/uploads/`

**Likely Causes**:
1. Upload succeeded but file saved elsewhere
2. Permissions issue
3. Disk quota
4. File deleted by cleanup process

**Solutions**:
```powershell
# 1. Check uploads folder exists
Test-Path d:\legal-chatbot\backend\uploads\

# If not, create it:
New-Item -ItemType Directory -Path d:\legal-chatbot\backend\uploads\

# 2. Check file permissions
# uploads folder should be readable/writable
$acl = Get-Acl d:\legal-chatbot\backend\uploads\
$acl | fl

# If permission issue:
# Right-click folder → Properties → Security → Full Control for user

# 3. Monitor folder for uploads
Get-ChildItem d:\legal-chatbot\backend\uploads\ | Watch-Object

# 4. Check backend code accessing correct path
# In rag_engine/main.py:
# Should have: UPLOAD_FOLDER = "uploads"
# Files saved there via pdfplumber
```

---

## Performance Problems

### System Slow Under Load

#### ❌ High Latency (> 10 seconds per query)

**Symptoms**: Asking questions takes > 10 seconds to respond

**Likely Causes**:
1. FAISS doing full scan (index not optimized)
2. Ollama model very slow to load
3. Network latency to Gemini
4. System out of memory (swapping)
5. Antivirus scanning

**Solutions** (in Speedup Order):
```powershell
# 1. Close unnecessary applications
# Frees RAM and CPU

# 2. Check system resources
Get-Process | Sort-Object WorkingSet -Descending | Select-Object name, WorkingSet -First 5

# 3. If Ollama mentioned:
# Ollama first run is slow (downloads model)
# Subsequent runs faster
# Can disable Ollama to test if bottleneck:
# In rag_engine/llm_router.py, set timeout to 0

# 4. Restart backend to clear memory leaks
Stop-Process -Name python
# Then restart backend

# 5. Restart Ollama if running
# It may have memory leak if running for hours
# Kill it and restart

# 6. Disable antivirus scanning during testing
# Antivirus can significantly slow FAISS operations
```

**Permanent Speedup**:
1. Add SSD (faster file I/O)
2. Add RAM (avoid swapping)
3. Use smaller embedding model
4. Implement caching

---

## Getting Help

### How to Debug & Report Issues

**When Reporting a Bug, Include**:
1. Exact error message
2. Steps to reproduce
3. Screenshot or video
4. System info (Windows/Mac/Linux, RAM, GPU)
5. Backend logs output
6. Browser console errors (F12)

**Collect Diagnostic Info**:
```powershell
# Run this and save output:

Write-Host "=== System Info ==="
$psuver = Get-WmiObject Win32_OperatingSystem
$psuver.Caption, $psuver.Version

Write-Host "`n=== Python =="
python --version

Write-Host "`n=== Node =="
node --version
npm --version

Write-Host "`n=== Backend Process ==="  
Get-Process python | Select-Object name, WorkingSet

Write-Host "`n=== Ports ==="
netstat -ano | findstr "8000"
netstat -ano | findstr "5173"

Write-Host "`n=== File Exists ==="
Test-Path "d:\legal-chatbot\backend\local_users.json"
Test-Path "d:\legal-chatbot\backend\vector_db\"

Write-Host "`n=== API Response ==="
try { (curl http://localhost:8000/).Content } catch { "Backend not responding" }
```

---

### Resources & Support

**Documentation**:
- [Setup Guide](SETUP_GUIDE.md) - Installation help
- [API Reference](API_REFERENCE.md) - Endpoint details  
- [Architecture](ARCHITECTURE.md) - System design
- [Usage Guide](USAGE_GUIDE.md) - How to use features

**Common Search Terms**:
- "Error message" + quick troubleshooting
- "Port already in use" + solution
- "Backend not starting" + checklist

**Getting Support**:
1. Check this guide first
2. Review relevant documentation
3. Check browser console for errors (F12)
4. Check backend terminal for error messages
5. Collect diagnostic info above
6. Contact support with all info

---

## Checklist for Fresh Start

**Complete Reset Procedure**:
```powershell
# If everything is broken, start fresh:

# 1. Kill processes
Stop-Process -Name python -Force
Stop-Process -Name node -Force

# 2. Clear frontend
cd d:\legal-chatbot\frontend
Remove-Item node_modules -Recurse -Force
Remove-Item package-lock.json
npm install
npm run dev

# 3. Clear backend  
cd d:\legal-chatbot\backend
Remove-Item .venv -Recurse -Force
Remove-Item vector_db -Recurse -Force
Remove-Item uploads -Recurse -Force
Remove-Item local_users.json -Force

# 4. Recreate venv
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r rag_engine/requirements.txt

# 5. Create .env
Add-Content .env "GEMINI_API_KEY=your-key-here"

# 6. Start backend
python -m uvicorn rag_engine.main:app --app-dir backend --reload

# 7. Frontend already starting in step 2
# Open http://localhost:5173 in browser

# 8. Test with admin/admin123
```

---

**Last Updated**: February 24, 2026  
**Version**: 1.0  
**Maintainer**: Engineering Team  
**Feedback**: [Create Issue/Contact Support]

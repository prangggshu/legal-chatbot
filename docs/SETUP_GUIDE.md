# Setup Guide - Installation & Configuration

Complete step-by-step guide to set up the Legal AI Chatbot locally.

## Prerequisites

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **Disk Space**: 5GB minimum (FAISS index + models)
- **RAM**: 8GB minimum (16GB recommended)
- **GPU**: Optional (CUDA for faster inference)

### Required Software
- **Python 3.11+** - [Download](https://www.python.org)
- **Node.js 18+** - [Download](https://nodejs.org)
- **Git** - [Download](https://git-scm.com)
- **Ollama** - [Download](https://ollama.ai) (for local LLM)

### API Keys
- **Google Gemini API Key** - [Get here](https://makersuite.google.com)

---

## 🔧 Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/legal-chatbot.git
cd legal-chatbot
```

### 2. Backend Setup

#### 2.1 Create Virtual Environment

```bash
cd backend

# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### 2.2 Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies Summary**:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- pdfplumber (PDF processing)
- sentence-transformers (embeddings)
- faiss-cpu (vector search)
- google-genai (Gemini API)
- python-dotenv (environment variables)
- langchain-ollama (Ollama integration)

#### 2.3 Create .env File

```bash
# In backend/ directory
cat > .env << EOF
GEMINI_API_KEY=your-gemini-api-key-here
LOCAL_AUTH_SECRET=your-secret-key-here
LOCAL_AUTH_DEFAULT_USERNAME=admin
LOCAL_AUTH_DEFAULT_PASSWORD=admin123
LOCAL_AUTH_TTL_SECONDS=3600
EOF
```

**⚠️ Important**: Replace `your-gemini-api-key-here` with your actual API key from Google.

### 3. Frontend Setup

#### 3.1 Install Node Dependencies

```bash
cd frontend
npm install
```

#### 3.2 Update API Configuration (if needed)

Edit `frontend/vite.config.ts`:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // Adjust if backend on different port
      changeOrigin: true
    }
  }
}
```

---

## 🚀 Running the Application

### Option 1: Development Mode (Recommended for development)

#### Terminal 1: Start Backend
```bash
cd backend
.\.venv\Scripts\activate      # (Windows)
# source .venv/bin/activate  # (macOS/Linux)
python -m uvicorn rag_engine.main:app --app-dir backend --reload --port 8000
```

**Expected Output**:
```
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

#### Terminal 2: Start Frontend
```bash
cd frontend
npm run dev
```

**Expected Output**:
```
VITE v5.4.1  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  press h to show help
```

#### Terminal 3: Start Ollama (Optional)
```bash
ollama run llama3
```

Both services should now be running:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **OpenAPI Docs**: http://localhost:8000/docs

---

### Option 2: Production Mode

#### Backend
```bash
cd backend
python -m uvicorn rag_engine.main:app --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm run build
npm run preview
```

---

## ✅ Verification

### 1. Backend Health Check

```bash
curl http://127.0.0.1:8000/
```

Expected response:
```json
{"status": "Legal AI Backend Running"}
```

### 2. Frontend Access

Open browser: http://localhost:5173

You should see the login page.

### 3. Authentication Test

Register a new user:
- Email: `testuser`
- Password: `testpass123`

Or use default credentials:
- Email: `admin`
- Password: `admin123`

### 4. Vector DB Check

```bash
cd backend
# Check if FAISS index exists
ls vector_db/
```

You should see:
- `legal_qa.index`
- `legal_qa_chunks.json`
- `legal_qa_sources.json`
- `legal_qa_metadata.json`

### 5. API Documentation

Visit: http://localhost:8000/docs

You should see interactive API docs (Swagger UI) listing all 8 endpoints.

---

## 🛠️ Configuration Details

### Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | (required) | Google Gemini API key |
| `LOCAL_AUTH_SECRET` | change-this-... | Token signing secret |
| `LOCAL_AUTH_DEFAULT_USERNAME` | admin | Initial admin username |
| `LOCAL_AUTH_DEFAULT_PASSWORD` | admin123 | Initial admin password |
| `LOCAL_AUTH_TTL_SECONDS` | 3600 | Token lifetime (1 hour) |
| `RERANKER_MIN_SCORE` | 0.5 | Fine-tuning threshold |
| `OLLAMA_HOST` | http://localhost:11434 | Ollama endpoint |

### Ollama Setup (Optional but Recommended)

```bash
# Download and install Ollama
# Then in a new terminal:
ollama pull llama3

# Verify it runs
ollama run llama3
# Type "test" and press Enter
# You should get a response
```

---

## 📁 Directory Structure After Setup

```
legal-chatbot/
├── backend/
│   ├── .venv/                    # Virtual environment
│   ├── .env                      # Environment variables
│   ├── rag_engine/               # Python modules
│   ├── uploads/                  # User PDFs
│   ├── vector_db/                # FAISS index
│   ├── local_users.json          # User credentials
│   └── requirements.txt
│
├── frontend/
│   ├── node_modules/             # Dependencies
│   ├── src/                      # React source
│   ├── dist/                     # Built files (after npm run build)
│   └── package.json
│
└── docs/                         # Documentation
```

---

## 🔑 Getting a Gemini API Key

1. Visit https://makersuite.google.com
2. Click "Create API Key"
3. Select or create a project
4. Copy the API key
5. Add to `.env`: `GEMINI_API_KEY=your-key-here`

---

## 🐛 Troubleshooting Setup

### Issue: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**: Ensure virtual environment is activated and requirements installed
```bash
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue: `GEMINI_API_KEY not found`
**Solution**: Create `.env` file in backend/ with your API key
```bash
echo "GEMINI_API_KEY=your-key-here" > .env
```

### Issue: Port 8000 already in use
**Solution**: Use different port
```bash
python -m uvicorn rag_engine.main:app --port 8001
# Then update frontend vite.config.ts proxy target
```

### Issue: `[Errno 98] Address already in use`
**Solution**: Kill existing process
```bash
# Find process on port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

### Issue: Frontend can't reach backend (CORS error)
**Solution**: Ensure proxy is configured in `vite.config.ts`:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '')
    }
  }
}
```

### Issue: FAISS index not loading
**Solution**: Rebuild index
```bash
cd backend
# Delete old index
rm -rf vector_db/

# Restart backend - it will rebuild automatically
python -m uvicorn rag_engine.main:app --reload
```

### Issue: Ollama connection refused
**Solution**: Start Ollama in separate terminal
```bash
ollama run llama3
# In another terminal, verify
curl http://localhost:11434/api/tags
```

---

## 📊 Verify Installation Checklist

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated
- [ ] Backend dependencies installed (`pip list` shows packages)
- [ ] Node.js 18+ installed
- [ ] Frontend dependencies installed (`npm list` shows packages)
- [ ] `.env` file created with GEMINI_API_KEY
- [ ] Backend starts without errors
- [ ] Frontend builds without errors
- [ ] Can access http://localhost:5173
- [ ] Can access http://localhost:8000/docs
- [ ] Can login with admin/admin123
- [ ] Can upload a test PDF
- [ ] Can ask a question
- [ ] FAISS index files exist in `backend/vector_db/`

---

## 🎓 Next Steps

1. **Try Basic Features**: See [USAGE_GUIDE.md](USAGE_GUIDE.md)
2. **Understand Architecture**: See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
3. **Deploy**: See [ARCHITECTURE.md](ARCHITECTURE.md#-deployment)
4. **Develop**: See [BACKEND_GUIDE.md](BACKEND_GUIDE.md) or [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)

---

## 📞 Support

- **Backend issues**: Check terminal output, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Frontend issues**: Check browser console (F12)
- **API issues**: Check http://localhost:8000/docs for endpoint details
- **General help**: See relevant documentation file

---

**Version:** 1.0  
**Last Updated:** February 24, 2026

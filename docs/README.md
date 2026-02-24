# Legal AI Chatbot - Documentation

Welcome to the Legal AI Chatbot documentation hub. This folder contains comprehensive guides for understanding, developing, and deploying the Legal AI Chatbot system.

## 📚 Documentation Structure

### Getting Started
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Installation, configuration, and first-time setup
- **[USAGE_GUIDE.md](USAGE_GUIDE.md)** - How to use the application as an end user

### Technical Documentation
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - System architecture, tech stack, and data flow
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical design decisions and pattern explanations
- **[BACKEND_GUIDE.md](BACKEND_GUIDE.md)** - Backend components, functions, and implementation details
- **[FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)** - Frontend structure, components, and styling

### API Documentation
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API endpoint documentation with examples

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues, error handling, and solutions

---

## 🚀 Quick Start

### For Users
1. Start with [USAGE_GUIDE.md](USAGE_GUIDE.md)
2. Learn how to upload documents and ask questions
3. Understand auth, risk analysis, and summarization features

### For Developers
1. Read [SETUP_GUIDE.md](SETUP_GUIDE.md) for environment setup
2. Study [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for system design
3. Deep dive into [BACKEND_GUIDE.md](BACKEND_GUIDE.md) and [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)
4. Reference [API_REFERENCE.md](API_REFERENCE.md) for endpoint details
5. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

### For DevOps/Deployment
1. Follow [SETUP_GUIDE.md](SETUP_GUIDE.md) for installation
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for infrastructure decisions
3. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for production issues

---

## 📖 Documentation at a Glance

| Document | Purpose | Audience |
|----------|---------|----------|
| PROJECT_OVERVIEW | System architecture and data flow | Everyone |
| SETUP_GUIDE | Installation and configuration | Developers, DevOps |
| USAGE_GUIDE | How to use the application | End users, Support teams |
| BACKEND_GUIDE | Backend implementation details | Backend developers |
| FRONTEND_GUIDE | Frontend components and structure | Frontend developers |
| API_REFERENCE | Endpoint documentation | Integration teams, Frontend devs |
| ARCHITECTURE | Design decisions and patterns | Tech leads, Architects |
| TROUBLESHOOTING | Issues and solutions | Support teams, Developers |

---

## 🎯 Key Features

### Document Management
- Upload and process legal documents (PDFs)
- Multi-level semantic chunking
- Vector-based similarity search
- Risk analysis and document summarization

### Q&A System
- Query answering using RAG (Retrieval-Augmented Generation)
- Semantic search with spell correction
- Legal reference extraction (Section X of Act Y)
- Intelligent LLM routing (Local Ollama → Gemini fallback)

### Security
- Local user authentication (no external database)
- PBKDF2 password hashing
- HMAC-signed tokens
- Token expiration and verification

### Analysis Tools
- Risk detection in documents
- Financial/legal penalty identification
- Clause-level risk scoring
- Document summarization with Gemini

---

## 🏗️ System Architecture

```
┌─ Frontend (React + TypeScript)
│  ├─ Authentication UI
│  ├─ Chat Interface
│  ├─ Document Upload
│  └─ Analysis Dashboard
│
├─ Backend (FastAPI + Python)
│  ├─ RAG Engine (FAISS + Embeddings)
│  ├─ Auth System (Local + JWT-like tokens)
│  ├─ LLM Routing (Ollama → Gemini)
│  ├─ Document Processing
│  └─ Risk Detection
│
└─ Storage
   ├─ FAISS Index (Vector DB)
   ├─ local_users.json (Auth)
   ├─ Uploaded PDFs
   └─ Metadata (chunks, sources)
```

---

## 📝 Document Purposes

### PROJECT_OVERVIEW.md
Comprehensive system overview including:
- Tech stack explanation
- Data flow diagrams
- Module responsibilities
- Integration points
- Performance characteristics

### SETUP_GUIDE.md
Step-by-step instructions for:
- Environment setup
- Dependency installation
- Configuration
- Database initialization
- Service startup
- Verification steps

### USAGE_GUIDE.md
User-facing documentation:
- Login/registration
- Uploading documents
- Asking questions
- Understanding answers
- Risk analysis
- Document summarization

### BACKEND_GUIDE.md
Developer reference:
- Module structure
- Function signatures and behavior
- Algorithm explanations
- Storage format
- Token generation/verification
- Scoring calculations

### FRONTEND_GUIDE.md
Component documentation:
- React component hierarchy
- State management
- API integration
- Styling approach
- Type definitions
- Component interactions

### API_REFERENCE.md
API specification:
- All endpoints (8 total)
- Request/response formats
- Status codes
- Error handling
- Authentication required
- Code examples

### ARCHITECTURE.md
Design decisions:
- Why FAISS over other solutions
- Chunking strategy explanation
- LLM routing logic
- Auth system design
- Scoring algorithm rationale
- Future scalability path

### TROUBLESHOOTING.md
Problem solving:
- Common errors
- Debugging tips
- Environment issues
- Performance problems
- API failures
- Recovery procedures

---

## 🔧 Configuration

### Environment Variables

**Required:**
```bash
GEMINI_API_KEY=<your-gemini-api-key>
```

**Optional:**
```bash
LOCAL_AUTH_SECRET=<your-secret>
LOCAL_AUTH_DEFAULT_USERNAME=admin
LOCAL_AUTH_DEFAULT_PASSWORD=admin123
LOCAL_AUTH_TTL_SECONDS=3600
```

### File Locations

```
backend/
├── local_users.json        # User credentials
└── vector_db/              # FAISS index
   ├── legal_qa.index      # Vector data
   ├── legal_qa_chunks.json # Text chunks
   └── legal_qa_metadata.json
```

---

## 📊 Technology Stack

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Vite (bundler)
- Axios/fetch (HTTP client)

### Backend
- FastAPI
- Python 3.11
- FAISS (vector search)
- Sentence Transformers (embeddings)
- Ollama (local LLM)
- Google Gemini API (cloud LLM)
- pdfplumber (PDF processing)

### Storage
- FAISS (vector DB)
- JSON files (metadata & auth)
- Local filesystem (PDFs, index)

### Deployment
- Docker (optional)
- Uvicorn (ASGI server)
- Vite dev server (frontend)

---

## 🤝 Contributing

When extending documentation:
1. Follow existing markdown format
2. Use relative links between documents
3. Keep code examples up-to-date
4. Include diagrams for complex flows
5. Add new documents to this README table

---

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review relevant guide based on component
3. Check error logs in terminal output
4. Consult API documentation for endpoint issues

---

## 📅 Documentation Status

- **Last Updated:** February 24, 2026
- **Version:** 1.0
- **Status:** Complete
- **Coverage:** 100% of core features

---

## 📋 Document Cross-References

**Setup Issues?** → See [SETUP_GUIDE.md](SETUP_GUIDE.md)  
**Can't upload a document?** → See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)  
**Want to understand the API?** → See [API_REFERENCE.md](API_REFERENCE.md)  
**Need to modify backend?** → See [BACKEND_GUIDE.md](BACKEND_GUIDE.md)  
**Need to modify frontend?** → See [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md)  
**Architecture questions?** → See [ARCHITECTURE.md](ARCHITECTURE.md)

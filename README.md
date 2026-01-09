"# Legal AI Chatbot

An intelligent legal document chatbot powered by RAG (Retrieval-Augmented Generation), Google Gemini AI, and FAISS vector search. This system helps users query legal documents, extract relevant clauses, and assess risk levels automatically.

## 🌟 Features

- **Document Upload & Processing**: Upload legal documents in various formats (PDF, DOCX, TXT, Excel)
- **Intelligent Question Answering**: Ask questions in natural language and get accurate answers from your documents
- **Clause Extraction**: Automatically identifies and extracts relevant legal clauses
- **Risk Assessment**: Analyzes clauses for potential legal risks (High, Medium, Low)
- **Confidence Scoring**: Provides confidence scores for retrieved information
- **Vector Search**: Uses FAISS for efficient semantic search across documents
- **RESTful API**: FastAPI-based backend with interactive documentation

## 🏗️ Architecture

The system consists of several key components:

- **RAG Core** (`rag_core.py`): Vector database management using FAISS and sentence transformers
- **Document Processor** (`document_processor.py`): Extracts and chunks text from various document formats
- **LLM Engine** (`llm_engine.py` & `gemini_engine.py`): Google Gemini AI integration for answer generation
- **Risk Engine** (`risk_engine.py`): Analyzes legal clauses for risk assessment
- **API Layer** (`main.py`): FastAPI endpoints for document upload and querying

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone or download the project:**
   ```bash
   cd legal-chatbot
   ```

2. **Create and activate a virtual environment:**
   
   Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   
   macOS/Linux:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   
   Create a `.env` file in the `rag_engine` folder:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

5. **Create required directories:**
   ```bash
   cd rag_engine
   mkdir data processed uploads vector_db
   ```

6. **Run the application:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API:**
   - API Status: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

## 📚 API Endpoints

### 1. Health Check
```http
GET /
```
Returns the status of the API server.

**Response:**
```json
{
  "status": "Legal AI Backend Running"
}
```

### 2. Upload Document
```http
POST /upload
```
Upload a legal document for processing.

**Request:**
- Form Data: `file` (PDF, DOCX, TXT, XLS, XLSX)

**Response:**
```json
{
  "status": "Document uploaded and processed",
  "chunks_created": 45
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/upload" \
     -F "file=@contract.pdf"
```

### 3. Ask Question
```http
POST /ask
```
Query the uploaded documents with a natural language question.

**Request Body:**
```json
{
  "query": "What are the payment terms?"
}
```

**Response:**
```json
{
  "question": "What are the payment terms?",
  "answer": "Payment shall be made within 30 days of invoice date...",
  "clause_reference": "Clause 5.2",
  "confidence_score": 0.87,
  "risk_level": "Low",
  "risk_reason": "Standard payment terms"
}
```

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the termination conditions?"}'
```

## 🔧 Technology Stack

- **FastAPI**: Modern web framework for building APIs
- **Google Gemini 2.5 Flash**: Advanced language model for answer generation
- **Sentence Transformers**: Embedding models for semantic search (`all-MiniLM-L6-v2`)
- **FAISS**: Facebook AI Similarity Search for vector database
- **Python-dotenv**: Environment variable management
- **Various Document Parsers**: Support for PDF, DOCX, Excel, and more

## 📂 Project Structure

```
legal-chatbot/
├── rag_engine/
│   ├── main.py                 # FastAPI application
│   ├── rag_core.py            # Vector search and retrieval
│   ├── gemini_engine.py       # Gemini AI integration
│   ├── llm_engine.py          # LLM routing logic
│   ├── llm_router.py          # Answer generation router
│   ├── risk_engine.py         # Risk assessment logic
│   ├── document_processor.py  # Document parsing and chunking
│   ├── data/                  # Source documents
│   ├── processed/             # Processed document cache
│   ├── uploads/               # Uploaded files
│   └── vector_db/             # FAISS indices
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── INSTALLATION.md            # Detailed installation guide
```

## 🎯 Use Cases

- **Contract Analysis**: Quickly find specific clauses in lengthy contracts
- **Legal Research**: Search through multiple legal documents simultaneously
- **Risk Assessment**: Identify potentially problematic clauses automatically
- **Due Diligence**: Speed up document review processes
- **Compliance Checking**: Verify specific terms and conditions

## 🔒 Risk Assessment

The system automatically analyzes clauses for risk levels:

- **High Risk**: Termination without notice, unfavorable terms
- **Medium Risk**: Penalty clauses, liquidated damages
- **Low Risk**: Standard legal provisions, jurisdiction clauses

## 🧪 Testing

Test the RAG functionality:
```bash
cd rag_engine
python rag_test.py
```

## 🛠️ Configuration

### Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)

### Embedding Model

By default, the system uses `all-MiniLM-L6-v2` for embeddings. You can change this in `rag_core.py`:
```python
embedder = SentenceTransformer("all-MiniLM-L6-v2")
```

### Server Configuration

Modify the server settings when running:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Performance

- **Vector Search**: Sub-second retrieval using FAISS
- **Document Processing**: Handles documents up to several MB
- **Concurrent Requests**: FastAPI's async support for multiple simultaneous queries
- **Embedding Model Size**: ~80MB (first-time download)

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated and dependencies installed
2. **API Key Error**: Verify `.env` file is in the `rag_engine` folder with correct key
3. **Port Conflicts**: Change port with `--port 8001` flag
4. **Out of Memory**: Reduce batch size or use a smaller embedding model

For more troubleshooting tips, see [INSTALLATION.md](INSTALLATION.md).

## 🚧 Limitations

- Currently supports single-user operation (no authentication)
- Vector database is in-memory (resets on restart)
- Risk assessment uses rule-based logic (not ML-based)
- Gemini API requires internet connection

## 🔮 Future Enhancements

- [ ] Persistent vector database
- [ ] User authentication and session management
- [ ] Support for more document formats
- [ ] Advanced risk assessment using ML
- [ ] Multi-document comparison
- [ ] Export answers to PDF/Word
- [ ] Web-based frontend interface

## 📝 License

[Specify your license here]

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues, questions, or suggestions, please open an issue in the project repository.

## 🙏 Acknowledgments

- Google Gemini AI for language model capabilities
- Facebook AI Research for FAISS
- Hugging Face for Sentence Transformers
- FastAPI team for the excellent framework

---

**Made with ❤️ for legal professionals and AI enthusiasts**" 

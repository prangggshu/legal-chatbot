# Fresh Installation Guide - Legal Chatbot

This guide will walk you through setting up the Legal AI Chatbot project on a new computer from scratch.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.10 or higher** ([Download here](https://www.python.org/downloads/))
- **Git** ([Download here](https://git-scm.com/downloads)) (optional, if cloning from repository)
- **Google Gemini API Key** ([Get one here](https://aistudio.google.com/app/apikey))

## Step 1: Get the Project

### Option A: Clone from Repository (if using Git)
```bash
git clone <repository-url>
cd legal-chatbot
```

### Option B: Download and Extract
1. Download the project ZIP file
2. Extract to a folder (e.g., `d:\legal-chatbot`)
3. Open terminal/command prompt and navigate to the folder:
   ```bash
   cd d:\legal-chatbot
   ```

## Step 2: Create a Virtual Environment

It's recommended to use a virtual environment to avoid dependency conflicts:

### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` appear in your terminal prompt.

## Step 3: Install Dependencies

Install all required Python packages:

```bash
pip install -r requirements.txt
```

This will install all necessary libraries including:
- FastAPI & Uvicorn (API server)
- Google Gemini AI
- Sentence Transformers (embeddings)
- FAISS (vector database)
- Document processing libraries (pandas, openpyxl, etc.)

**Note:** This may take 5-10 minutes depending on your internet connection.

## Step 4: Set Up Environment Variables

1. Create a `.env` file in the `rag_engine` folder:
   ```bash
   cd rag_engine
   ```

2. Create the file and add your API key:

   **On Windows (Command Prompt):**
   ```bash
   echo GEMINI_API_KEY=your_actual_api_key_here > .env
   ```

   **On Windows (PowerShell):**
   ```powershell
   New-Item -Path .env -ItemType File
   Add-Content -Path .env -Value "GEMINI_API_KEY=your_actual_api_key_here"
   ```

   **On macOS/Linux:**
   ```bash
   echo "GEMINI_API_KEY=your_actual_api_key_here" > .env
   ```

   **Or manually create a file named `.env` with the following content:**
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. Replace `your_actual_api_key_here` with your actual Google Gemini API key.

## Step 5: Verify Directory Structure

Ensure the following folders exist in the `rag_engine` directory. If they don't exist, create them:

```bash
mkdir data
mkdir processed
mkdir uploads
mkdir vector_db
```

**On Windows:**
```bash
md data
md processed
md uploads
md vector_db
```

## Step 6: Test the Installation

### Test 1: Import Dependencies
```bash
python -c "import fastapi, sentence_transformers, google.genai; print('✓ All dependencies installed successfully!')"
```

### Test 2: Check API Key
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✓ API Key loaded!' if os.getenv('GEMINI_API_KEY') else '✗ API Key not found')"
```

## Step 7: Run the Application

Start the FastAPI server:

```bash
cd rag_engine
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Step 8: Verify the API is Running

Open your browser and navigate to:
- **API Status:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

You should see the FastAPI interactive documentation.

## Usage

### Upload a Document
Use the `/upload` endpoint to upload legal documents:
```bash
curl -X POST "http://localhost:8000/upload" \
     -F "file=@path/to/your/document.pdf"
```

### Ask a Question
Use the `/ask` endpoint to query the uploaded documents:
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "What are the payment terms?"}'
```

Or use the interactive API docs at http://localhost:8000/docs

## Troubleshooting

### Issue: `ModuleNotFoundError`
**Solution:** Make sure you activated the virtual environment and installed all dependencies:
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Issue: `GEMINI_API_KEY not found`
**Solution:** 
1. Verify the `.env` file exists in the `rag_engine` folder
2. Check that the API key is correctly formatted: `GEMINI_API_KEY=your_key_here`
3. No quotes around the key value
4. No spaces around the `=` sign

### Issue: `Port 8000 already in use`
**Solution:** Either stop the process using port 8000, or run on a different port:
```bash
uvicorn main:app --reload --port 8001
```

### Issue: Installing dependencies is slow
**Solution:** This is normal. The project uses PyTorch and other large ML libraries. On slower connections, it may take 10-15 minutes.

### Issue: Permission errors on Windows
**Solution:** Run your terminal/command prompt as Administrator.

## Development Tools (Optional)

For development, you may want to install:

```bash
pip install pytest  # For testing
pip install black   # For code formatting
pip install pylint  # For linting
```

## Next Steps

1. Place your legal documents in the `rag_engine/data` folder
2. Use the `/upload` endpoint to process them
3. Start asking questions via the `/ask` endpoint

## System Requirements

- **RAM:** Minimum 4GB, recommended 8GB or more
- **Storage:** At least 5GB free space (for dependencies and models)
- **Internet:** Required for initial setup and API calls

## Additional Notes

- The first time you run the application, sentence-transformers will download the embedding model (~500MB)
- FAISS vector indices are stored in the `vector_db` folder
- Uploaded documents are stored in the `uploads` folder
- Processed data is cached in the `processed` folder

---

**Need Help?** Check the project README.md or raise an issue in the project repository.

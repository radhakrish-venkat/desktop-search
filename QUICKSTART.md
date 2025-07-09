# Desktop Search Quickstart

Welcome to Desktop Search! This guide will get you up and running with fast, private, and AI-powered document search in just a few minutes.

---

## 1. Install Requirements

Clone the repo and install dependencies:
```bash
git clone <repository-url>
cd desktop-search
pip install -r requirements.txt
```

---

## 2. Initialize the App

Check and set up all required components:
```bash
python main.py status
python main.py init
```

To reset everything from scratch:
```bash
python main.py reinitialize --force
```

---

## 3. Index Your Documents

Index a folder (PDF, DOCX, TXT, etc.):
```bash
python main.py index /path/to/your/documents
```

---

## 4. Start the API Server

Default (HTTP):
```bash
python start_api.py
```

With HTTPS (recommended for LLM features):
```bash
python start_https.py
```

---

## 5. Search Your Documents

### CLI Example
```bash
python main.py search "your search query"
```

### Web/API Example
Open [https://localhost:8443/docs](https://localhost:8443/docs) in your browser for interactive docs.

---

## 6. Enable LLM-Enhanced Search (ChatGPT-like)

### Requirements
- [Ollama](https://ollama.ai) or [LocalAI](https://localai.io) running locally
- Download a model (e.g., `ollama run phi3`)

### CLI Example
```bash
python main.py llm search "Summarize the project"
```

### API Example
```bash
curl -X POST "https://localhost:8443/api/v1/llm/search" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "project summary",
       "max_results": 5,
       "use_llm": true,
       "llm_model": "phi3",
       "embedding_model": "bge-small-en"
     }'
```

---

## 7. Model & Provider Info

- List models: `GET /api/v1/llm/models/available`
- List providers: `GET /api/v1/llm/providers/available`
- Change models: `POST /api/v1/llm/config`

---

## 8. Privacy & Security
- **All search and LLM processing is 100% local**
- **No data is sent to the cloud**
- **You control which models and providers are used**

---

## 9. More Resources
- [LLM_SETUP.md](LLM_SETUP.md) — Full LLM setup & troubleshooting
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) — Full API reference
- [README.md](README.md) — Features, architecture, and more

---

Happy searching! 🚀 
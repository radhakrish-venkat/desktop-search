# 🚀 Enhanced Hybrid Search System

A comprehensive document search and Q&A system that combines traditional keyword search, semantic search, and local LLM integration for powerful document discovery and question-answering capabilities.

## ✨ Core Features

### 🔍 Hybrid Search
- **Traditional Keyword Search**: BM25 algorithm for exact matches
- **Semantic Search**: Neural embeddings for meaning-based search
- **Hybrid Combination**: Weighted combination of both approaches
- **Advanced Chunking**: Intelligent document splitting with overlap

### 🤖 AI-Powered Q&A
- **Context-Aware Answers**: Uses retrieved documents as context
- **Session Management**: Threaded conversation history
- **Local LLM Integration**: Privacy-focused, no cloud dependencies
- **Source Attribution**: Links answers to source documents

### 📁 Enhanced Document Processing
- **Multi-Format Support**: PDF, DOCX, TXT, MD, HTML, CSV, JSON, and more
- **OCR Capabilities**: Text extraction from scanned documents
- **Code Recognition**: Intelligent parsing of programming files
- **Metadata Extraction**: Language detection, content analysis

### 🎨 Modern Interface
- **Multiple Themes**: Default, Sunset, Forest, Midnight themes
- **Responsive Design**: Works on desktop and mobile
- **Real-time Search**: Instant results with progress indicators
- **Session Management**: Easy Q&A conversation tracking

## 🏗️ Architecture

```
[ Enhanced Document Parser ]
           ↓
[ Text Chunking + Preprocessing ]
           ↓
[ Dual Indexing: Vector + Keyword ]
           ↓
[ Hybrid Search Engine ]
           ↓
[ Local LLM Integration ]
           ↓
[ Notebook-style Q&A Interface ]
```

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Vector Search** | ChromaDB + Sentence Transformers | Semantic similarity search |
| **Keyword Search** | Whoosh + BM25 | Traditional text search |
| **Document Parsing** | Unstructured + Custom Parsers | Multi-format document processing |
| **LLM Integration** | Local LLM (Ollama/Phi-3) | Question answering |
| **Storage** | SQLite + ChromaDB | Persistent data storage |
| **API** | FastAPI | RESTful API endpoints |
| **Frontend** | HTML/CSS/JavaScript | Modern web interface |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python start_api.py
```

### 3. Access the Interface

- **Main Interface**: http://localhost:8880/index.html
- **Enhanced Search**: http://localhost:8880/enhanced-search.html
- **API Documentation**: http://localhost:8880/docs

### 4. Test the System

```bash
python test_enhanced_search.py
```

## 📖 Usage Guide

### Document Indexing

1. **Via Web Interface**:
   - Navigate to the Enhanced Search interface
   - Enter directory path in the indexing section
   - Configure chunk size and overlap
   - Click "Index Documents"

2. **Via API**:
```bash
curl -X POST "http://localhost:8880/api/v1/enhanced-search/index" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/path/to/documents",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "embedding_model": "all-MiniLM-L6-v2"
  }'
```

### Hybrid Search

1. **Web Interface**:
   - Enter search query
   - Choose search type (Hybrid, Semantic, Keyword)
   - Adjust weights for hybrid search
   - View results with scores and metadata

2. **API**:
```bash
curl -X POST "http://localhost:8880/api/v1/enhanced-search/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "n_results": 10,
    "semantic_weight": 0.7,
    "keyword_weight": 0.3
  }'
```

### AI Q&A

1. **Web Interface**:
   - Start a new session or continue existing
   - Ask questions in natural language
   - View AI-generated answers with sources
   - Browse conversation history

2. **API**:
```bash
curl -X POST "http://localhost:8880/api/v1/enhanced-search/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "session_id": "optional-session-id",
    "include_sources": true
  }'
```

## 🔌 API Endpoints

### Core Search Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/enhanced-search/index` | POST | Index documents |
| `/api/v1/enhanced-search/search` | POST | Hybrid search |
| `/api/v1/enhanced-search/semantic-search` | GET | Semantic search only |
| `/api/v1/enhanced-search/keyword-search` | GET | Keyword search only |

### Q&A Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/enhanced-search/ask` | POST | Ask a question |
| `/api/v1/enhanced-search/sessions` | GET | List Q&A sessions |
| `/api/v1/enhanced-search/session/{id}` | GET | Get session details |
| `/api/v1/enhanced-search/session/{id}` | DELETE | Delete session |

### System Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/enhanced-search/stats` | GET | System statistics |
| `/api/v1/enhanced-search/health` | GET | Health check |
| `/api/v1/enhanced-search/clear-index` | POST | Clear search index |

## ⚙️ Configuration

### Search Configuration

```python
# Enhanced search configuration
search_config = {
    "chunk_size": 1000,           # Characters per chunk
    "chunk_overlap": 200,         # Overlap between chunks
    "embedding_model": "all-MiniLM-L6-v2",  # Sentence transformer model
    "semantic_weight": 0.7,       # Weight for semantic search
    "keyword_weight": 0.3,        # Weight for keyword search
    "enable_llm": True,           # Enable LLM integration
    "max_results": 10             # Default max results
}
```

### LLM Configuration

```python
# Local LLM configuration
llm_config = {
    "llm_model": "phi3",          # LLM model name
    "llm_max_tokens": 2048,       # Max response tokens
    "llm_temperature": 0.7,       # Response creativity
    "embedding_model": "all-MiniLM-L6-v2",  # Embedding model
    "enable_gpu": True,           # Use GPU acceleration
    "cache_responses": True       # Cache LLM responses
}
```

## 📊 Performance Features

### Search Performance
- **Vector Search**: Fast similarity search using HNSW index
- **Keyword Search**: Efficient BM25 ranking
- **Hybrid Combination**: Weighted score fusion
- **Caching**: Response caching for repeated queries

### LLM Performance
- **Local Processing**: No cloud dependencies
- **Response Caching**: LRU cache for common questions
- **Batch Processing**: Efficient handling of multiple requests
- **Context Optimization**: Smart context window management

### Document Processing
- **Parallel Processing**: Multi-threaded document parsing
- **Memory Optimization**: Streaming processing for large files
- **Format Detection**: Automatic file type recognition
- **Error Recovery**: Graceful handling of corrupted files

## 🔒 Privacy & Security

### Local-First Architecture
- **No Cloud Dependencies**: All processing happens locally
- **Data Privacy**: Documents never leave your system
- **Secure Storage**: Encrypted local database storage
- **Access Control**: Optional API key authentication

### Security Features
- **Input Validation**: Comprehensive input sanitization
- **File Type Validation**: Secure file processing
- **Rate Limiting**: Protection against abuse
- **Error Handling**: Secure error messages

## 🧪 Testing

### Automated Tests
```bash
# Run comprehensive test suite
python test_enhanced_search.py

# Test specific components
python -m pytest tests/test_enhanced_search.py
```

### Manual Testing
1. **Index Test Documents**: Use the test script to create sample documents
2. **Search Functionality**: Test various search queries and types
3. **Q&A Testing**: Ask questions and verify responses
4. **Performance Testing**: Test with large document collections

## 🚀 Advanced Features

### Custom Embeddings
```python
# Use custom embedding models
from sentence_transformers import SentenceTransformer

custom_model = SentenceTransformer("your-custom-model")
search = EnhancedHybridSearch(embedding_model=custom_model)
```

### Custom Document Parsers
```python
# Extend document parsing
from pkg.file_parsers.enhanced_parsers import EnhancedDocumentParser

parser = EnhancedDocumentParser(
    enable_ocr=True,
    enable_unstructured=True
)
```

### Session Management
```python
# Advanced session handling
session = search.get_qa_session("session-id")
session.add_question("question", "answer", results, tokens)
```

## 📈 Monitoring & Analytics

### System Statistics
- **Document Counts**: Vector and keyword document counts
- **Search Metrics**: Query performance and result quality
- **LLM Usage**: Token consumption and response times
- **Session Analytics**: Q&A session statistics

### Health Monitoring
- **Component Health**: Individual system component status
- **Performance Metrics**: Response times and throughput
- **Error Tracking**: Error rates and types
- **Resource Usage**: Memory and CPU utilization

## 🔧 Troubleshooting

### Common Issues

1. **LLM Not Available**:
   - Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
   - Pull model: `ollama pull phi3`
   - Check connection: `curl http://localhost:11434/api/tags`

2. **Embedding Model Issues**:
   - Clear cache: `rm -rf ~/.cache/torch/sentence_transformers`
   - Reinstall: `pip install --force-reinstall sentence-transformers`

3. **Performance Issues**:
   - Reduce chunk size for faster indexing
   - Use smaller embedding models
   - Enable GPU acceleration if available

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests: `python -m pytest`
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add comprehensive docstrings
- Include unit tests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Sentence Transformers**: For semantic search capabilities
- **ChromaDB**: For vector storage and similarity search
- **Whoosh**: For keyword search functionality
- **Ollama**: For local LLM integration
- **FastAPI**: For the web API framework

## 📞 Support

- **Documentation**: Check the API docs at `/docs`
- **Issues**: Report bugs on GitHub
- **Discussions**: Join community discussions
- **Email**: Contact the development team

---

**Happy Searching! 🔍✨** 
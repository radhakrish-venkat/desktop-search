# Local LLM Integration Setup Guide

This guide will help you set up local LLM integration to enhance your search with ChatGPT-like capabilities while keeping everything private and local.

## 🎯 Overview

The Desktop Search application now supports local LLM integration that provides:

- **Enhanced Search Results**: Get AI-generated insights and summaries of search results
- **Question Answering**: Ask specific questions and get answers based on your documents
- **Document Summarization**: Generate comprehensive summaries of search results
- **100% Private**: All processing happens locally, no data leaves your machine
- **Ollama Integration**: Fast, easy-to-use local LLM server
- **Multiple Models**: Choose from phi3, mistral, llama2, codellama, and more
- **Multiple Embeddings**: bge-small-en, nomic-embed-text, all-MiniLM-L6-v2

## 🚀 Quick Start

### 1. Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### 2. Download a Model

```bash
# Download a model (choose one)
ollama pull phi3      # Fast, efficient
ollama pull mistral   # Good balance
ollama pull llama2    # Powerful
ollama pull codellama # Code-focused
```

### 3. Test the Integration

```bash
# Check LLM status
curl -X GET "https://localhost:8443/api/v1/llm/status"

# Try enhanced search
curl -X POST "https://localhost:8443/api/v1/llm/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "max_results": 5,
    "use_llm": true,
    "llm_model": "phi3",
    "embedding_model": "bge-small-en"
  }'

# Ask a question
curl -X POST "https://localhost:8443/api/v1/llm/question" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main benefits of machine learning?",
    "query": "machine learning",
    "max_results": 5
  }'

# Generate a summary
curl -X POST "https://localhost:8443/api/v1/llm/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "max_results": 5
  }'
```

## 🔧 Detailed Setup

### Ollama Setup

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Start Ollama
   ollama serve
   ```

2. **Download Models**:
   ```bash
   # Download a model
   ollama pull phi3
   
   # List available models
   ollama list
   
   # Test the model
   ollama run phi3 "Hello, how are you?"
   ```

3. **Verify Installation**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Should return JSON with available models
   ```

## 📖 Usage Examples

### Enhanced Search

Get AI-generated insights about your search results:

```bash
# Basic enhanced search
curl -X POST "https://localhost:8443/api/v1/llm/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "max_results": 5,
    "use_llm": true,
    "llm_model": "phi3",
    "embedding_model": "bge-small-en"
  }'
```

**Response**:
```json
{
  "enhanced": true,
  "query": "machine learning algorithms",
  "llm_response": "Based on the search results, I found several key documents discussing various ML algorithms...",
  "results": [...],
  "provider": "OllamaProvider",
  "llm_model": "phi3",
  "embedding_model": "bge-small-en"
}
```

### Question Answering

Ask specific questions about your documents:

```bash
curl -X POST "https://localhost:8443/api/v1/llm/question" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main challenges in implementing machine learning?",
    "query": "machine learning",
    "max_results": 10
  }'
```

**Response**:
```json
{
  "answered": true,
  "question": "What are the main challenges in implementing machine learning?",
  "answer": "Based on the documents in your collection, the main challenges include...",
  "provider": "OllamaProvider",
  "llm_model": "phi3",
  "embedding_model": "bge-small-en",
  "sources": ["/path/to/doc1.txt", "/path/to/doc2.pdf"]
}
```

### Document Summarization

Generate comprehensive summaries of search results:

```bash
curl -X POST "https://localhost:8443/api/v1/llm/summary" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence applications",
    "max_results": 10
  }'
```

**Response**:
```json
{
  "summarized": true,
  "summary": "Based on the search results for 'artificial intelligence applications', here are the key findings...",
  "provider": "OllamaProvider",
  "llm_model": "phi3",
  "embedding_model": "bge-small-en",
  "result_count": 10
}
```

## 🌐 API Reference

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/llm/status` | GET | Get LLM provider status and model info |
| `/api/v1/llm/models/available` | GET | List available LLM and embedding models |
| `/api/v1/llm/providers/available` | GET | List detected LLM providers |
| `/api/v1/llm/config` | POST | Configure LLM and embedding models |
| `/api/v1/llm/search` | POST | Enhanced search with LLM insights |
| `/api/v1/llm/question` | POST | Ask questions about documents |
| `/api/v1/llm/summary` | POST | Generate summaries of search results |

### Model Configuration

```bash
curl -X POST "https://localhost:8443/api/v1/llm/config" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_model": "phi3",
    "embedding_model": "bge-small-en",
    "llm_max_tokens": 1024,
    "llm_temperature": 0.7,
    "llm_top_p": 0.9
  }'
```

### Check Available Models

```bash
curl -X GET "https://localhost:8443/api/v1/llm/models/available"
```

**Response**:
```json
{
  "llm_models": [
    {"name": "phi3", "description": "Fast, efficient model good for reasoning"},
    {"name": "mistral", "description": "Powerful model for complex tasks"},
    {"name": "llama2", "description": "General purpose model"},
    {"name": "codellama", "description": "Code-focused model"}
  ],
  "embedding_models": [
    {"name": "bge-small-en", "description": "High quality English embeddings"},
    {"name": "nomic-embed-text", "description": "Good multilingual support"},
    {"name": "all-MiniLM-L6-v2", "description": "Fast general purpose embeddings"}
  ]
}
```

## 🔧 Configuration

### Model Configuration

You can customize the LLM behavior by modifying the configuration:

```python
# In pkg/llm/local_llm.py
@dataclass
class LLMConfig:
    llm_model: str = "phi3"           # Change default LLM model
    embedding_model: str = "bge-small-en"  # Change default embedding model
    llm_max_tokens: int = 2048        # Adjust response length
    llm_temperature: float = 0.7       # Control creativity (0.0-1.0)
    llm_top_p: float = 0.9            # Nucleus sampling
    llm_context_window: int = 4096     # Context window size
```

### Provider Selection

The system automatically detects Ollama, but you can check status:

```bash
# Check LLM status
curl -X GET "https://localhost:8443/api/v1/llm/status"
```

## 🛠️ Troubleshooting

### Common Issues

1. **No LLM Providers Available**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Start Ollama if needed
   ollama serve
   ```

2. **Model Not Found**:
   ```bash
   # List available models
   ollama list
   
   # Download a model
   ollama pull phi3
   ```

3. **Slow Responses**:
   - Use smaller models for faster responses (phi3, mistral)
   - Reduce `llm_max_tokens` in configuration
   - Use GPU acceleration if available

4. **Memory Issues**:
   - Use smaller models
   - Reduce `llm_context_window` size
   - Close other applications

5. **404/405 Errors**:
   - Ensure the API server is running
   - Check that the LLM router is properly included
   - Verify the endpoint URLs are correct

### Performance Optimization

1. **Model Selection**:
   ```bash
   # Fast models
   ollama pull phi3      # Small, fast
   ollama pull mistral   # Good balance
   
   # Powerful models
   ollama pull llama2    # Large, powerful
   ollama pull codellama # Code-focused
   ```

2. **Embedding Model Selection**:
   - `bge-small-en`: Best for English content
   - `nomic-embed-text`: Good for multilingual content
   - `all-MiniLM-L6-v2`: Fast general purpose

3. **Hardware Requirements**:
   - **Minimum**: 8GB RAM, 4GB free space
   - **Recommended**: 16GB RAM, 8GB free space
   - **GPU**: Optional but recommended for faster inference

4. **System Resources**:
   ```bash
   # Monitor resource usage
   htop  # CPU and memory
   nvidia-smi  # GPU usage (if available)
   ```

## 🔒 Privacy & Security

### Data Privacy

- **100% Local**: All LLM processing happens on your machine
- **No Internet Required**: Once models are downloaded, no internet needed
- **No Data Collection**: No telemetry or data collection
- **Secure Storage**: All data stays on your local system

### Security Features

- **Model Verification**: Models are verified before use
- **Input Sanitization**: All inputs are sanitized
- **Error Handling**: Graceful error handling without data leakage
- **Resource Limits**: Built-in limits to prevent resource exhaustion

## 📚 Advanced Usage

### Custom Prompts

You can customize the prompts used by the LLM:

```python
# In pkg/llm/local_llm.py
def enhance_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Custom prompt for enhanced search
    prompt = f"""
    Based on the search results for '{query}', provide:
    1. Key findings and insights
    2. Patterns and trends
    3. Recommendations and next steps
    4. Potential applications
    
    Focus on actionable insights and practical recommendations.
    """
```

### Multiple Models

You can use different models for different tasks:

```python
# Configure different models for different tasks
enhancement_config = LLMConfig(llm_model="phi3", llm_temperature=0.7)
summarization_config = LLMConfig(llm_model="mistral", llm_temperature=0.5)
question_config = LLMConfig(llm_model="codellama", llm_temperature=0.3)
```

### Batch Processing

For processing multiple queries:

```bash
# Process multiple questions
for question in "What is ML?" "How does AI work?" "Benefits of automation"; do
    curl -X POST "https://localhost:8443/api/v1/llm/question" \
      -H "Content-Type: application/json" \
      -d "{\"question\": \"$question\", \"query\": \"$question\", \"max_results\": 5}"
done
```

## 🎯 Best Practices

1. **Model Selection**:
   - Use `phi3` for fast, general responses
   - Use `mistral` for complex reasoning tasks
   - Use `codellama` for code-related queries
   - Use `bge-small-en` for English embeddings

2. **Query Optimization**:
   - Be specific in your questions
   - Use relevant keywords
   - Adjust `max_results` based on needs

3. **Resource Management**:
   - Monitor system resources
   - Close unused models
   - Use appropriate batch sizes

4. **Quality Assurance**:
   - Review LLM outputs
   - Cross-reference with original documents
   - Use multiple models for verification

## 🆘 Support

### Getting Help

1. **Check Status**:
   ```bash
   curl -X GET "https://localhost:8443/api/v1/llm/status"
   ```

2. **Test Basic Functionality**:
   ```bash
   # Test Ollama connection
   curl http://localhost:11434/api/tags
   ```

3. **Common Commands**:
   ```bash
   # Restart Ollama
   pkill ollama && ollama serve
   
   # Check logs
   ollama logs
   ```

### Resources

- **Ollama**: https://ollama.ai/
- **Model Hub**: https://huggingface.co/
- **Documentation**: Check the main README.md and API_DOCUMENTATION.md

## ✅ Success Checklist

- [ ] Ollama installed and running
- [ ] Model downloaded and working
- [ ] Service running and accessible
- [ ] API server started (`python start_https.py`)
- [ ] Enhanced search working (`/api/v1/llm/search`)
- [ ] Question answering working (`/api/v1/llm/question`)
- [ ] Summary generation working (`/api/v1/llm/summary`)
- [ ] API endpoints accessible
- [ ] Performance acceptable
- [ ] Privacy verified (no external calls)

Once you've completed this checklist, you have a fully functional local LLM-enhanced search system that provides ChatGPT-like capabilities while keeping everything private and secure! 
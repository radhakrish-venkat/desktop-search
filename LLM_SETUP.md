# Local LLM Integration Setup Guide

This guide will help you set up local LLM integration to enhance your search with ChatGPT-like capabilities while keeping everything private and local.

## 🎯 Overview

The Desktop Search application now supports local LLM integration that provides:

- **Enhanced Search Results**: Get AI-generated insights and summaries of search results
- **Question Answering**: Ask specific questions and get answers based on your documents
- **Document Summarization**: Generate comprehensive summaries of search results
- **100% Private**: All processing happens locally, no data leaves your machine
- **Multiple LLM Providers**: Support for Ollama and LocalAI

## 🚀 Quick Start

### 1. Install a Local LLM Provider

Choose one of the following options:

#### Option A: Ollama (Recommended)
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

#### Option B: LocalAI
```bash
# Using Docker
docker run -d -p 8080:8080 localai/localai:latest

# Or build from source
git clone https://github.com/go-skynet/LocalAI
cd LocalAI
make build
```

### 2. Download a Model

#### For Ollama:
```bash
# Download a model (choose one)
ollama pull llama2
ollama pull codellama
ollama pull mistral
ollama pull phi2
```

#### For LocalAI:
```bash
# Models are automatically downloaded when first used
# Popular models: gpt4all, llama2, codellama
```

### 3. Test the Integration

```bash
# Check LLM status
python main.py llm status

# Try enhanced search
python main.py llm enhanced-search "machine learning"

# Ask a question
python main.py llm ask-question "What are the main benefits of machine learning?"

# Generate a summary
python main.py llm summarize "artificial intelligence"
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
   ollama pull llama2
   
   # List available models
   ollama list
   
   # Test the model
   ollama run llama2 "Hello, how are you?"
   ```

3. **Verify Installation**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Should return JSON with available models
   ```

### LocalAI Setup

1. **Install LocalAI**:
   ```bash
   # Using Docker (recommended)
   docker run -d -p 8080:8080 localai/localai:latest
   
   # Or build from source
   git clone https://github.com/go-skynet/LocalAI
   cd LocalAI
   make build
   ./localai
   ```

2. **Configure Models**:
   ```bash
   # Create models directory
   mkdir -p models
   
   # Download a model (example for gpt4all)
   wget https://gpt4all.io/models/ggml-gpt4all-j-v1.3-groin.bin -O models/gpt4all
   ```

3. **Verify Installation**:
   ```bash
   # Check if LocalAI is running
   curl http://localhost:8080/v1/models
   
   # Should return JSON with available models
   ```

## 📖 Usage Examples

### Enhanced Search

Get AI-generated insights about your search results:

```bash
# Basic enhanced search
python main.py llm enhanced-search "machine learning algorithms"

# With specific parameters
python main.py llm enhanced-search "data analysis" \
  --search-type semantic \
  --limit 15 \
  --threshold 0.4
```

**Output**:
```
🔍 Enhanced search for: 'machine learning algorithms' (using local LLM)
✅ Found LLM providers: ollama

🤖 Enhancing results with local LLM...

📊 LLM Insights:
============================================================
Based on the search results for 'machine learning algorithms', 
I found several key documents discussing various ML algorithms:

1. **Supervised Learning**: Documents mention algorithms like 
   linear regression, decision trees, and neural networks.

2. **Unsupervised Learning**: Clustering algorithms like K-means 
   and dimensionality reduction techniques are covered.

3. **Deep Learning**: Several documents discuss neural networks, 
   CNNs, and RNNs for complex pattern recognition.

Key recommendations:
- Start with simpler algorithms for basic problems
- Use cross-validation for model evaluation
- Consider ensemble methods for better performance
============================================================
Provider: OllamaProvider

📄 Search Results (5 found):
----------------------------------------
1. File: /path/to/ml_guide.pdf
   Snippet: This comprehensive guide covers machine learning algorithms...
   Score: 0.892
```

### Question Answering

Ask specific questions about your documents:

```bash
# Ask a question
python main.py llm ask-question "What are the main challenges in implementing machine learning?"

# With more results
python main.py llm ask-question "How do neural networks work?" \
  --max-results 20 \
  --threshold 0.3
```

**Output**:
```
❓ Question: 'What are the main challenges in implementing machine learning?'

🤖 Generating answer with local LLM...

💡 Answer:
============================================================
Based on the documents in your collection, the main challenges 
in implementing machine learning include:

1. **Data Quality**: Ensuring clean, relevant, and sufficient 
   training data is often the biggest challenge.

2. **Model Selection**: Choosing the right algorithm for the 
   specific problem and data characteristics.

3. **Computational Resources**: Training complex models requires 
   significant computational power and time.

4. **Interpretability**: Making models explainable and 
   understandable to stakeholders.

5. **Deployment**: Moving from development to production 
   environments with proper monitoring and maintenance.

The documents suggest starting with simpler models and gradually 
increasing complexity as needed.
============================================================
Provider: OllamaProvider

📚 Sources (8 documents):
   1. /path/to/ml_challenges.pdf
   2. /path/to/deployment_guide.pdf
   3. /path/to/best_practices.pdf
   ... and 3 more
```

### Document Summarization

Generate comprehensive summaries of search results:

```bash
# Generate summary
python main.py llm summarize "artificial intelligence applications"

# With more documents
python main.py llm summarize "data science" \
  --max-results 30 \
  --threshold 0.2
```

**Output**:
```
📝 Generating summary for: 'artificial intelligence applications'

🤖 Generating summary with local LLM...

📋 Summary:
============================================================
Based on the search results for 'artificial intelligence applications', 
here are the key findings:

**Main Application Areas:**
1. **Healthcare**: AI is being used for medical diagnosis, 
   drug discovery, and personalized treatment plans.

2. **Finance**: Applications include fraud detection, 
   algorithmic trading, and risk assessment.

3. **Transportation**: Self-driving cars, traffic optimization, 
   and logistics management.

4. **Education**: Personalized learning, automated grading, 
   and educational content generation.

**Key Trends:**
- Increasing focus on explainable AI
- Integration with IoT devices
- Growing emphasis on ethical AI development
- Rise of edge computing for AI applications

**Challenges Identified:**
- Data privacy and security concerns
- Need for regulatory frameworks
- Skills gap in AI expertise
- Bias and fairness in AI systems
============================================================
Provider: OllamaProvider
Documents analyzed: 15
```

## 🌐 API Usage

### Enhanced Search API

```bash
# Enhanced search endpoint
curl -X POST "https://localhost:8443/api/v1/llm/enhanced-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning",
    "search_type": "semantic",
    "limit": 10,
    "threshold": 0.3
  }'
```

### Question Answering API

```bash
# Ask a question
curl -X POST "https://localhost:8443/api/v1/llm/ask-question" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the benefits of machine learning?",
    "max_results": 10,
    "threshold": 0.3
  }'
```

### Summary Generation API

```bash
# Generate summary
curl -X POST "https://localhost:8443/api/v1/llm/generate-summary" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence",
    "max_results": 20,
    "threshold": 0.3
  }'
```

### LLM Status API

```bash
# Check LLM status
curl -X GET "https://localhost:8443/api/v1/llm/llm-status"
```

## 🔧 Configuration

### Model Configuration

You can customize the LLM behavior by modifying the configuration:

```python
# In pkg/llm/local_llm.py
@dataclass
class LLMConfig:
    model_name: str = "llama2"  # Change default model
    max_tokens: int = 2048      # Adjust response length
    temperature: float = 0.7     # Control creativity (0.0-1.0)
    top_p: float = 0.9          # Nucleus sampling
    context_window: int = 4096   # Context window size
```

### Provider Selection

The system automatically detects available providers, but you can manually set one:

```bash
# Set active provider
curl -X POST "https://localhost:8443/api/v1/llm/set-llm-provider" \
  -H "Content-Type: application/json" \
  -d '"ollama"'
```

## 🛠️ Troubleshooting

### Common Issues

1. **No LLM Providers Available**:
   ```bash
   # Check if Ollama is running
   curl http://localhost:11434/api/tags
   
   # Check if LocalAI is running
   curl http://localhost:8080/v1/models
   
   # Start the service if needed
   ollama serve  # For Ollama
   ```

2. **Model Not Found**:
   ```bash
   # List available models
   ollama list  # For Ollama
   
   # Download a model
   ollama pull llama2  # For Ollama
   ```

3. **Slow Responses**:
   - Use smaller models for faster responses
   - Reduce `max_tokens` in configuration
   - Use GPU acceleration if available

4. **Memory Issues**:
   - Use smaller models
   - Reduce `context_window` size
   - Close other applications

### Performance Optimization

1. **Model Selection**:
   ```bash
   # Fast models
   ollama pull phi2      # Small, fast
   ollama pull mistral   # Good balance
   
   # Powerful models
   ollama pull llama2    # Large, powerful
   ollama pull codellama # Code-focused
   ```

2. **Hardware Requirements**:
   - **Minimum**: 8GB RAM, 4GB free space
   - **Recommended**: 16GB RAM, 8GB free space
   - **GPU**: Optional but recommended for faster inference

3. **System Resources**:
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
enhancement_config = LLMConfig(model_name="llama2", temperature=0.7)
summarization_config = LLMConfig(model_name="mistral", temperature=0.5)
question_config = LLMConfig(model_name="codellama", temperature=0.3)
```

### Batch Processing

For processing multiple queries:

```bash
# Process multiple questions
for question in "What is ML?" "How does AI work?" "Benefits of automation"; do
    python main.py llm ask-question "$question"
done
```

## 🎯 Best Practices

1. **Model Selection**:
   - Use smaller models for faster responses
   - Use specialized models for specific domains
   - Test different models for your use case

2. **Query Optimization**:
   - Be specific in your questions
   - Use relevant keywords
   - Adjust threshold based on results

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
   python main.py llm status
   ```

2. **Test Basic Functionality**:
   ```bash
   # Test LLM connection
   curl http://localhost:11434/api/tags  # Ollama
   curl http://localhost:8080/v1/models  # LocalAI
   ```

3. **Common Commands**:
   ```bash
   # Restart Ollama
   pkill ollama && ollama serve
   
   # Restart LocalAI
   docker restart localai
   
   # Check logs
   ollama logs  # For Ollama
   docker logs localai  # For LocalAI
   ```

### Resources

- **Ollama**: https://ollama.ai/
- **LocalAI**: https://localai.io/
- **Model Hub**: https://huggingface.co/
- **Documentation**: Check the main README.md

## ✅ Success Checklist

- [ ] LLM provider installed (Ollama or LocalAI)
- [ ] Model downloaded and working
- [ ] Service running and accessible
- [ ] Enhanced search working
- [ ] Question answering working
- [ ] Summary generation working
- [ ] API endpoints accessible
- [ ] Performance acceptable
- [ ] Privacy verified (no external calls)

Once you've completed this checklist, you have a fully functional local LLM-enhanced search system that provides ChatGPT-like capabilities while keeping everything private and secure! 
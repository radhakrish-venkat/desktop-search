# Desktop Search

A fast and efficient local document search tool that indexes and searches through various file formats including PDF, DOCX, XLSX, PPTX, and TXT files. Built with Python and featuring a clean command-line interface.

## Features

### **Core Search Capabilities**
- **Multi-format Support**: Indexes PDF, DOCX, XLSX, PPTX, and TXT files
- **Fast Keyword Search**: Uses inverted indexing for quick search results
- **Smart Ranking**: TF-IDF scoring for relevant result ranking
- **Snippet Generation**: Shows context around search terms with highlighting
- **Persistent Indexing**: Save and load indexes for repeated use

### **Google Drive Integration**
- **Cloud File Support**: Index and search Google Drive files including Google Docs, Sheets, and Slides
- **Hybrid Indexing**: Combine local files and Google Drive files in a single searchable index
- **Offline Search**: Once indexed, search Google Drive content without internet connection
- **Real-time Search**: Direct Google Drive API search without pre-building indexes
- **Secure Authentication**: OAuth2 with read-only access to your Google Drive

### **Advanced Semantic Search**
- **Semantic Understanding**: Find related content even without exact keyword matches
- **ChromaDB Integration**: Vector database for storing document embeddings
- **Sentence Transformers**: State-of-the-art embedding models for semantic similarity
- **Hybrid Semantic Search**: Combines semantic and keyword matching for optimal results
- **Configurable Models**: Support for different sentence transformer models
- **Similarity Thresholds**: Adjustable similarity scores for result filtering

### **Unified Search Experience**
- **Cross-Platform Search**: Search across local files and Google Drive simultaneously
- **Source Transparency**: Clear indication of result sources (local vs cloud)
- **Unified Results**: Consistent ranking and display across all file sources
- **Smart Indexing**: Automatically detects existing indexes and uses incremental updates
- **Incremental Indexing**: Add new files without rebuilding entire index
- **Smart Change Detection**: Tracks file modifications using metadata and hashes

### **Developer Experience**
- **Type Safety**: Full type hints throughout the codebase
- **Comprehensive Testing**: Unit and integration tests for all components
- **Robust Error Handling**: Graceful handling of corrupted or unsupported files
- **Progress Tracking**: Shows indexing progress for large directories
- **Modular Architecture**: Clean separation of concerns with extensible design

### **🔒 Security Features**
- **Index Integrity Protection**: SHA256 hashes prevent index file tampering
- **Content Validation**: Detects and rejects suspicious file content patterns
- **Secure Token Storage**: Encrypted Google Drive authentication tokens
- **Sanitized Logging**: Automatic redaction of sensitive information in logs
- **File Type Verification**: MIME type detection for additional security
- **Input Validation**: Comprehensive path and parameter validation
- **No Code Injection**: No use of eval(), exec(), or shell commands

## Advantages

### **🚀 Performance Benefits**
- **Lightning Fast Search**: Inverted indexing provides sub-second search results
- **Offline Capability**: Search Google Drive content without internet connection after indexing
- **Efficient Memory Usage**: Smart file size limits and chunking prevent memory issues
- **Scalable Architecture**: Handles large document collections with progress tracking

### **🔍 Search Quality**
- **Semantic Intelligence**: Understands context and meaning, not just keywords
- **Hybrid Matching**: Combines semantic similarity with traditional keyword search
- **Smart Ranking**: TF-IDF scoring ensures most relevant results appear first
- **Context-Aware Snippets**: Shows relevant text portions with search term highlighting

### **☁️ Cloud Integration**
- **Seamless Hybrid Search**: Search local and cloud files with a single command
- **Secure Cloud Access**: OAuth2 authentication with minimal permissions (read-only)
- **Real-time Updates**: Direct Google Drive API search for fresh results
- **Offline Independence**: Once indexed, no internet required for searching

### **🛠️ Developer Friendly**
- **Type Safety**: Full type annotations for better code quality and IDE support
- **Comprehensive Testing**: High test coverage with unit and integration tests
- **Modular Design**: Clean architecture makes it easy to extend and maintain
- **Rich CLI**: Intuitive command-line interface with helpful error messages

### **🔒 Privacy & Security**
- **Local Processing**: All search processing happens on your machine
- **No Data Mining**: Your documents and search queries never leave your system
- **Minimal Permissions**: Google Drive integration only requests read access
- **Secure Storage**: Credentials and tokens stored locally with proper encryption
- **Content Validation**: Automatic detection of suspicious file content
- **Integrity Protection**: Index files protected against tampering

### **📊 Enterprise Ready**
- **Multiple File Formats**: Support for all major document types
- **Configurable Models**: Choose the best embedding model for your use case
- **Smart Indexing**: Automatically chooses incremental or full indexing based on existing state
- **Incremental Updates**: Add new files without rebuilding entire indexes
- **Smart Change Detection**: Tracks file modifications using metadata and hashes
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Security Auditing**: Built-in security features and validation

## 🔒 Security Summary

- **Index Integrity Protection:** All index files are protected with SHA256 hashes and structure validation. Any tampering or corruption is detected and blocked.
- **Content Validation:** Every file is checked for suspicious patterns (e.g., scripts, XSS) and only supported file types are processed.
- **Secure Google Drive Tokens:** Google Drive authentication tokens are encrypted using your system keyring or strong file-based encryption.
- **Sanitized Logging:** All logs are automatically sanitized to redact sensitive paths, tokens, and secrets.
- **Input Validation:** All user inputs and file paths are strictly validated.
- **No Code Injection:** The codebase does not use `eval`, `exec`, or shell commands.
- **Security-Focused Testing:** Dedicated security tests ensure all protections work as intended.
- **Best Practices:** Follows strong security practices for file permissions, dependency management, and error handling.

**For full details, see [SECURITY.md](SECURITY.md).**

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd desktop-search
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Dependencies

The following packages are required:
- `click` - Command-line interface
- `pypdf` - PDF text extraction
- `python-docx` - Word document parsing
- `openpyxl` - Excel spreadsheet parsing
- `python-pptx` - PowerPoint presentation parsing
- `chromadb` - Vector database for semantic search
- `sentence-transformers` - Sentence embeddings for semantic search
- `google-auth` - Google authentication
- `google-auth-oauthlib` - OAuth2 authentication for Google APIs
- `google-auth-httplib2` - HTTP client for Google APIs
- `google-api-python-client` - Google Drive API client
- `cryptography` - Encryption for secure token storage
- `keyring` - System keyring integration
- `python-magic` - File type detection

## Usage

### Command Line Interface

The application provides a unified CLI with the following commands:

**Index a directory (unified ChromaDB):**
```bash
python main.py index /path/to/your/documents
```
This uses smart indexing that automatically detects if an index already exists and uses incremental indexing for faster updates. All data is stored in `data/chroma_db`.

**Search for content:**
```bash
python main.py search "your search query"
```

**View index statistics:**
```bash
python main.py stats
```

### Web Interface

**Start the API server:**
```bash
# HTTP (default)
python start_api.py

# HTTPS (secure)
python start_https.py
```

**Access the web interface:**
- HTTP: http://localhost:8443
- HTTPS: https://localhost:8443

## 🌐 Network Access & Security Configuration

### Default Network Configuration

By default, the Desktop Search API is configured for **local network access**:

- **Host Binding**: `0.0.0.0` (accessible from all network interfaces)
- **Port**: `8443` (static port)
- **Local Access**: ✅ `https://localhost:8443` or `https://127.0.0.1:8443`
- **Network Access**: ✅ `https://YOUR_IP:8443` (accessible from other devices on your network)
- **Internet Access**: ❌ Not configured for external access

### 🔒 Security Considerations

**Current Default State:**
- ✅ **Local Network**: Other devices on your WiFi/LAN can access the API
- ❌ **Internet**: Not accessible from outside your network
- ⚠️ **Security**: Anyone on your local network can potentially access the API

### 🛡️ Restricting Access to Localhost Only

If you want to restrict access to **localhost only** (recommended for development):

#### Option 1: Environment Variable (Recommended)
```bash
# Restrict to localhost only
export HOST="127.0.0.1"
python start_https.py

# PowerShell
$env:HOST="127.0.0.1"
python start_https.py
```

#### Option 2: Configuration File
```bash
# Create .env file
echo "HOST=127.0.0.1" > .env
python start_https.py
```

#### Option 3: Direct Code Change
```python
# In api/config.py, change:
HOST: str = os.getenv("HOST", "127.0.0.1")  # localhost only
```

### 🌍 Network Access Scenarios

| Configuration | Local Access | Network Access | Internet Access | Use Case |
|---------------|-------------|----------------|-----------------|----------|
| `HOST=127.0.0.1` | ✅ | ❌ | ❌ | **Development/Security** |
| `HOST=0.0.0.0` | ✅ | ✅ | ❌ | **Current Default** |
| `HOST=0.0.0.0` + Port Forward | ✅ | ✅ | ✅ | **Production/Remote** |

### 🔧 Production Deployment

For production use with external access:

1. **Use a Reverse Proxy** (Recommended):
   ```bash
   # Example with nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;
       
       location / {
           proxy_pass https://127.0.0.1:8443;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Configure Firewall Rules**:
   ```bash
   # Allow only specific IPs
   sudo ufw allow from 192.168.1.0/24 to any port 8443
   
   # Or block external access
   sudo ufw deny 8443
   ```

3. **Use Environment Variables**:
   ```bash
   export HOST="127.0.0.1"  # Bind to localhost only
   export DEBUG="False"      # Disable debug mode
   export ALLOWED_ORIGINS="https://yourdomain.com"
   python start_https.py
   ```

### 🔍 Check Current Network Access

```bash
# Check what interfaces the server is listening on
netstat -an | grep 8443

# Expected output:
# tcp4       0      0  *.8443                 *.*                    LISTEN     # All interfaces
# tcp4       0      0  127.0.0.1.8443         *.*                    LISTEN     # Localhost only
```

### 🚨 Security Recommendations

1. **Development**: Use `HOST=127.0.0.1` for localhost-only access
2. **Testing**: Use `HOST=0.0.0.0` to test from other devices on your network
3. **Production**: Use reverse proxy (nginx/apache) with proper SSL certificates
4. **Firewall**: Configure firewall rules to restrict access as needed
5. **Authentication**: Always use API keys for production deployments
6. **HTTPS**: Use HTTPS in production with valid SSL certificates

**Generate SSL certificates for development:**
```bash
python generate_certs.py
```

**Production HTTPS setup:**
1. Get SSL certificates from a trusted CA (Let's Encrypt, Cloudflare, etc.)
2. Place certificates in the `certs/` directory:
   - `certs/key.pem` (private key)
   - `certs/cert.pem` (certificate)
3. Set proper permissions: `chmod 600 certs/key.pem && chmod 644 certs/cert.pem`
4. Start with HTTPS: `python start_https.py`

### Search Options

**Different search types:**
```bash
# Semantic search (default)
python main.py search "your query" --search-type semantic

# Keyword search
python main.py search "your query" --search-type keyword

# Hybrid search (combines semantic and keyword)
python main.py search "your query" --search-type hybrid
```

**Customize search parameters:**
```bash
# Limit results
python main.py search "your query" --limit 20

# Adjust similarity threshold for semantic search
python main.py search "your query" --threshold 0.5
```

**Force full indexing:**
```bash
python main.py index /path/to/documents --force-full
```

### Google Drive Integration

**Set up Google Drive credentials:**
```bash
python main.py gdrive setup /path/to/credentials.json
```

**Index Google Drive files:**
```bash
python main.py gdrive index-gdrive --folder-id "your_folder_id"
```

**Search Google Drive files:**
```bash
python main.py gdrive search-gdrive "your query"
```

### Web Interface

The application also includes a modern web interface for easy interaction:

1. **Start the API server:**
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8443
```

2. **Open the web interface:**
   - Navigate to `frontend/index.html` in your browser
   - Or serve it with a simple HTTP server: `python -m http.server 3000`

**Web Interface Features:**
- **Unified Search**: Search across all indexed directories with semantic, keyword, or hybrid search
- **Directory Management**: Add, remove, and refresh directories with real-time progress tracking
- **Statistics Dashboard**: View detailed index statistics and system information
- **Real-time Updates**: Live progress bars and status updates during indexing
- **Modern UI**: Clean, responsive design with intuitive navigation


### Security Testing

**Run security tests:**
```bash
python run_tests.py --security
```

**Run all tests including security:**
```bash
python run_tests.py
```

## Testing

The application includes comprehensive tests for all functionality:

```bash
# Run all tests
python run_tests.py

# Run only security tests
python run_tests.py --security

# Run specific test modules
python -m pytest tests/test_security.py
python -m pytest tests/test_integration.py
```

## Architecture

The application follows a modular architecture:

1. **CLI Layer**: Command-line interface using Click
2. **Indexer**: Builds inverted index for fast searching with tokenization and stop word filtering
3. **Searcher**: Performs search operations with ranking and snippet generation
4. **File Parsers**: Extract text from various file formats (PDF, DOCX, XLSX, PPTX, TXT)
5. **Semantic Indexer**: Creates embeddings for semantic similarity search
6. **Google Drive Integration**: Handles cloud file indexing and search
7. **Security Layer**: Provides integrity protection, content validation, and secure logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security

For security issues, please email [security-email] instead of creating a public issue.

# Desktop Search

A fast and efficient local document search tool that indexes and searches through various file formats including PDF, DOCX, XLSX, PPTX, and TXT files. Built with Python and featuring a clean command-line interface.

## Features

- **Multi-format Support**: Indexes PDF, DOCX, XLSX, PPTX, and TXT files
- **Fast Search**: Uses inverted indexing for quick search results
- **Smart Ranking**: TF-IDF scoring for relevant result ranking
- **Semantic Search**: Advanced semantic search using ChromaDB and sentence-transformers
- **Hybrid Search**: Combines semantic and keyword matching for better results
- **Snippet Generation**: Shows context around search terms with highlighting
- **Persistent Indexing**: Save and load indexes for repeated use
- **Robust Error Handling**: Graceful handling of corrupted or unsupported files
- **Progress Tracking**: Shows indexing progress for large directories
- **Type Safety**: Full type hints throughout the codebase
- **Comprehensive Testing**: Unit and integration tests for all components

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

## Usage

### Basic Commands

**Index a directory:**
```bash
python main.py index /path/to/your/documents
```
This creates an `index.pkl` file in the indexed directory.

**Search for content:**
```bash
python main.py search "your search query"
```

### Advanced Usage

**Index and save to custom location:**
```bash
python main.py index /path/to/documents --save my_index.pkl
```

**Search with saved index:**
```bash
python main.py search "query" --load my_index.pkl
```

**Search in a specific directory (uses default index.pkl):**
```bash
python main.py search "query" --directory /path/to/documents
```

**Limit search results:**
```bash
python main.py search "query" --limit 5
```

**Index without saving to file:**
```bash
python main.py index /path/to/documents --no-save
```

**Get help:**
```bash
python main.py --help
python main.py index --help
python main.py search --help
```

### Semantic Search Commands

**Build semantic index:**
```bash
python main.py semantic-index /path/to/your/documents
```

**Semantic search:**
```bash
python main.py semantic-search "your semantic query"
```

**Hybrid search (semantic + keyword):**
```bash
python main.py semantic-search "your query" --hybrid
```

**Get semantic index statistics:**
```bash
python main.py semantic-stats
```

**Custom ChromaDB path:**
```bash
python main.py semantic-index /path/to/documents --db-path ./my_chroma_db
```

**Use different sentence transformer model:**
```bash
python main.py semantic-index /path/to/documents --model all-mpnet-base-v2
```

## Examples

### Indexing Documents
```bash
# Index your documents folder
$ python main.py index ~/Documents
Starting indexing of directory: /Users/username/Documents
Starting to index directory: /Users/username/Documents
Processed 100 files...
Processed 200 files...
Indexing complete. Processed 245 files, skipped 12 files.
Indexed 245 documents.
Index saved to: /Users/username/Documents/index.pkl
```

### Searching Content
```bash
# Search for "python programming"
$ python main.py search "python programming"
Searching for: 'python programming'

--- Search Results (3 found) ---
1. File: /Users/username/Documents/projects/python_tutorial.pdf
   Snippet: ...Python programming language is widely used for web development, data science, and automation...
2. File: /Users/username/Documents/notes/programming_notes.txt
   Snippet: ...Learn Python programming basics including variables, loops, and functions...
3. File: /Users/username/Documents/work/code_review.docx
   Snippet: ...The Python programming team needs to review the new API implementation...
```

### Search with Directory Option
```bash
# Search in a specific directory using its default index
$ python main.py search "javascript" --directory ~/Documents/projects
Searching for: 'javascript'

--- Search Results (2 found) ---
1. File: /Users/username/Documents/projects/web_app.js
   Snippet: ...JavaScript code for the web application...
```

### Semantic Search Examples
```bash
# Build semantic index
$ python main.py semantic-index ~/Documents
Starting semantic indexing of directory: /Users/username/Documents
Using model: all-MiniLM-L6-v2
ChromaDB path: ./chroma_db
Semantic indexing complete!
Files processed: 245
Chunks created: 1200
Files skipped: 12

# Semantic search for concepts
$ python main.py semantic-search "machine learning algorithms"
Performing semantic search for: 'machine learning algorithms'
ChromaDB path: ./chroma_db

--- Semantic Search Results (3 found) ---
1. File: ai_research.pdf
   Path: /Users/username/Documents/research/ai_research.pdf
   Chunk: 2/5
   Similarity: 0.892
   Snippet: The study explores various machine learning algorithms including neural networks, decision trees, and support vector machines...

# Hybrid search combining semantic and keyword matching
$ python main.py semantic-search "data analysis techniques" --hybrid
Performing semantic search for: 'data analysis techniques'
ChromaDB path: ./chroma_db
Using hybrid search (semantic + keyword matching)...

--- Semantic Search Results (2 found) ---
1. File: statistics_guide.docx
   Path: /Users/username/Documents/guides/statistics_guide.docx
   Chunk: 1/3
   Combined Score: 0.945
   Snippet: This guide covers statistical analysis methods, data visualization techniques, and hypothesis testing procedures...
```

## Supported File Formats

| Format | Extension | Description | Dependencies |
|--------|-----------|-------------|--------------|
| PDF | `.pdf` | Portable Document Format | PyPDF2 |
| Word | `.docx` | Microsoft Word documents | python-docx |
| Excel | `.xlsx` | Microsoft Excel spreadsheets | openpyxl |
| PowerPoint | `.pptx` | Microsoft PowerPoint presentations | python-pptx |
| Text | `.txt` | Plain text files | Built-in |

## Architecture

The project follows a modular architecture with clear separation of concerns:

- **`main.py`**: Entry point that sets up the Python path and invokes the CLI
- **`cli_commands/cli.py`**: Command-line interface using Click framework
- **`pkg/file_parsers/parsers.py`**: File format parsers for text extraction
- **`pkg/indexer/core.py`**: Indexing engine with inverted index and TF-IDF
- **`pkg/indexer/semantic.py`**: Semantic indexing using ChromaDB and sentence-transformers
- **`pkg/searcher/core.py`**: Search engine with ranking and snippet generation

### Key Components

1. **File Parsers**: Extract text from various file formats with error handling
2. **Indexer**: Builds inverted index for fast searching with tokenization and stop word filtering
3. **Semantic Indexer**: Creates document embeddings and stores them in ChromaDB for semantic search
4. **Searcher**: Performs ranked search using TF-IDF scoring with snippet generation
5. **Semantic Searcher**: Performs semantic similarity search using sentence embeddings
6. **CLI**: User-friendly command-line interface with help and error handling

## Performance

- **Indexing**: Processes ~1000 files per minute (varies by file size and type)
- **Search**: Returns results in milliseconds
- **Memory**: Efficient memory usage with file size limits (50MB per file)
- **Storage**: Index files are typically 10-20% of original document size
- **Scalability**: Handles large directories with progress tracking

## Semantic Search Features

### Document Chunking
- **Smart Chunking**: Documents are split into overlapping chunks (1000 characters by default)
- **Sentence Boundary Awareness**: Chunks are created at sentence boundaries when possible
- **Overlap**: 200-character overlap between chunks to maintain context

### Embedding Models
- **Default Model**: `all-MiniLM-L6-v2` (fast and efficient)
- **Alternative Models**: Support for other sentence transformer models
- **Model Loading**: Automatic model download and caching

### Search Types
- **Semantic Search**: Pure semantic similarity using sentence embeddings
- **Hybrid Search**: Combines semantic similarity with keyword matching
- **Configurable Thresholds**: Adjustable similarity thresholds for result filtering

### Vector Database
- **ChromaDB**: Persistent vector database for storing embeddings
- **Cosine Similarity**: Uses cosine distance for similarity calculations
- **Efficient Retrieval**: Fast similarity search with configurable result limits

## Configuration

### File Size Limits
- Maximum file size: 50MB (configurable in `parsers.py`)
- Large files are automatically skipped to prevent memory issues

### Skip Patterns
The indexer automatically skips:
- Hidden files and directories (starting with `.`)
- System files (`.DS_Store`, `.pyc`, etc.)
- Development directories (`node_modules`, `__pycache__`, etc.)
- Version control directories (`.git`, `.svn`, etc.)
- Temporary files (`.tmp`, `.log`, etc.)
- IDE directories (`.vscode`, `.idea`, etc.)

### Stop Words
Common stop words are filtered out during indexing and search:
- Articles: the, a, an
- Prepositions: in, on, at, to, for, of, with, by
- Conjunctions: and, or, but
- Common verbs: is, are, was, were, have, has, had, do, does, did
- Pronouns: i, you, he, she, it, we, they, me, him, her, us, them

## Testing

The project includes comprehensive test coverage:

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test modules
python -m pytest tests/pkg/file_parsers/test_parsers.py
python -m pytest tests/pkg/indexer/test_core.py
python -m pytest tests/pkg/searcher/test_core.py
python -m pytest tests/test_integration.py

# Run tests with coverage
python -m pytest tests/ --cov=pkg --cov=cmd
```

### Test Individual Components
```bash
# Test file parsers
python -m pkg.file_parsers.parsers

# Test indexer
python -m pkg.indexer.core

# Test searcher
python -m pkg.searcher.core
```

### Test Types
- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test complete workflows and CLI commands
- **Error Handling Tests**: Test edge cases and error conditions
- **Performance Tests**: Test with larger datasets

## Troubleshooting

### Common Issues

**"Import could not be resolved" errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Restart your IDE/editor to refresh the Python environment
- Check that you're using the correct Python interpreter

**Large files not indexed:**
- Files larger than 50MB are automatically skipped
- Check file size and consider splitting large documents
- Verify the file is not corrupted

**No search results:**
- Ensure the directory was indexed successfully
- Check that the search terms are not all stop words
- Verify the index file exists and is not corrupted
- Try using the `--directory` option to specify the correct location

**Memory issues:**
- Reduce the number of files indexed at once
- Increase system memory or use smaller file batches
- Check for memory leaks in large directories

**File parsing errors:**
- Ensure required dependencies are installed for the file format
- Check file permissions and accessibility
- Verify file format is supported

## Development

### Project Structure
```
desktop-search/
├── main.py                 # Entry point
├── cli_commands/
│   ├── __init__.py
│   └── cli.py             # Command-line interface
├── pkg/
│   ├── __init__.py
│   ├── file_parsers/
│   │   ├── __init__.py
│   │   └── parsers.py     # File format parsers
│   ├── indexer/
│   │   ├── __init__.py
│   │   └── core.py        # Indexing engine
│   ├── searcher/
│   │   ├── __init__.py
│   │   └── core.py        # Search engine
│   └── utils/
│       └── __init__.py    # Utility functions
├── tests/
│   ├── __init__.py
│   ├── pkg/
│   │   ├── file_parsers/
│   │   │   └── test_parsers.py
│   │   ├── indexer/
│   │   │   └── test_core.py
│   │   └── searcher/
│   │       └── test_core.py
│   └── test_integration.py
├── requirements.txt       # Dependencies
└── README.md             # This file
```

### Code Quality
- **Type Hints**: Full type annotations throughout the codebase
- **Error Handling**: Comprehensive exception handling and logging
- **Documentation**: Detailed docstrings for all functions and classes
- **Testing**: High test coverage with unit and integration tests

### Adding New Features
1. Create feature branch
2. Add tests for new functionality
3. Implement the feature with proper error handling
4. Update documentation
5. Run all tests to ensure nothing is broken
6. Submit pull request

### Semantic Search Implementation Plan

#### Phase 1: Dependencies and Setup
```bash
# Add to requirements.txt
sentence-transformers>=2.2.0
torch>=1.9.0
```

#### Phase 2: Core Implementation
1. **Create semantic indexer** (`pkg/indexer/semantic.py`):
   - Load sentence transformer model
   - Generate embeddings for document chunks
   - Store embeddings with metadata

2. **Extend searcher** (`pkg/searcher/semantic.py`):
   - Implement semantic similarity search
   - Add hybrid search combining keyword + semantic
   - Configurable similarity thresholds

3. **Update CLI** (`cli_commands/cli.py`):
   - Add `--semantic` flag for semantic search
   - Add `--hybrid` flag for combined search
   - Add `--threshold` option for similarity threshold

#### Phase 3: Advanced Features
- Document chunking for better semantic matching
- Caching for improved performance
- Multiple model support
- Batch processing for large datasets

#### Example Usage (Future)
```bash
# Semantic search
python main.py search "machine learning algorithms" --semantic

# Hybrid search (keyword + semantic)
python main.py search "python programming" --hybrid --threshold 0.7

# Semantic search with custom model
python main.py search "data analysis" --semantic --model all-mpnet-base-v2
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with proper tests
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write tests for new functionality
- Update documentation as needed
- Ensure all tests pass before submitting

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## TODO

### Planned Features

#### Semantic Search with Sentence Transformers
- **Integration**: Add support for semantic search using sentence-transformers
- **Model**: Use `all-MiniLM-L6-v2` for local semantic embeddings
- **Features**:
  - Semantic similarity search (understanding meaning, not just keywords)
  - Hybrid search combining keyword and semantic matching
  - Configurable similarity thresholds
  - Support for multiple embedding models
- **Implementation**:
  - Add `sentence-transformers` dependency
  - Create semantic index alongside keyword index
  - Implement semantic search in searcher module
  - Add CLI options for semantic vs keyword search

#### Additional Enhancements
- **Fuzzy Search**: Add fuzzy matching for typos and variations
- **Advanced Filtering**: Filter by file type, date, size
- **Search History**: Remember and suggest previous searches
- **GUI Interface**: Web-based or desktop GUI
- **Real-time Indexing**: Watch directories for changes
- **Cloud Storage**: Support for Google Drive, Dropbox, etc.

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for the command-line interface
- Uses [PyPDF2](https://pypdf2.readthedocs.io/) for PDF processing
- Inspired by modern search engine architectures
- Thanks to the Python community for excellent libraries and tools

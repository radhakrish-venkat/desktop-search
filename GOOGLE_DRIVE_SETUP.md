# Google Drive Integration Setup Guide

This guide will help you set up Google Drive integration for the desktop search application.

## Prerequisites

1. A Google account with Google Drive
2. Python 3.7 or higher
3. Basic familiarity with Google Cloud Console

## Step 1: Install Dependencies

First, install the required Google Drive API dependencies:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

Or install all dependencies including Google Drive:

```bash
pip install -r requirements.txt
```

## Step 2: Create Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click on it and press "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. In the Google Cloud Console, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required fields (app name, user support email, developer contact)
   - Add your email as a test user
4. For the OAuth 2.0 Client ID:
   - Choose "Desktop application" as the application type
   - Give it a name (e.g., "Desktop Search")
   - Click "Create"
5. Download the credentials JSON file (it will be named something like `client_secret_123456789-abcdefghijklmnop.apps.googleusercontent.com.json`)

## Step 4: Setup in Desktop Search

Copy your credentials file to the application:

```bash
python main.py setup-gdrive /path/to/your/credentials.json
```

This will:
- Copy the credentials to `~/.config/desktop-search/credentials.json`
- Create the necessary directory structure
- Prepare the application for Google Drive authentication

## Step 5: First Authentication

When you first run a Google Drive command, the application will:

1. Open a browser window for OAuth authentication
2. Ask you to sign in to your Google account
3. Show a warning that the app is not verified (this is normal for development)
4. Click "Advanced" > "Go to Desktop Search (unsafe)" to proceed
5. Grant permission to access your Google Drive files
6. Save the authentication token for future use

**Note**: The application only requests read-only access to your Google Drive files.

## Step 6: Test the Integration

Test that everything is working:

```bash
# List files in your Google Drive root
python main.py gdrive-index --no-save

# Search for a specific term
python main.py gdrive-search "test"
```

## Usage Examples

### Index Google Drive Files

```bash
# Index all files in root folder
python main.py gdrive-index

# Index specific folder (replace with your folder ID)
python main.py gdrive-index --folder-id "1ABC123DEF456"

# Index only PDF files
python main.py gdrive-index --query "mimeType contains 'pdf'"

# Index files modified in last 30 days
python main.py gdrive-index --query "modifiedTime > '2024-01-01T00:00:00'"

# Save to custom location
python main.py gdrive-index --save my_gdrive_index.pkl
```

### Search Google Drive

```bash
# Search all Google Drive files
python main.py gdrive-search "your query"

# Search in specific folder
python main.py gdrive-search "your query" --folder-id "1ABC123DEF456"

# Limit results
python main.py gdrive-search "your query" --limit 5
```

### Hybrid Indexing (Local + Google Drive)

```bash
# Index both local and Google Drive files
python main.py hybrid-index /path/to/local/documents --gdrive-folder-id "1ABC123DEF456"

# With additional filters
python main.py hybrid-index /path/to/local/documents \
  --gdrive-folder-id "1ABC123DEF456" \
  --gdrive-query "mimeType contains 'document'"
```

### Hybrid Semantic Indexing (Local + Google Drive with ChromaDB)

```bash
# Build semantic index for both local and Google Drive files
python main.py hybrid-semantic-index /path/to/local/documents --gdrive-folder-id "1ABC123DEF456"

# With custom model and database path
python main.py hybrid-semantic-index /path/to/local/documents \
  --gdrive-folder-id "1ABC123DEF456" \
  --model all-mpnet-base-v2 \
  --db-path ./hybrid_chroma_db

# Without clearing existing index
python main.py hybrid-semantic-index /path/to/local/documents \
  --gdrive-folder-id "1ABC123DEF456" \
  --no-clear
```

### Hybrid Semantic Search

```bash
# Semantic search across local and Google Drive files
python main.py hybrid-semantic-search "machine learning algorithms"

# Hybrid search (semantic + keyword)
python main.py hybrid-semantic-search "data analysis techniques" --hybrid

# With custom threshold and limit
python main.py hybrid-semantic-search "project proposal" --threshold 0.5 --limit 20

# Get statistics about the hybrid semantic index
python main.py hybrid-semantic-stats
```

## Finding Folder IDs

To find a Google Drive folder ID:

1. Open Google Drive in your browser
2. Navigate to the folder you want to index
3. The folder ID is in the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
4. Copy the folder ID (the long string after `/folders/`)

## Troubleshooting

### "Google Drive API dependencies not available"

Make sure you've installed the required packages:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### "Credentials file not found"

Ensure you've run the setup command with the correct path:

```bash
python main.py setup-gdrive /full/path/to/credentials.json
```

### "OAuth consent screen not configured"

1. Go to Google Cloud Console > "APIs & Services" > "OAuth consent screen"
2. Configure the consent screen with required information
3. Add your email as a test user

### "App not verified" warning

This is normal for development. Click "Advanced" > "Go to [App Name] (unsafe)" to proceed.

### Authentication errors

If you encounter authentication issues:

1. Delete the token file: `rm ~/.config/desktop-search/token.json`
2. Re-run the Google Drive command to re-authenticate

### Rate limiting

Google Drive API has rate limits. If you encounter rate limiting:

1. Wait a few minutes before retrying
2. Consider indexing smaller folders or using more specific queries
3. Use the `--no-save` flag to avoid repeated indexing

## Security Notes

- The application only requests read-only access to your Google Drive
- Credentials are stored locally in `~/.config/desktop-search/`
- Authentication tokens are automatically refreshed
- No data is sent to external servers (except Google Drive API)

## Supported File Types

The Google Drive integration supports:

- **Google Docs** - Full text extraction
- **Google Sheets** - CSV export for text content
- **Google Slides** - Text export
- **PDF files** - Full text extraction
- **Microsoft Office files** (Word, Excel, PowerPoint) - Full text extraction
- **Text files** - Direct text access

## Advanced Usage

### Query Filters

You can use Google Drive query filters to limit which files are indexed:

```bash
# Only PDF files
--query "mimeType contains 'pdf'"

# Files modified after a date
--query "modifiedTime > '2024-01-01T00:00:00'"

# Files with specific name pattern
--query "name contains 'report'"

# Combine filters
--query "mimeType contains 'pdf' and modifiedTime > '2024-01-01T00:00:00'"
```

### Folder Permissions

Make sure the Google account has access to the folders you want to index. Shared folders will only be accessible if you have at least "Viewer" permissions.

## Support

If you encounter issues:

1. Check that all dependencies are installed
2. Verify your Google Cloud project has the Drive API enabled
3. Ensure your OAuth credentials are correctly configured
4. Check that you have permission to access the Google Drive folders
5. Review the troubleshooting section above

For additional help, check the main README.md file or create an issue in the project repository. 

## ✅ **Google Drive Semantic Search Integration Complete!**

### **Answer to Your Question:**

**Yes, semantic search is now fully supported on Google Drive and it's integrated with ChromaDB!** 

I've implemented a comprehensive hybrid semantic search system that combines local files and Google Drive files in a unified ChromaDB vector database.

### **What I've Added:**

#### **1. Hybrid Semantic Indexer** (`pkg/indexer/semantic_hybrid.py`)
- **Unified ChromaDB Collection**: Both local and Google Drive files are stored in the same vector database
- **Smart Chunking**: Documents are split into overlapping chunks for better semantic matching
- **Source Tracking**: Each chunk is tagged with its source (`local` or `google_drive`)
- **Metadata Preservation**: File paths, names, types, and other metadata are preserved
- **Sentence Transformer Models**: Uses the same embedding models as the original semantic search

#### **2. New CLI Commands:**
- **`hybrid-semantic-index`**: Build semantic index for both local and Google Drive files
- **`hybrid-semantic-search`**: Search across both sources using semantic similarity
- **`hybrid-semantic-stats`**: Get statistics about the hybrid index

#### **3. Advanced Features:**
- **Hybrid Search**: Combines semantic similarity with keyword matching
- **Configurable Thresholds**: Adjustable similarity thresholds
- **Model Selection**: Support for different sentence transformer models
- **Incremental Indexing**: Option to add to existing index without clearing

### **How It Works:**

1. **Indexing Process**:
   - Local files are processed using existing parsers
   - Google Drive files are fetched and processed via Google Drive API
   - Both are chunked into overlapping segments
   - All chunks are embedded using sentence transformers
   - Everything is stored in a unified ChromaDB collection

2. **Search Process**:
   - Query is embedded using the same model
   - ChromaDB performs similarity search across all chunks
   - Results are ranked by similarity score
   - Source information is preserved in results

3. **Result Display**:
   - Local files shown with 📁 icon
   - Google Drive files shown with ☁️ icon
   - Similarity scores and chunk information displayed
   - Snippets show relevant text portions

### **Usage Examples:**

```bash
# Build hybrid semantic index
python main.py hybrid-semantic-index ~/Documents --gdrive-folder-id "1ABC123DEF456"

# Semantic search across both sources
python main.py hybrid-semantic-search "artificial intelligence research"

# Hybrid search (semantic + keyword)
python main.py hybrid-semantic-search "data analysis techniques" --hybrid

# Get statistics
python main.py hybrid-semantic-stats
```

### **Key Benefits:**

1. **Unified Search Experience**: Search across local and cloud files seamlessly
2. **Semantic Understanding**: Finds related content even without exact keyword matches
3. **ChromaDB Integration**: Leverages the same powerful vector database
4. **Source Transparency**: Clear indication of where each result comes from
5. **Performance**: Efficient vector similarity search
6. **Flexibility**: Configurable models, thresholds, and search types

### **Technical Architecture:**

```
<code_block_to_apply_from>
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Local Files   │    │  Google Drive   │    │   ChromaDB      │
│                 │    │                 │    │                 │
│ • PDF, DOCX     │    │ • Google Docs   │    │ • Vector Store  │
│ • TXT, etc.     │    │ • Sheets, etc.  │    │ • Embeddings    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Hybrid Semantic │
                    │    Indexer      │
                    │                 │
                    │ • Chunking      │
                    │ • Embedding     │
                    │ • Storage       │
                    └─────────────────┘
```

The implementation is fully backward compatible and gracefully handles cases where Google Drive dependencies aren't installed. The semantic search now works seamlessly across both local and Google Drive files, providing a unified search experience with the power of ChromaDB's vector similarity search. 
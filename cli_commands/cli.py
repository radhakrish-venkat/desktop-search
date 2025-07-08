import click
import os
from typing import Optional, Dict, Any

# Import the core logic functions from your pkg directory
from pkg.indexer.core import build_index, save_index, load_index
from pkg.searcher.core import search_index
from pkg.indexer.semantic import SemanticIndexer
from pkg.indexer.google_drive import build_google_drive_index, merge_indices, search_google_drive
from pkg.utils.google_drive import setup_google_drive_credentials, GOOGLE_DRIVE_AVAILABLE
from pkg.indexer.semantic_hybrid import HybridSemanticIndexer
from pkg.indexer.incremental import incremental_index, incremental_semantic_index

# --- Main Click Group ---
@click.group()
@click.version_option(version='0.1.0', prog_name='desktop-search')
def cli():
    """
    A simple local document search tool.
    """
    pass

def get_default_index_path(directory: str) -> str:
    """Get the default index file path for a directory."""
    return os.path.join(directory, 'index.pkl')

# --- Index Command ---
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--save', '-s', 'save_path', type=click.Path(dir_okay=False), help='Save index to specified file (overrides default)')
@click.option('--no-save', is_flag=True, help='Do not save index to file (only keep in memory)')
def index(directory: str, save_path: Optional[str], no_save: bool):
    """
    Scans the specified DIRECTORY, extracts text from supported documents,
    and builds a search index.
    
    By default, saves the index to DIRECTORY/index.pkl
    """
    click.echo(f"Starting indexing of directory: {directory}")
    
    try:
        index_data = build_index(directory)
        if not index_data:
            click.echo("Error: Failed to build index.", err=True)
            raise click.Abort()
        
        doc_count = len(index_data['document_store'])
        click.echo(f"Indexing complete. Indexed {doc_count} documents.")
        
        # Determine where to save the index
        if not no_save:
            if save_path:
                # Use user-specified path
                target_path = save_path
            else:
                # Use default path in .index folder
                target_path = get_default_index_path(directory)
            
            if save_index(index_data, target_path):
                click.echo(f"Index saved to: {target_path}")
            else:
                click.echo("Warning: Failed to save index.", err=True)
        else:
            click.echo("Index not saved to file (--no-save flag used)")
        
        # Store in context for immediate search
        click.get_current_context().obj = index_data
        
    except click.Abort:
        raise
    except Exception as e:
        click.echo(f"Error during indexing: {e}", err=True)
        raise click.Abort()

# --- Search Command ---
@cli.command()
@click.argument('query')
@click.option('--load', '-l', 'load_path', type=click.Path(exists=True), help='Load index from specified file')
@click.option('--directory', '-d', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True), help='Directory to search (loads default index from directory/.index/index.pkl)')
@click.option('--limit', '-n', default=10, help='Maximum number of results to show')
def search(query: str, load_path: Optional[str], directory: Optional[str], limit: int):
    """
    Searches the indexed documents for the given QUERY.
    
    If no --load option is provided, tries to load from:
    1. The default index file (DIRECTORY/index.pkl) if --directory is specified
    2. The index in memory from a previous 'index' command
    """
    click.echo(f"Searching for: '{query}'")
    
    # Try to load index from file first, then from context
    index_data: Optional[Dict[str, Any]] = None
    
    if load_path:
        # Load from user-specified path
        index_data = load_index(load_path)
        if not index_data:
            click.echo(f"Error: Could not load index from {load_path}", err=True)
            raise click.Abort()
    elif directory:
        # Load from default location in the specified directory
        default_index_path = get_default_index_path(directory)
        index_data = load_index(default_index_path)
        if not index_data:
            click.echo(f"Error: Could not load index from {default_index_path}", err=True)
            click.echo(f"Try running 'python main.py index {directory}' first", err=True)
            raise click.Abort()
    else:
        # Try to get from context (from previous index command)
        index_data = click.get_current_context().obj
    
    if not index_data:
        click.echo("Error: No index found. Please run 'index' command first or use --load/--directory option.", err=True)
        raise click.Abort()

    try:
        results = search_index(query, index_data)
        
        if results:
            click.echo(f"\n--- Search Results ({len(results)} found) ---")
            for i, result in enumerate(results[:limit], 1):
                click.echo(f"{i}. File: {result.get('filepath', 'N/A')}")
                click.echo(f"   Snippet: {result.get('snippet', 'No snippet available')}")
                click.echo("-" * 40)
            
            if len(results) > limit:
                click.echo(f"... and {len(results) - limit} more results")
        else:
            click.echo("No matching documents found.")
            
    except Exception as e:
        click.echo(f"Error during search: {e}", err=True)
        raise click.Abort()

# --- Semantic Index Command ---
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--db-path', '-p', default='./chroma_db', help='ChromaDB persistence directory')
@click.option('--model', '-m', default='all-MiniLM-L6-v2', help='Sentence transformer model name')
def semantic_index(directory: str, db_path: str, model: str):
    """
    Builds a semantic search index using ChromaDB and sentence-transformers.
    
    This creates embeddings for document chunks and stores them in a vector database
    for semantic similarity search.
    """
    click.echo(f"Starting semantic indexing of directory: {directory}")
    click.echo(f"Using model: {model}")
    click.echo(f"ChromaDB path: {db_path}")
    
    try:
        indexer = SemanticIndexer(persist_directory=db_path, model_name=model)
        stats = indexer.build_semantic_index(directory)
        
        if not stats:
            click.echo("Error: Failed to build semantic index.", err=True)
            raise click.Abort()
        
        click.echo(f"Semantic indexing complete!")
        click.echo(f"Files processed: {stats['stats']['total_files']}")
        click.echo(f"Chunks created: {stats['stats']['total_chunks']}")
        click.echo(f"Files skipped: {stats['stats']['skipped_files']}")
        
        # Store indexer in context for immediate search
        click.get_current_context().obj = {'semantic_indexer': indexer}
        
    except Exception as e:
        click.echo(f"Error during semantic indexing: {e}", err=True)
        raise click.Abort()

# --- Semantic Search Command ---
@cli.command()
@click.argument('query')
@click.option('--db-path', '-p', default='./chroma_db', help='ChromaDB persistence directory')
@click.option('--limit', '-n', default=10, help='Maximum number of results to show')
@click.option('--threshold', '-t', default=0.3, help='Similarity threshold (0-1)')
@click.option('--hybrid', is_flag=True, help='Use hybrid search (combines semantic and keyword matching)')
def semantic_search(query: str, db_path: str, limit: int, threshold: float, hybrid: bool):
    """
    Performs semantic search on the indexed documents.
    
    Uses sentence embeddings to find semantically similar content,
    even if the exact keywords don't match.
    """
    click.echo(f"Performing semantic search for: '{query}'")
    click.echo(f"ChromaDB path: {db_path}")
    
    try:
        # Try to get indexer from context first
        context_obj = click.get_current_context().obj
        if context_obj and 'semantic_indexer' in context_obj:
            indexer = context_obj['semantic_indexer']
        else:
            # Create new indexer instance
            indexer = SemanticIndexer(persist_directory=db_path)
        
        # Perform search
        if hybrid:
            click.echo("Using hybrid search (semantic + keyword matching)...")
            results = indexer.hybrid_search(query, n_results=limit)
        else:
            click.echo("Using semantic search...")
            results = indexer.semantic_search(query, n_results=limit, threshold=threshold)
        
        if results:
            click.echo(f"\n--- Semantic Search Results ({len(results)} found) ---")
            for i, result in enumerate(results, 1):
                click.echo(f"{i}. File: {result['filename']}")
                click.echo(f"   Path: {result['filepath']}")
                click.echo(f"   Chunk: {result['chunk_index'] + 1}/{result['total_chunks']}")
                
                if 'similarity' in result:
                    click.echo(f"   Similarity: {result['similarity']:.3f}")
                if 'combined_score' in result:
                    click.echo(f"   Combined Score: {result['combined_score']:.3f}")
                
                # Show snippet (truncated)
                snippet = result['snippet'][:200] + "..." if len(result['snippet']) > 200 else result['snippet']
                click.echo(f"   Snippet: {snippet}")
                click.echo("-" * 50)
            
            if len(results) > limit:
                click.echo(f"... and {len(results) - limit} more results")
        else:
            click.echo("No semantically similar documents found.")
            
    except Exception as e:
        click.echo(f"Error during semantic search: {e}", err=True)
        raise click.Abort()

# --- Semantic Stats Command ---
@cli.command()
@click.option('--db-path', '-p', default='./chroma_db', help='ChromaDB persistence directory')
def semantic_stats(db_path: str):
    """
    Shows statistics about the semantic index.
    """
    click.echo(f"Getting semantic index statistics from: {db_path}")
    
    try:
        indexer = SemanticIndexer(persist_directory=db_path)
        stats = indexer.get_collection_stats()
        
        if stats:
            click.echo(f"\n--- Semantic Index Statistics ---")
            click.echo(f"Total chunks: {stats['total_chunks']}")
            click.echo(f"Model: {stats['model_name']}")
            click.echo(f"Database path: {stats['persist_directory']}")
        else:
            click.echo("No semantic index found or error retrieving stats.")
            
    except Exception as e:
        click.echo(f"Error getting semantic stats: {e}", err=True)
        raise click.Abort()

# --- Google Drive Setup Command ---
@cli.command()
@click.argument('credentials_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
def setup_gdrive(credentials_path: str):
    """
    Set up Google Drive credentials for the application.
    
    CREDENTIALS_PATH should be the path to your credentials.json file
    downloaded from Google Cloud Console.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        click.echo("Error: Google Drive API dependencies not available.", err=True)
        click.echo("Please install: google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client", err=True)
        raise click.Abort()
    
    click.echo(f"Setting up Google Drive credentials from: {credentials_path}")
    
    try:
        if setup_google_drive_credentials(credentials_path):
            click.echo("Google Drive credentials set up successfully!")
            click.echo("You can now use Google Drive indexing and search commands.")
        else:
            click.echo("Error: Failed to set up Google Drive credentials.", err=True)
            raise click.Abort()
    except Exception as e:
        click.echo(f"Error during setup: {e}", err=True)
        raise click.Abort()

# --- Google Drive Index Command ---
@cli.command()
@click.option('--folder-id', '-f', help='Google Drive folder ID to index (default: root folder)')
@click.option('--query', '-q', help='Additional query to filter files (e.g., "mimeType contains \'pdf\'")')
@click.option('--save', '-s', 'save_path', type=click.Path(dir_okay=False), help='Save index to specified file')
@click.option('--no-save', is_flag=True, help='Do not save index to file (only keep in memory)')
def gdrive_index(folder_id: Optional[str], query: Optional[str], save_path: Optional[str], no_save: bool):
    """
    Indexes files from Google Drive and builds a search index.
    
    Requires Google Drive credentials to be set up first using 'setup-gdrive' command.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        click.echo("Error: Google Drive API dependencies not available.", err=True)
        click.echo("Please install: google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client", err=True)
        raise click.Abort()
    
    click.echo(f"Starting Google Drive indexing (folder_id: {folder_id or 'root'})")
    if query:
        click.echo(f"Using query filter: {query}")
    
    try:
        index_data = build_google_drive_index(folder_id=folder_id, query=query)
        if not index_data:
            click.echo("Error: Failed to build Google Drive index.", err=True)
            raise click.Abort()
        
        doc_count = len(index_data['document_store'])
        click.echo(f"Google Drive indexing complete. Indexed {doc_count} documents.")
        
        # Determine where to save the index
        if not no_save:
            if save_path:
                target_path = save_path
            else:
                # Use default path
                target_path = f"gdrive_index_{folder_id or 'root'}.pkl"
            
            if save_index(index_data, target_path):
                click.echo(f"Index saved to: {target_path}")
            else:
                click.echo("Warning: Failed to save index.", err=True)
        else:
            click.echo("Index not saved to file (--no-save flag used)")
        
        # Store in context for immediate search
        click.get_current_context().obj = index_data
        
    except click.Abort:
        raise
    except Exception as e:
        click.echo(f"Error during Google Drive indexing: {e}", err=True)
        raise click.Abort()

# --- Hybrid Index Command ---
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--gdrive-folder-id', '-g', help='Google Drive folder ID to include')
@click.option('--gdrive-query', '-q', help='Additional query to filter Google Drive files')
@click.option('--save', '-s', 'save_path', type=click.Path(dir_okay=False), help='Save index to specified file')
@click.option('--no-save', is_flag=True, help='Do not save index to file (only keep in memory)')
def hybrid_index(directory: str, gdrive_folder_id: Optional[str], gdrive_query: Optional[str], save_path: Optional[str], no_save: bool):
    """
    Builds a hybrid index combining local files and Google Drive files.
    
    This command indexes both local files from DIRECTORY and Google Drive files,
    then merges them into a single searchable index.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        click.echo("Error: Google Drive API dependencies not available.", err=True)
        click.echo("Please install: google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client", err=True)
        raise click.Abort()
    
    click.echo(f"Starting hybrid indexing of local directory: {directory}")
    if gdrive_folder_id:
        click.echo(f"Including Google Drive folder: {gdrive_folder_id}")
    
    try:
        # Build local index
        click.echo("Building local file index...")
        local_index = build_index(directory)
        if not local_index:
            click.echo("Error: Failed to build local index.", err=True)
            raise click.Abort()
        
        # Build Google Drive index
        gdrive_index = None
        if gdrive_folder_id or gdrive_query:
            click.echo("Building Google Drive index...")
            gdrive_index = build_google_drive_index(folder_id=gdrive_folder_id, query=gdrive_query)
            if not gdrive_index:
                click.echo("Warning: Failed to build Google Drive index, continuing with local index only.", err=True)
        
        # Merge indices
        if gdrive_index:
            click.echo("Merging local and Google Drive indices...")
            merged_index = merge_indices(local_index, gdrive_index)
        else:
            merged_index = local_index
        
        # Display stats
        stats = merged_index['stats']
        click.echo(f"Hybrid indexing complete!")
        click.echo(f"Local files: {stats.get('local_files', stats.get('total_files', 0))}")
        if gdrive_index:
            click.echo(f"Google Drive files: {stats.get('gdrive_files', 0)}")
        click.echo(f"Total documents: {stats['total_documents']}")
        
        # Determine where to save the index
        if not no_save:
            if save_path:
                target_path = save_path
            else:
                # Use default path
                target_path = get_default_index_path(directory)
            
            if save_index(merged_index, target_path):
                click.echo(f"Index saved to: {target_path}")
            else:
                click.echo("Warning: Failed to save index.", err=True)
        else:
            click.echo("Index not saved to file (--no-save flag used)")
        
        # Store in context for immediate search
        click.get_current_context().obj = merged_index
        
    except click.Abort:
        raise
    except Exception as e:
        click.echo(f"Error during hybrid indexing: {e}", err=True)
        raise click.Abort()

# --- Google Drive Search Command ---
@cli.command()
@click.argument('query')
@click.option('--folder-id', '-f', help='Google Drive folder ID to search in (default: all folders)')
@click.option('--limit', '-n', default=10, help='Maximum number of results to show')
def gdrive_search(query: str, folder_id: Optional[str], limit: int):
    """
    Searches Google Drive files directly using Google Drive API.
    
    This performs a real-time search on Google Drive without requiring
    a pre-built index.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        click.echo("Error: Google Drive API dependencies not available.", err=True)
        click.echo("Please install: google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client", err=True)
        raise click.Abort()
    
    click.echo(f"Searching Google Drive for: '{query}'")
    if folder_id:
        click.echo(f"Searching in folder: {folder_id}")
    
    try:
        results = search_google_drive(query, folder_id=folder_id, limit=limit)
        
        if results:
            click.echo(f"\n--- Google Drive Search Results ({len(results)} found) ---")
            for i, result in enumerate(results, 1):
                click.echo(f"{i}. File: {result.get('filename', 'N/A')}")
                click.echo(f"   Type: {result.get('mime_type', 'N/A')}")
                click.echo(f"   Snippet: {result.get('snippet', 'No snippet available')}")
                click.echo("-" * 40)
        else:
            click.echo("No matching Google Drive files found.")
            
    except Exception as e:
        click.echo(f"Error during Google Drive search: {e}", err=True)
        raise click.Abort()

# --- Hybrid Semantic Index Command ---
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--gdrive-folder-id', '-g', help='Google Drive folder ID to include')
@click.option('--gdrive-query', '-q', help='Additional query to filter Google Drive files')
@click.option('--db-path', '-p', default='./chroma_db', help='ChromaDB persistence directory')
@click.option('--model', '-m', default='all-MiniLM-L6-v2', help='Sentence transformer model name')
@click.option('--no-clear', is_flag=True, help='Do not clear existing index before building')
def hybrid_semantic_index(directory: str, gdrive_folder_id: Optional[str], gdrive_query: Optional[str], db_path: str, model: str, no_clear: bool):
    """
    Builds a hybrid semantic search index combining local files and Google Drive files.
    
    This creates embeddings for document chunks from both local and Google Drive files
    and stores them in a vector database for semantic similarity search.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        click.echo("Error: Google Drive API dependencies not available.", err=True)
        click.echo("Please install: google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client", err=True)
        raise click.Abort()
    
    click.echo(f"Starting hybrid semantic indexing of local directory: {directory}")
    if gdrive_folder_id:
        click.echo(f"Including Google Drive folder: {gdrive_folder_id}")
    click.echo(f"Using model: {model}")
    click.echo(f"ChromaDB path: {db_path}")
    
    try:
        indexer = HybridSemanticIndexer(persist_directory=db_path, model_name=model)
        stats = indexer.build_hybrid_semantic_index(
            local_directory=directory,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_query=gdrive_query,
            clear_existing=not no_clear
        )
        
        if not stats:
            click.echo("Error: Failed to build hybrid semantic index.", err=True)
            raise click.Abort()
        
        click.echo(f"Hybrid semantic indexing complete!")
        click.echo(f"Total files processed: {stats['stats']['total_files']}")
        click.echo(f"Total chunks created: {stats['stats']['total_chunks']}")
        click.echo(f"Files skipped: {stats['stats']['skipped_files']}")
        
        # Store indexer in context for immediate search
        click.get_current_context().obj = {'hybrid_semantic_indexer': indexer}
        
    except Exception as e:
        click.echo(f"Error during hybrid semantic indexing: {e}", err=True)
        raise click.Abort()

# --- Hybrid Semantic Search Command ---
@cli.command()
@click.argument('query')
@click.option('--db-path', '-p', default='./chroma_db', help='ChromaDB persistence directory')
@click.option('--limit', '-n', default=10, help='Maximum number of results to show')
@click.option('--threshold', '-t', default=0.3, help='Similarity threshold (0-1)')
@click.option('--hybrid', is_flag=True, help='Use hybrid search (combines semantic and keyword matching)')
def hybrid_semantic_search(query: str, db_path: str, limit: int, threshold: float, hybrid: bool):
    """
    Performs semantic search on the hybrid index (local + Google Drive files).
    
    Uses sentence embeddings to find semantically similar content from both
    local files and Google Drive files.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        click.echo("Error: Google Drive API dependencies not available.", err=True)
        click.echo("Please install: google-auth, google-auth-oauthlib, google-auth-httplib2, google-api-python-client", err=True)
        raise click.Abort()
    
    click.echo(f"Performing hybrid semantic search for: '{query}'")
    click.echo(f"ChromaDB path: {db_path}")
    
    try:
        # Try to get indexer from context first
        context_obj = click.get_current_context().obj
        if context_obj and 'hybrid_semantic_indexer' in context_obj:
            indexer = context_obj['hybrid_semantic_indexer']
        else:
            # Create new indexer instance
            indexer = HybridSemanticIndexer(persist_directory=db_path)
        
        # Perform search
        if hybrid:
            click.echo("Using hybrid search (semantic + keyword matching)...")
            results = indexer.hybrid_search(query, n_results=limit)
        else:
            click.echo("Using semantic search...")
            results = indexer.semantic_search(query, n_results=limit, threshold=threshold)
        
        if results:
            click.echo(f"\n--- Hybrid Semantic Search Results ({len(results)} found) ---")
            for i, result in enumerate(results, 1):
                source_icon = "📁" if result.get('source') == 'local' else "☁️"
                click.echo(f"{i}. {source_icon} {result.get('filename', 'N/A')}")
                click.echo(f"   Path: {result.get('filepath', 'N/A')}")
                click.echo(f"   Chunk: {result.get('chunk_index', 0) + 1}/{result.get('total_chunks', 1)}")
                
                if 'similarity' in result:
                    click.echo(f"   Similarity: {result['similarity']:.3f}")
                if 'combined_score' in result:
                    click.echo(f"   Combined Score: {result['combined_score']:.3f}")
                
                # Show snippet (truncated)
                snippet = result['snippet'][:200] + "..." if len(result['snippet']) > 200 else result['snippet']
                click.echo(f"   Snippet: {snippet}")
                click.echo("-" * 50)
            
            if len(results) > limit:
                click.echo(f"... and {len(results) - limit} more results")
        else:
            click.echo("No semantically similar documents found.")
            
    except Exception as e:
        click.echo(f"Error during hybrid semantic search: {e}", err=True)
        raise click.Abort()

# --- Hybrid Semantic Stats Command ---
@cli.command()
@click.option('--db-path', '-p', default='./chroma_db', help='ChromaDB persistence directory')
def hybrid_semantic_stats(db_path: str):
    """
    Shows statistics about the hybrid semantic index.
    """
    click.echo(f"Getting hybrid semantic index statistics from: {db_path}")
    
    try:
        indexer = HybridSemanticIndexer(persist_directory=db_path)
        stats = indexer.get_collection_stats()
        
        if stats:
            click.echo(f"\n--- Hybrid Semantic Index Statistics ---")
            click.echo(f"Total documents: {stats.get('total_documents', 0)}")
            click.echo(f"Total chunks: {stats.get('total_chunks', 0)}")
            click.echo(f"Local files: {stats.get('local_files', 0)}")
            click.echo(f"Google Drive files: {stats.get('gdrive_files', 0)}")
            click.echo(f"Model used: {stats.get('model_name', 'Unknown')}")
            click.echo(f"ChromaDB path: {db_path}")
        else:
            click.echo("No statistics available. Index may be empty or not found.")
            
    except Exception as e:
        click.echo(f"Error getting statistics: {e}", err=True)
        raise click.Abort()

# --- Incremental Index Command ---
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True), required=False)
@click.option('--gdrive-folder-id', '-g', help='Google Drive folder ID to index')
@click.option('--gdrive-query', '-q', help='Additional query to filter Google Drive files')
@click.option('--save', '-s', 'save_path', type=click.Path(dir_okay=False), help='Save index to specified file')
@click.option('--metadata-path', '-m', default='./index_metadata.json', help='Path to store file metadata for change detection')
def incremental_index_cmd(directory: Optional[str], gdrive_folder_id: Optional[str], gdrive_query: Optional[str], save_path: Optional[str], metadata_path: str):
    """
    Performs incremental indexing of local and Google Drive files.
    
    Only indexes new or modified files by tracking file changes.
    Much faster than full re-indexing for large collections.
    
    Requires at least one of: DIRECTORY or --gdrive-folder-id
    """
    if not directory and not gdrive_folder_id and not gdrive_query:
        click.echo("Error: Must specify either DIRECTORY or --gdrive-folder-id", err=True)
        raise click.Abort()
    
    click.echo("Starting incremental indexing...")
    click.echo(f"Metadata tracking file: {metadata_path}")
    
    if directory:
        click.echo(f"Local directory: {directory}")
    if gdrive_folder_id:
        click.echo(f"Google Drive folder ID: {gdrive_folder_id}")
    if gdrive_query:
        click.echo(f"Google Drive query: {gdrive_query}")
    
    try:
        stats = incremental_index(
            directory_path=directory,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_query=gdrive_query,
            index_path=save_path
        )
        
        if not stats:
            click.echo("Error: Failed to perform incremental indexing.", err=True)
            raise click.Abort()
        
        click.echo(f"\n--- Incremental Indexing Results ---")
        click.echo(f"Total files in index: {stats['stats']['total_files']}")
        click.echo(f"New files processed: {stats['stats']['new_files']}")
        click.echo(f"Modified files processed: {stats['stats']['modified_files']}")
        click.echo(f"Deleted files removed: {stats['stats']['deleted_files']}")
        click.echo(f"Files skipped (no changes): {stats['stats']['skipped_files']}")
        
        if save_path:
            click.echo(f"Index saved to: {save_path}")
        
    except Exception as e:
        click.echo(f"Error during incremental indexing: {e}", err=True)
        raise click.Abort()

# --- Incremental Semantic Index Command ---
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True), required=False)
@click.option('--gdrive-folder-id', '-g', help='Google Drive folder ID to index')
@click.option('--gdrive-query', '-q', help='Additional query to filter Google Drive files')
@click.option('--db-path', '-p', default='./chroma_db', help='ChromaDB persistence directory')
@click.option('--model', '-m', default='all-MiniLM-L6-v2', help='Sentence transformer model name')
@click.option('--metadata-path', '-t', default='./index_metadata.json', help='Path to store file metadata for change detection')
def incremental_semantic_index_cmd(directory: Optional[str], gdrive_folder_id: Optional[str], gdrive_query: Optional[str], db_path: str, model: str, metadata_path: str):
    """
    Performs incremental semantic indexing of local and Google Drive files.
    
    Only indexes new or modified files by tracking file changes.
    Uses ChromaDB for vector storage and semantic search.
    
    Requires at least one of: DIRECTORY or --gdrive-folder-id
    """
    if not directory and not gdrive_folder_id and not gdrive_query:
        click.echo("Error: Must specify either DIRECTORY or --gdrive-folder-id", err=True)
        raise click.Abort()
    
    click.echo("Starting incremental semantic indexing...")
    click.echo(f"ChromaDB path: {db_path}")
    click.echo(f"Model: {model}")
    click.echo(f"Metadata tracking file: {metadata_path}")
    
    if directory:
        click.echo(f"Local directory: {directory}")
    if gdrive_folder_id:
        click.echo(f"Google Drive folder ID: {gdrive_folder_id}")
    if gdrive_query:
        click.echo(f"Google Drive query: {gdrive_query}")
    
    try:
        stats = incremental_semantic_index(
            directory_path=directory,
            gdrive_folder_id=gdrive_folder_id,
            gdrive_query=gdrive_query,
            persist_directory=db_path,
            model_name=model
        )
        
        if not stats:
            click.echo("Error: Failed to perform incremental semantic indexing.", err=True)
            raise click.Abort()
        
        click.echo(f"\n--- Incremental Semantic Indexing Results ---")
        click.echo(f"Total files processed: {stats['stats']['total_files']}")
        click.echo(f"Total chunks created: {stats['stats']['total_chunks']}")
        click.echo(f"New files processed: {stats['stats'].get('new_files', 0)}")
        click.echo(f"Modified files processed: {stats['stats'].get('modified_files', 0)}")
        click.echo(f"Deleted files removed: {stats['stats'].get('deleted_files', 0)}")
        click.echo(f"Files skipped (no changes): {stats['stats'].get('skipped_files', 0)}")
        
    except Exception as e:
        click.echo(f"Error during incremental semantic indexing: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
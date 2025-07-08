import click
import os
from typing import Optional, Dict, Any

# Import the core logic functions from your pkg directory
from pkg.indexer.core import build_index, save_index, load_index
from pkg.searcher.core import search_index
from pkg.indexer.semantic import SemanticIndexer

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

if __name__ == '__main__':
    cli()
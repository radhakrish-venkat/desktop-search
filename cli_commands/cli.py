import click
import os
from typing import Optional

# Import the core logic functions from your pkg directory
from pkg.indexer.semantic import SemanticIndexer
from pkg.indexer.google_drive import build_google_drive_index, search_google_drive
from pkg.utils.google_drive import setup_google_drive_credentials, GOOGLE_DRIVE_AVAILABLE
from pkg.indexer.incremental import smart_semantic_index

# --- Main Click Group ---
@click.group()
@click.version_option(version='0.1.0', prog_name='desktop-search')
def cli():
    """
    A simple local document search tool with unified ChromaDB indexing.
    """
    pass

# --- Index Command ---
@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--force-full', is_flag=True, help='Force full indexing even if incremental is possible')
@click.option('--model', '-m', default='all-MiniLM-L6-v2', help='Sentence transformer model name')
def index(directory: str, force_full: bool, model: str):
    """
    Scans the specified DIRECTORY, extracts text from supported documents,
    and builds a search index in the unified ChromaDB.
    
    Smart indexing: Automatically detects if an index already exists and uses
    incremental indexing for faster updates. Use --force-full to always rebuild.
    
    All data is stored in data/chroma_db
    """
    click.echo(f"Starting smart indexing of directory: {directory}")
    click.echo(f"Using model: {model}")
    
    if force_full:
        click.echo("Force full indexing enabled - rebuilding entire index")
    
    try:
        # Use smart semantic indexing that automatically chooses incremental or full
        stats = smart_semantic_index(
            directory_path=directory,
            persist_directory='data/chroma_db',
            model_name=model,
            force_full=force_full
        )
        
        if not stats:
            click.echo("Error: Failed to build index.", err=True)
            raise click.Abort()
        
        stats_data = stats.get('stats', {})
        indexing_type = stats_data.get('indexing_type', 'unknown')
        
        click.echo(f"Indexing complete ({indexing_type}).")
        click.echo(f"Total files: {stats_data.get('total_files', 0)}")
        click.echo(f"Chunks created: {stats_data.get('total_chunks', 0)}")
        
        if indexing_type == 'incremental':
            click.echo(f"New files: {stats_data.get('new_files', 0)}")
            click.echo(f"Modified files: {stats_data.get('modified_files', 0)}")
            click.echo(f"Deleted files: {stats_data.get('deleted_files', 0)}")
            click.echo(f"Skipped files: {stats_data.get('skipped_files', 0)}")
        
        click.echo("Index saved to: data/chroma_db")
        
        # Store indexer in context for immediate search
        indexer = SemanticIndexer(persist_directory='data/chroma_db', model_name=model)
        click.get_current_context().obj = {'semantic_indexer': indexer}
        
    except click.Abort:
        raise
    except Exception as e:
        click.echo(f"Error during indexing: {e}", err=True)
        raise click.Abort()

# --- API Key Management Commands ---
@cli.group()
def auth():
    """API key management commands"""
    pass

@auth.command()
@click.option('--name', '-n', required=True, help='Name for the API key')
@click.option('--description', '-d', help='Description of the API key')
@click.option('--expires-days', '-e', type=int, help='Days until expiration (1-365)')
@click.option('--permissions', '-p', multiple=True, default=['read', 'search'], help='Permissions for the key')
@click.option('--admin-key', '-a', help='Admin key for authentication')
@click.option('--api-url', default='http://localhost:8443', help='API base URL (use https:// for secure connections, or leave empty for auto-detection)')
def create_key(name: str, description: str, expires_days: int, permissions: tuple, admin_key: str, api_url: str):
    """Create a new API key"""
    import requests
    import json
    
    try:
        url = f"{api_url}/api/v1/auth/create-key"
        data = {
            "name": name,
            "description": description,
            "expires_days": expires_days,
            "permissions": list(permissions)
        }
        headers = {"X-Admin-Key": admin_key} if admin_key else {}
        response = requests.post(url, json=data, headers=headers, verify=False)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            click.echo("✅ API key created successfully!")
            click.echo(f"🔑 API Key: {result['data']['api_key']}")
            click.echo(f"📝 Name: {result['data']['key_info']['name']}")
            click.echo(f"📅 Created: {result['data']['key_info']['created_at']}")
            if result['data']['key_info']['expires_at']:
                click.echo(f"⏰ Expires: {result['data']['key_info']['expires_at']}")
            click.echo(f"🔐 Permissions: {', '.join(result['data']['key_info']['permissions'])}")
            click.echo("\n⚠️  IMPORTANT: Save this API key securely - it won't be shown again!")
        else:
            click.echo(f"❌ Failed to create API key: {result.get('message', 'Unknown error')}", err=True)
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Connection error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

@auth.command()
@click.option('--admin-key', '-a', required=True, help='Admin key for authentication')
@click.option('--api-url', default='http://localhost:8443', help='API base URL (use https:// for secure connections, or leave empty for auto-detection)')
def list_keys(admin_key: str, api_url: str):
    """List all API keys"""
    import requests
    
    try:
        url = f"{api_url}/api/v1/auth/list-keys"
        headers = {"X-Admin-Key": admin_key}
        
        response = requests.get(url, headers=headers, verify=False)
        result = response.json()
        
        if response.status_code == 200:
            keys = result.get('keys', [])
            if keys:
                click.echo("📋 API Keys:")
                for key in keys:
                    status = "✅ Active" if key['is_active'] else "❌ Inactive"
                    click.echo(f"  🔑 {key['name']} ({key['id']}) - {status}")
                    click.echo(f"     📝 {key['description'] or 'No description'}")
                    click.echo(f"     📅 Created: {key['created_at']}")
                    if key['expires_at']:
                        click.echo(f"     ⏰ Expires: {key['expires_at']}")
                    click.echo(f"     🔐 Permissions: {', '.join(key['permissions'])}")
                    click.echo()
            else:
                click.echo("📭 No API keys found")
        else:
            click.echo(f"❌ Failed to list keys: {result.get('message', 'Unknown error')}", err=True)
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Connection error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

@auth.command()
@click.argument('key_id')
@click.option('--admin-key', '-a', required=True, help='Admin key for authentication')
@click.option('--api-url', default='http://localhost:8443', help='API base URL (use https:// for secure connections, or leave empty for auto-detection)')
def revoke_key(key_id: str, admin_key: str, api_url: str):
    """Revoke an API key"""
    import requests
    
    try:
        url = f"{api_url}/api/v1/auth/revoke-key/{key_id}"
        headers = {"X-Admin-Key": admin_key}
        
        response = requests.delete(url, headers=headers, verify=False)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            click.echo(f"✅ {result['message']}")
        else:
            click.echo(f"❌ Failed to revoke key: {result.get('message', 'Unknown error')}", err=True)
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Connection error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

@auth.command()
@click.argument('api_key')
@click.option('--api-url', default='http://localhost:8443', help='API base URL (use https:// for secure connections, or leave empty for auto-detection)')
def validate_key(api_key: str, api_url: str):
    """Validate an API key"""
    import requests
    
    try:
        url = f"{api_url}/api/v1/auth/validate-key"
        data = {"api_key": api_key}
        
        response = requests.post(url, json=data, verify=False)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            key_info = result['data']['key_info']
            click.echo("✅ API key is valid!")
            click.echo(f"📝 Name: {key_info['name']}")
            click.echo(f"🔐 Permissions: {', '.join(key_info['permissions'])}")
        else:
            click.echo(f"❌ Invalid API key: {result.get('message', 'Unknown error')}", err=True)
            
    except requests.exceptions.RequestException as e:
        click.echo(f"❌ Connection error: {e}", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)

# --- Search Command ---
@cli.command()
@click.argument('query')
@click.option('--limit', '-n', default=10, help='Maximum number of results to show')
@click.option('--search-type', '-t', type=click.Choice(['keyword', 'semantic', 'hybrid']), default='semantic', help='Type of search to perform')
@click.option('--threshold', '-th', default=0.3, help='Similarity threshold (0-1) for semantic search')
def search(query: str, limit: int, search_type: str, threshold: float):
    """
    Searches the indexed documents for the given QUERY using the unified ChromaDB.
    """
    click.echo(f"Searching for: '{query}' (unified index, {search_type} search)")
    try:
        # Use the unified ChromaDB for all searches
        indexer = SemanticIndexer(
            persist_directory='data/chroma_db',
            model_name='all-MiniLM-L6-v2'
        )
        
        if search_type == 'keyword':
            results = indexer.keyword_search(query=query, n_results=limit)
        elif search_type == 'hybrid':
            results = indexer.hybrid_search(query=query, n_results=limit)
        else:  # semantic
            results = indexer.semantic_search(query=query, n_results=limit, threshold=threshold)
            
        if results:
            click.echo(f"\n--- Search Results ({len(results)} found) ---")
            for i, result in enumerate(results[:limit], 1):
                click.echo(f"{i}. File: {result.get('filepath', 'N/A')}")
                click.echo(f"   Snippet: {result.get('snippet', 'No snippet available')}")
                if result.get('score'):
                    click.echo(f"   Score: {result.get('score', 0):.3f}")
                click.echo("-" * 40)
            if len(results) > limit:
                click.echo(f"... and {len(results) - limit} more results")
        else:
            click.echo("No matching documents found.")
    except Exception as e:
        click.echo(f"Error during search: {e}", err=True)
        raise click.Abort()

# --- Stats Command ---
@cli.command()
def stats():
    """
    Shows statistics about the unified ChromaDB index.
    """
    click.echo("Loading index statistics...")
    try:
        indexer = SemanticIndexer(persist_directory='data/chroma_db')
        stats_data = indexer.get_collection_stats()
        
        click.echo(f"\n--- Index Statistics ---")
        click.echo(f"Total chunks: {stats_data.get('total_chunks', 0)}")
        click.echo(f"Model: {stats_data.get('model_name', 'Unknown')}")
        click.echo(f"Database path: {stats_data.get('persist_directory', 'Unknown')}")
        
        # Try to get more detailed stats
        try:
            all_docs = indexer.collection.get()
            if all_docs and all_docs.get('metadatas'):
                file_types = {}
                total_files = set()
                metadatas = all_docs['metadatas']
                if metadatas:
                    for metadata in metadatas:
                        if isinstance(metadata, dict):
                            filepath = metadata.get('filepath', '')
                            if filepath:
                                total_files.add(filepath)
                            extension = metadata.get('extension', '')
                            if extension:
                                file_types[extension] = file_types.get(extension, 0) + 1
                
                click.echo(f"Total unique files: {len(total_files)}")
                if file_types:
                    click.echo(f"\nFile types:")
                    for file_type, count in file_types.items():
                        click.echo(f"  {file_type}: {count}")
        except Exception as e:
            click.echo(f"Could not get detailed stats: {e}")
                
    except Exception as e:
        click.echo(f"Error loading statistics: {e}", err=True)
        raise click.Abort()

# --- Google Drive Commands ---
@cli.group()
def gdrive():
    """
    Google Drive integration commands.
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        click.echo("Google Drive integration not available. Install google-auth and google-auth-oauthlib.", err=True)
        raise click.Abort()
    pass

@gdrive.command()
@click.argument('credentials_path', type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
def setup(credentials_path: str):
    """
    Sets up Google Drive API credentials.
    """
    click.echo(f"Setting up Google Drive credentials from: {credentials_path}")
    try:
        setup_google_drive_credentials(credentials_path)
        click.echo("Google Drive credentials configured successfully!")
    except Exception as e:
        click.echo(f"Error setting up credentials: {e}", err=True)
        raise click.Abort()

@gdrive.command()
@click.option('--folder-id', '-f', help='Google Drive folder ID to index (default: root folder)')
@click.option('--query', '-q', help='Additional query to filter files (e.g., "mimeType contains \'pdf\'")')
def index_gdrive(folder_id: Optional[str], query: Optional[str]):
    """
    Indexes Google Drive files and merges them with the local index.
    """
    click.echo("Starting Google Drive indexing...")
    if folder_id:
        click.echo(f"Folder ID: {folder_id}")
    if query:
        click.echo(f"Query filter: {query}")
    
    try:
        stats = build_google_drive_index(
            folder_id=folder_id,
            query=query
        )
        
        if stats:
            click.echo(f"Google Drive indexing complete!")
            click.echo(f"Files indexed: {stats.get('stats', {}).get('total_files', 0)}")
            click.echo(f"Documents created: {stats.get('stats', {}).get('total_documents', 0)}")
        else:
            click.echo("Error: Failed to index Google Drive files.", err=True)
            raise click.Abort()
            
    except Exception as e:
        click.echo(f"Error during Google Drive indexing: {e}", err=True)
        raise click.Abort()

@gdrive.command()
@click.argument('query')
@click.option('--folder-id', '-f', help='Google Drive folder ID to search in (default: all folders)')
@click.option('--limit', '-n', default=10, help='Maximum number of results to show')
def search_gdrive(query: str, folder_id: Optional[str], limit: int):
    """
    Searches Google Drive files.
    """
    click.echo(f"Searching Google Drive for: '{query}'")
    if folder_id:
        click.echo(f"Folder ID: {folder_id}")
    
    try:
        results = search_google_drive(
            query=query,
            folder_id=folder_id,
            limit=limit
        )
        
        if results:
            click.echo(f"\n--- Google Drive Search Results ({len(results)} found) ---")
            for i, result in enumerate(results[:limit], 1):
                click.echo(f"{i}. File: {result.get('filename', 'N/A')}")
                click.echo(f"   ID: {result.get('filepath', 'N/A')}")
                click.echo(f"   Snippet: {result.get('snippet', 'No snippet available')}")
                click.echo("-" * 40)
            if len(results) > limit:
                click.echo(f"... and {len(results) - limit} more results")
        else:
            click.echo("No matching Google Drive files found.")
    except Exception as e:
        click.echo(f"Error during Google Drive search: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
import click
import os
from typing import Optional

# Import the core logic functions from your pkg directory
from pkg.indexer.semantic import SemanticIndexer
from pkg.indexer.google_drive import build_google_drive_index, search_google_drive
from pkg.utils.google_drive import setup_google_drive_credentials, GOOGLE_DRIVE_AVAILABLE
from pkg.indexer.incremental import smart_semantic_index
from pkg.utils.initialization import check_app_status, initialize_app, reinitialize_app
from pkg.llm.local_llm import get_llm_manager

# --- Main Click Group ---
@click.group()
@click.version_option(version='0.1.0', prog_name='desktop-search')
def cli():
    """
    A simple local document search tool with unified ChromaDB indexing.
    """
    pass

# --- Status Command ---
@cli.command()
@click.option('--fix', is_flag=True, help='Automatically fix missing components')
@click.option('--reinitialize', is_flag=True, help='Reinitialize everything from scratch (removes all existing data)')
def status(fix: bool, reinitialize: bool):
    """
    Check the status of the Desktop Search application components.
    
    Shows the status of:
    - SSL certificates
    - Database
    - API keys
    - Directories configuration
    """
    click.echo("🔍 Checking Desktop Search application status...")
    
    try:
        status_info = check_app_status()
        
        # Display status
        click.echo("\n📊 Application Status:")
        click.echo("=" * 50)
        
        # Certificates
        certs = status_info['certs']
        click.echo("🔐 SSL Certificates:")
        click.echo(f"   Key file: {'✅' if certs['key_exists'] else '❌'}")
        click.echo(f"   Cert file: {'✅' if certs['cert_exists'] else '❌'}")
        
        # Database
        db = status_info['database']
        click.echo("\n🗄️  Database:")
        click.echo(f"   Data directory: {'✅' if db['data_dir_exists'] else '❌'}")
        click.echo(f"   ChromaDB directory: {'✅' if db['chroma_db_exists'] else '❌'}")
        click.echo(f"   Has data: {'✅' if db['has_data'] else '❌'}")
        
        # API Keys
        keys = status_info['api_keys']
        click.echo("\n🔑 API Keys:")
        click.echo(f"   API_KEY: {'✅' if keys['api_key_set'] else '❌'}")
        click.echo(f"   JWT_SECRET_KEY: {'✅' if keys['jwt_secret_set'] else '❌'}")
        
        # Directories
        dirs = status_info['directories']
        click.echo("\n📁 Directories Configuration:")
        click.echo(f"   directories.json: {'✅' if dirs['config_exists'] else '❌'}")
        
        # Summary
        all_good = (
            certs['key_exists'] and certs['cert_exists'] and
            db['data_dir_exists'] and db['chroma_db_exists'] and
            dirs['config_exists']
        )
        
        click.echo("\n" + "=" * 50)
        
        if reinitialize:
            click.echo("\n🔄 Reinitializing everything from scratch...")
            click.echo("⚠️  This will remove ALL existing data including:")
            click.echo("   - SSL certificates")
            click.echo("   - Database and indexes")
            click.echo("   - Directory configurations")
            click.echo("   - Index metadata")
            
            if click.confirm("Are you sure you want to continue?"):
                if reinitialize_app():
                    click.echo("✅ Reinitialization completed successfully!")
                else:
                    click.echo("❌ Reinitialization failed!")
                    raise click.Abort()
            else:
                click.echo("❌ Reinitialization cancelled")
                raise click.Abort()
        elif all_good:
            click.echo("✅ All components are ready!")
        else:
            click.echo("⚠️  Some components are missing or incomplete")
            
            if fix:
                click.echo("\n🔧 Attempting to fix missing components...")
                if initialize_app():
                    click.echo("✅ Fixed successfully!")
                else:
                    click.echo("❌ Failed to fix some components")
            else:
                click.echo("\n💡 Run 'desktop-search status --fix' to automatically fix missing components")
                click.echo("   Or run 'desktop-search status --reinitialize' to start completely fresh")
        
    except Exception as e:
        click.echo(f"❌ Error checking status: {e}", err=True)
        raise click.Abort()

# --- Reinitialize Command ---
@cli.command()
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
def reinitialize(force: bool):
    """
    Reinitialize the Desktop Search application from scratch.
    
    WARNING: This will remove ALL existing data including:
    - SSL certificates
    - Database and indexes
    - Directory configurations
    - Index metadata
    
    Use this when you want to start completely fresh.
    """
    click.echo("🔄 Reinitializing Desktop Search application from scratch...")
    click.echo("⚠️  This will remove ALL existing data!")
    
    if not force:
        click.echo("\nThe following will be removed:")
        click.echo("   - SSL certificates")
        click.echo("   - Database and indexes")
        click.echo("   - Directory configurations")
        click.echo("   - Index metadata")
        
        if not click.confirm("Are you sure you want to continue?"):
            click.echo("❌ Reinitialization cancelled")
            raise click.Abort()
    
    try:
        if reinitialize_app():
            click.echo("✅ Reinitialization completed successfully!")
            click.echo("\n📋 What was recreated:")
            click.echo("   🔐 SSL certificates")
            click.echo("   🗄️  Database directories")
            click.echo("   📁 Directories configuration")
            click.echo("   🔑 API key status checked")
        else:
            click.echo("❌ Reinitialization failed!")
            raise click.Abort()
            
    except Exception as e:
        click.echo(f"❌ Error during reinitialization: {e}", err=True)
        raise click.Abort()

# --- Init Command ---
@cli.command()
def init():
    """
    Initialize the Desktop Search application.
    
    Creates all necessary components:
    - SSL certificates
    - Database directories
    - Directories configuration
    - Checks API keys
    """
    click.echo("🚀 Initializing Desktop Search application...")
    
    try:
        if initialize_app():
            click.echo("✅ Application initialized successfully!")
            click.echo("\n📋 What was created:")
            click.echo("   🔐 SSL certificates (if missing)")
            click.echo("   🗄️  Database directories")
            click.echo("   📁 Directories configuration")
            click.echo("   🔑 API key status checked")
        else:
            click.echo("❌ Initialization failed!")
            raise click.Abort()
            
    except Exception as e:
        click.echo(f"❌ Error during initialization: {e}", err=True)
        raise click.Abort()

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

# --- LLM Enhanced Search Commands ---
@cli.group()
def llm():
    """
    LLM-enhanced search commands using local models.
    
    Provides ChatGPT-like search enhancement capabilities while keeping everything private and local.
    """
    pass

@llm.command()
@click.argument('query')
@click.option('--limit', '-n', default=10, help='Maximum number of results to show')
@click.option('--search-type', '-t', type=click.Choice(['keyword', 'semantic', 'hybrid']), default='semantic', help='Type of search to perform')
@click.option('--threshold', '-th', default=0.3, help='Similarity threshold (0-1) for semantic search')
def enhanced_search(query: str, limit: int, search_type: str, threshold: float):
    """
    Enhanced search with LLM-generated insights.
    
    Performs a search and then uses a local LLM to provide insights,
    summaries, and recommendations based on the search results.
    """
    click.echo(f"🔍 Enhanced search for: '{query}' (using local LLM)")
    
    try:
        # Get LLM manager
        llm_manager = get_llm_manager()
        
        # Check LLM availability
        available_providers = llm_manager.detect_providers()
        if not available_providers:
            click.echo("❌ No local LLM providers available")
            click.echo("💡 Install Ollama to enable LLM features")
            click.echo("   - Ollama: https://ollama.ai/")
            raise click.Abort()
        
        click.echo(f"✅ Found LLM providers: {', '.join(available_providers)}")
        
        # Perform search
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
        
        if not results:
            click.echo("No matching documents found.")
            return
        
        # Enhance with LLM
        click.echo(f"\n🤖 Enhancing results with local LLM...")
        enhanced_response = llm_manager.enhance_search_results(query, results)
        
        if enhanced_response.get("enhanced", False):
            click.echo(f"\n📊 LLM Insights:")
            click.echo("=" * 60)
            click.echo(enhanced_response.get("llm_response", ""))
            click.echo("=" * 60)
            click.echo(f"Provider: {enhanced_response.get('provider', 'Unknown')}")
        else:
            click.echo(f"⚠️  LLM enhancement failed: {enhanced_response.get('message', 'Unknown error')}")
        
        # Show search results
        click.echo(f"\n📄 Search Results ({len(results)} found):")
        click.echo("-" * 40)
        for i, result in enumerate(results[:limit], 1):
            click.echo(f"{i}. File: {result.get('filepath', 'N/A')}")
            click.echo(f"   Snippet: {result.get('snippet', 'No snippet available')[:200]}...")
            if result.get('score'):
                click.echo(f"   Score: {result.get('score', 0):.3f}")
            click.echo()
            
    except Exception as e:
        click.echo(f"Error during enhanced search: {e}", err=True)
        raise click.Abort()

@llm.command()
@click.argument('question')
@click.option('--max-results', '-n', default=10, help='Maximum number of search results to use')
@click.option('--threshold', '-th', default=0.3, help='Similarity threshold (0-1) for search')
def ask_question(question: str, max_results: int, threshold: float):
    """
    Ask a specific question and get LLM-generated answer based on search results.
    
    The LLM will search through your documents and provide a comprehensive
    answer based on the relevant content found.
    """
    click.echo(f"❓ Question: '{question}'")
    
    try:
        # Get LLM manager
        llm_manager = get_llm_manager()
        
        # Check LLM availability
        available_providers = llm_manager.detect_providers()
        if not available_providers:
            click.echo("❌ No local LLM providers available")
            click.echo("💡 Install Ollama to enable LLM features")
            raise click.Abort()
        
        click.echo(f"✅ Found LLM providers: {', '.join(available_providers)}")
        
        # Perform search to get relevant documents
        indexer = SemanticIndexer(
            persist_directory='data/chroma_db',
            model_name='all-MiniLM-L6-v2'
        )
        
        search_results = indexer.semantic_search(
            query=question,
            n_results=max_results,
            threshold=threshold
        )
        
        if not search_results:
            click.echo("No relevant documents found to answer your question.")
            return
        
        # Get LLM answer
        click.echo(f"\n🤖 Generating answer with local LLM...")
        answer_response = llm_manager.answer_question(question, search_results)
        
        if answer_response.get("answered", False):
            click.echo(f"\n💡 Answer:")
            click.echo("=" * 60)
            click.echo(answer_response.get("answer", ""))
            click.echo("=" * 60)
            click.echo(f"Provider: {answer_response.get('provider', 'Unknown')}")
            
            sources = answer_response.get("sources", [])
            if sources:
                click.echo(f"\n📚 Sources ({len(sources)} documents):")
                for i, source in enumerate(sources[:5], 1):
                    click.echo(f"   {i}. {source}")
                if len(sources) > 5:
                    click.echo(f"   ... and {len(sources) - 5} more")
        else:
            click.echo(f"❌ Failed to answer question: {answer_response.get('message', 'Unknown error')}")
            
    except Exception as e:
        click.echo(f"Error answering question: {e}", err=True)
        raise click.Abort()

@llm.command()
@click.argument('query')
@click.option('--max-results', '-n', default=20, help='Maximum number of search results to summarize')
@click.option('--threshold', '-th', default=0.3, help='Similarity threshold (0-1) for search')
def summarize(query: str, max_results: int, threshold: float):
    """
    Generate a summary of search results using local LLM.
    
    Searches for documents matching the query and then uses a local LLM
    to generate a comprehensive summary of the key information found.
    """
    click.echo(f"📝 Generating summary for: '{query}'")
    
    try:
        # Get LLM manager
        llm_manager = get_llm_manager()
        
        # Check LLM availability
        available_providers = llm_manager.detect_providers()
        if not available_providers:
            click.echo("❌ No local LLM providers available")
            click.echo("💡 Install Ollama to enable LLM features")
            raise click.Abort()
        
        click.echo(f"✅ Found LLM providers: {', '.join(available_providers)}")
        
        # Perform search
        indexer = SemanticIndexer(
            persist_directory='data/chroma_db',
            model_name='all-MiniLM-L6-v2'
        )
        
        search_results = indexer.semantic_search(
            query=query,
            n_results=max_results,
            threshold=threshold
        )
        
        if not search_results:
            click.echo("No documents found to summarize.")
            return
        
        # Generate summary
        click.echo(f"\n🤖 Generating summary with local LLM...")
        summary_response = llm_manager.generate_summary(search_results)
        
        if summary_response.get("summarized", False):
            click.echo(f"\n📋 Summary:")
            click.echo("=" * 60)
            click.echo(summary_response.get("summary", ""))
            click.echo("=" * 60)
            click.echo(f"Provider: {summary_response.get('provider', 'Unknown')}")
            click.echo(f"Documents analyzed: {summary_response.get('result_count', 0)}")
        else:
            click.echo(f"❌ Failed to generate summary: {summary_response.get('message', 'Unknown error')}")
            
    except Exception as e:
        click.echo(f"Error generating summary: {e}", err=True)
        raise click.Abort()

@llm.command()
def llm_status():
    """
    Check the status of local LLM providers.
    """
    click.echo("🔍 Checking local LLM providers...")
    
    try:
        # Get comprehensive LLM status
        from pkg.utils.llm_initialization import get_llm_status
        llm_status = get_llm_status()
        
        click.echo(f"\n📊 LLM System Status:")
        click.echo("=" * 50)
        
        # Ollama status
        ollama_running = llm_status.get("ollama_running", False)
        click.echo(f"Ollama Status: {'✅ Running' if ollama_running else '❌ Not running'}")
        
        # GPU status
        gpu_available = llm_status.get("gpu_available", False)
        click.echo(f"GPU Available: {'✅ Yes' if gpu_available else '❌ No'}")
        
        # Models
        models = llm_status.get("models_available", [])
        if models:
            click.echo(f"Available Models: {', '.join(models)}")
        else:
            click.echo("Available Models: None (consider running 'ollama pull phi3')")
        
        # Provider status
        llm_manager = get_llm_manager()
        status_info = llm_manager.get_provider_status()
        
        active_provider = status_info.get("active_provider")
        if active_provider:
            click.echo(f"Active Provider: {active_provider}")
        else:
            click.echo("Active Provider: None")
        
        available_providers = status_info.get("available_providers", [])
        if available_providers:
            click.echo(f"\n📋 Available Providers:")
            for provider in available_providers:
                status_icon = "✅" if provider.get("available", False) else "❌"
                loaded_icon = "✅" if provider.get("loaded", False) else "❌"
                click.echo(f"   {status_icon} {provider['name']} ({provider['type']}) - Loaded: {loaded_icon}")
        else:
            click.echo("\n❌ No LLM providers available")
            click.echo("💡 Install one of the following:")
            click.echo("   - Ollama: https://ollama.ai/")
        
        detected = status_info.get("detected_providers", [])
        if detected:
            click.echo(f"\n🔍 Detected Providers: {', '.join(detected)}")
        
        # Show performance statistics
        performance_stats = status_info.get("performance_stats", {})
        if performance_stats:
            click.echo(f"\n📈 Performance Statistics:")
            click.echo(f"   Total Requests: {performance_stats.get('total_requests', 0)}")
            click.echo(f"   Cache Hits: {performance_stats.get('cache_hits', 0)}")
            click.echo(f"   Cache Hit Rate: {performance_stats.get('cache_hit_rate', 0.0):.2%}")
            click.echo(f"   Avg Response Time: {performance_stats.get('average_response_time', 0.0):.2f}s")
        
        # Show cache information
        cache_info = status_info.get("cache_info")
        if cache_info:
            click.echo(f"\n💾 Cache Information:")
            click.echo(f"   Enabled: {'✅' if cache_info.get('enabled', False) else '❌'}")
            click.echo(f"   Current Size: {cache_info.get('size', 0)}")
            click.echo(f"   Max Size: {cache_info.get('max_size', 0)}")
        
    except Exception as e:
        click.echo(f"Error checking LLM status: {e}", err=True)
        raise click.Abort()

@llm.command()
def performance():
    """
    Show detailed LLM performance statistics and optimization options.
    """
    click.echo("📊 LLM Performance Analysis")
    
    try:
        llm_manager = get_llm_manager()
        stats = llm_manager.get_performance_stats()
        
        click.echo(f"\n📈 Performance Statistics:")
        click.echo("=" * 50)
        click.echo(f"Total Requests: {stats.get('total_requests', 0)}")
        click.echo(f"Cache Hits: {stats.get('cache_hits', 0)}")
        click.echo(f"Cache Hit Rate: {stats.get('cache_hit_rate', 0.0):.2%}")
        click.echo(f"Average Response Time: {stats.get('average_response_time', 0.0):.2f}s")
        click.echo(f"Total Response Time: {stats.get('total_response_time', 0.0):.2f}s")
        
        # Show configuration
        config = llm_manager.config
        click.echo(f"\n⚙️  Current Configuration:")
        click.echo("=" * 50)
        click.echo(f"GPU Acceleration: {'✅' if config.use_gpu else '❌'}")
        click.echo(f"Response Caching: {'✅' if config.cache_responses else '❌'}")
        click.echo(f"Cache Size: {config.cache_size}")
        click.echo(f"Max Concurrent Requests: {config.max_concurrent_requests}")
        click.echo(f"Request Timeout: {config.request_timeout}s")
        click.echo(f"Batch Size: {config.batch_size}")
        
        # Performance recommendations
        click.echo(f"\n💡 Performance Recommendations:")
        click.echo("=" * 50)
        
        if not config.use_gpu:
            click.echo("🔧 Enable GPU acceleration for faster inference")
        
        if not config.cache_responses:
            click.echo("🔧 Enable response caching for repeated queries")
        
        if config.max_concurrent_requests < 8:
            click.echo("🔧 Increase max concurrent requests to 8")
        
        if stats.get('cache_hit_rate', 0.0) < 0.1:
            click.echo("🔧 Consider increasing cache size for better hit rates")
        
        if stats.get('average_response_time', 0.0) > 5.0:
            click.echo("🔧 Consider using a smaller/faster model")
        
        click.echo("\n💡 Use 'llm optimize' to apply recommended optimizations")
        
    except Exception as e:
        click.echo(f"Error getting performance stats: {e}", err=True)
        raise click.Abort()

@llm.command()
def optimize():
    """
    Apply performance optimizations to the LLM setup.
    """
    click.echo("🔧 Applying LLM Performance Optimizations...")
    
    try:
        llm_manager = get_llm_manager()
        
        # Apply optimizations
        optimizations = []
        
        # Enable GPU if available
        if llm_manager.config.use_gpu:
            optimizations.append("GPU acceleration enabled")
        
        # Enable caching if not already enabled
        if not llm_manager.config.cache_responses:
            llm_manager.config.cache_responses = True
            optimizations.append("Response caching enabled")
        
        # Optimize concurrent requests
        if llm_manager.config.max_concurrent_requests < 8:
            llm_manager.config.max_concurrent_requests = 8
            optimizations.append("Concurrent requests increased to 8")
        
        # Update provider configurations
        for provider in llm_manager.providers.values():
            if hasattr(provider, '_configure_model_performance'):
                provider._configure_model_performance()
                optimizations.append(f"Model performance configured for {type(provider).__name__}")
        
        if optimizations:
            click.echo("✅ Applied optimizations:")
            for opt in optimizations:
                click.echo(f"   • {opt}")
        else:
            click.echo("ℹ️  No optimizations needed - system is already optimized")
        
        click.echo("\n💡 Run 'llm performance' to see current statistics")
        
    except Exception as e:
        click.echo(f"Error applying optimizations: {e}", err=True)
        raise click.Abort()

@llm.command()
def clear_stats():
    """
    Clear LLM performance statistics.
    """
    click.echo("🗑️  Clearing LLM performance statistics...")
    
    try:
        llm_manager = get_llm_manager()
        llm_manager.clear_performance_stats()
        click.echo("✅ Performance statistics cleared")
        
    except Exception as e:
        click.echo(f"Error clearing statistics: {e}", err=True)
        raise click.Abort()

@llm.command()
def initialize():
    """
    Initialize LLM system with GPU detection and optimizations.
    """
    click.echo("🤖 Initializing LLM system...")
    
    try:
        from pkg.utils.llm_initialization import initialize_llm_system
        
        results = initialize_llm_system()
        
        if results.get("errors"):
            click.echo("❌ LLM initialization failed:")
            for error in results["errors"]:
                click.echo(f"   - {error}")
            raise click.Abort()
        
        # Print summary
        click.echo("\n📊 LLM System Summary:")
        click.echo("=" * 40)
        click.echo(f"Ollama Status: {'✅ Running' if results.get('ollama_status') else '❌ Not running'}")
        click.echo(f"GPU Available: {'✅ Yes' if results.get('gpu_available') else '❌ No'}")
        click.echo(f"GPU Acceleration: {'✅ Enabled' if results.get('gpu_acceleration') else '❌ Disabled'}")
        click.echo(f"Concurrent Processing: {'✅ Enabled' if results.get('concurrent_processing') else '❌ Disabled'}")
        
        models = results.get("models_available", [])
        if models:
            click.echo(f"Available Models: {', '.join(models)}")
        else:
            click.echo("Available Models: None (consider running 'ollama pull phi3')")
        
        optimizations = results.get("optimizations_applied", [])
        if optimizations:
            click.echo("\nOptimizations Applied:")
            for opt in optimizations:
                click.echo(f"   ✅ {opt}")
        
        click.echo("\n✅ LLM system initialized successfully!")
        
    except Exception as e:
        click.echo(f"Error initializing LLM system: {e}", err=True)
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
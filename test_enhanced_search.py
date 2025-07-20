#!/usr/bin/env python3
"""
Test script for Enhanced Hybrid Search System
Tests indexing, search, and Q&A functionality
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test configuration
API_BASE = "http://localhost:8880/api/v1/enhanced-search"
TEST_DIR = project_root / "test_docs"

def create_test_documents():
    """Create test documents for testing"""
    TEST_DIR.mkdir(exist_ok=True)
    
    # Create various test files
    test_files = {
        "sample.txt": """
        This is a sample text document for testing the enhanced search system.
        It contains information about machine learning, artificial intelligence, and data science.
        The document discusses various algorithms and techniques used in modern AI applications.
        """,
        
        "python_code.py": """
        # Sample Python code for testing
        def machine_learning_algorithm(data):
            \"\"\"
            This function implements a machine learning algorithm.
            It processes data and returns predictions.
            \"\"\"
            import numpy as np
            from sklearn.ensemble import RandomForestClassifier
            
            # Preprocess the data
            processed_data = np.array(data)
            
            # Train the model
            model = RandomForestClassifier(n_estimators=100)
            model.fit(processed_data, labels)
            
            return model.predict(test_data)
        
        class DataProcessor:
            def __init__(self):
                self.model = None
            
            def train(self, training_data):
                self.model = machine_learning_algorithm(training_data)
        """,
        
        "research_paper.md": """
        # Research Paper on Hybrid Search Systems

        ## Abstract
        This paper presents a novel approach to document search that combines
        traditional keyword-based methods with modern semantic search techniques.

        ## Introduction
        Document search has evolved significantly over the past decade.
        Traditional keyword search methods like BM25 and TF-IDF have been
        supplemented by semantic search using neural embeddings.

        ## Methodology
        Our hybrid approach combines:
        1. **Keyword Search**: Using BM25 algorithm for exact matches
        2. **Semantic Search**: Using sentence transformers for meaning-based search
        3. **Local LLM Integration**: For question-answering capabilities

        ## Results
        The hybrid system shows 25% improvement over baseline methods
        in terms of search relevance and user satisfaction.

        ## Conclusion
        Hybrid search systems represent the future of document retrieval,
        offering both precision and semantic understanding.
        """,
        
        "config.json": """
        {
            "search_config": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "embedding_model": "all-MiniLM-L6-v2",
                "enable_llm": true
            },
            "indexing_config": {
                "supported_formats": ["txt", "md", "py", "json", "pdf", "docx"],
                "max_file_size": "100MB",
                "enable_ocr": true
            }
        }
        """
    }
    
    for filename, content in test_files.items():
        filepath = TEST_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content.strip())
    
    print(f"✅ Created {len(test_files)} test documents in {TEST_DIR}")

def test_api_health():
    """Test API health endpoint"""
    print("\n🔍 Testing API Health...")
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data['data']['status']}")
            return True
        else:
            print(f"❌ API Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health error: {e}")
        return False

def test_indexing():
    """Test document indexing"""
    print("\n📁 Testing Document Indexing...")
    
    try:
        response = requests.post(f"{API_BASE}/index", json={
            "directory_path": str(TEST_DIR),
            "clear_existing": True,
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "embedding_model": "all-MiniLM-L6-v2",
            "enable_llm": True
        }, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            stats = data['data']['statistics']
            print(f"✅ Indexing completed:")
            print(f"   - Processed files: {stats['processed_files']}")
            print(f"   - Total chunks: {stats['total_chunks']}")
            print(f"   - Duration: {stats.get('duration', 'N/A')}s")
            return True
        else:
            print(f"❌ Indexing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Indexing error: {e}")
        return False

def test_hybrid_search():
    """Test hybrid search functionality"""
    print("\n🔍 Testing Hybrid Search...")
    
    test_queries = [
        "machine learning algorithms",
        "python code implementation",
        "research methodology",
        "hybrid search systems",
        "document processing"
    ]
    
    for query in test_queries:
        try:
            response = requests.post(f"{API_BASE}/search", json={
                "query": query,
                "n_results": 5,
                "semantic_weight": 0.7,
                "keyword_weight": 0.3,
                "include_metadata": True
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data['data']['results']
                print(f"✅ Query '{query}': {len(results)} results")
                
                if results:
                    top_result = results[0]
                    print(f"   Top result: {top_result['filename']} (Score: {top_result['score']:.3f})")
            else:
                print(f"❌ Search failed for '{query}': {response.status_code}")
                
        except Exception as e:
            print(f"❌ Search error for '{query}': {e}")

def test_semantic_search():
    """Test semantic search only"""
    print("\n🧠 Testing Semantic Search...")
    
    try:
        response = requests.get(f"{API_BASE}/semantic-search?query=artificial intelligence&n_results=3", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = data['data']['results']
            print(f"✅ Semantic search: {len(results)} results")
            
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['filename']} (Score: {result['score']:.3f})")
        else:
            print(f"❌ Semantic search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Semantic search error: {e}")

def test_keyword_search():
    """Test keyword search only"""
    print("\n🔤 Testing Keyword Search...")
    
    try:
        response = requests.get(f"{API_BASE}/keyword-search?query=python&n_results=3", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            results = data['data']['results']
            print(f"✅ Keyword search: {len(results)} results")
            
            for i, result in enumerate(results[:2]):
                print(f"   {i+1}. {result['filename']} (Score: {result['score']:.3f})")
        else:
            print(f"❌ Keyword search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Keyword search error: {e}")

def test_qa_functionality():
    """Test Q&A functionality"""
    print("\n🤖 Testing Q&A Functionality...")
    
    test_questions = [
        "What is machine learning?",
        "How does the hybrid search system work?",
        "What algorithms are mentioned in the documents?",
        "Explain the research methodology"
    ]
    
    session_id = None
    
    for question in test_questions:
        try:
            response = requests.post(f"{API_BASE}/ask", json={
                "question": question,
                "session_id": session_id,
                "include_sources": True,
                "max_context_results": 3
            }, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                answer_data = data['data']
                
                if not session_id and answer_data.get('session_id'):
                    session_id = answer_data['session_id']
                
                print(f"✅ Q: {question}")
                print(f"   A: {answer_data['answer'][:100]}...")
                print(f"   Sources: {len(answer_data['sources'])} documents")
                
                # Small delay between questions
                time.sleep(1)
            else:
                print(f"❌ Q&A failed for '{question}': {response.status_code}")
                
        except Exception as e:
            print(f"❌ Q&A error for '{question}': {e}")

def test_qa_session_management():
    """Test Q&A session management"""
    print("\n📝 Testing Q&A Session Management...")
    
    try:
        # List sessions
        response = requests.get(f"{API_BASE}/sessions", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            sessions = data['data']['sessions']
            print(f"✅ Found {len(sessions)} Q&A sessions")
            
            if sessions:
                # Get details of first session
                session_id = sessions[0]['session_id']
                response = requests.get(f"{API_BASE}/session/{session_id}", timeout=30)
                
                if response.status_code == 200:
                    session_data = response.json()
                    questions = session_data['data']['questions']
                    print(f"   Session {session_id[:8]}... has {len(questions)} questions")
                else:
                    print(f"❌ Failed to get session details: {response.status_code}")
        else:
            print(f"❌ Failed to list sessions: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Session management error: {e}")

def test_statistics():
    """Test statistics endpoint"""
    print("\n📊 Testing Statistics...")
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            stats = data['data']
            
            print(f"✅ System Statistics:")
            print(f"   - Vector documents: {stats.get('vector_documents', 0)}")
            print(f"   - Keyword documents: {stats.get('keyword_documents', 0)}")
            print(f"   - Q&A sessions: {stats.get('qa_sessions', 0)}")
            print(f"   - Total questions: {stats.get('total_questions', 0)}")
            print(f"   - Embedding model: {stats.get('embedding_model', 'N/A')}")
            print(f"   - LLM enabled: {stats.get('llm_enabled', False)}")
        else:
            print(f"❌ Statistics failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Statistics error: {e}")

def test_clear_index():
    """Test clearing the index"""
    print("\n🗑️ Testing Index Clear...")
    
    try:
        response = requests.post(f"{API_BASE}/clear-index", timeout=30)
        
        if response.status_code == 200:
            print("✅ Index cleared successfully")
            return True
        else:
            print(f"❌ Index clear failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Index clear error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Enhanced Hybrid Search System Test")
    print("=" * 50)
    
    # Check if API is running
    if not test_api_health():
        print("\n❌ API is not running. Please start the server first:")
        print("   python start_api.py")
        return
    
    # Create test documents
    create_test_documents()
    
    # Run tests
    test_indexing()
    test_hybrid_search()
    test_semantic_search()
    test_keyword_search()
    test_qa_functionality()
    test_qa_session_management()
    test_statistics()
    
    # Optional: clear index
    # test_clear_index()
    
    print("\n✅ Enhanced Search System Test Completed!")
    print("\n📋 Test Summary:")
    print("   - Document indexing with enhanced parsing")
    print("   - Hybrid search (semantic + keyword)")
    print("   - Individual semantic and keyword search")
    print("   - AI-powered Q&A with session management")
    print("   - System statistics and health monitoring")
    print("\n🌐 Access the enhanced search interface at:")
    print("   http://localhost:8880/enhanced-search.html")

if __name__ == "__main__":
    main() 
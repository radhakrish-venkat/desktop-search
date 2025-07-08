import re
import sys
from typing import List, Dict, Any, Optional, Tuple
import logging
from collections import Counter
import math

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def _tokenize_text(text: str) -> List[str]:
    """
    Performs basic tokenization: converts to lowercase and splits by non-alphanumeric characters.
    Filters out empty strings. This should be consistent with the indexer's tokenization.
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of tokens
    """
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Common stop words to filter out (same as indexer)
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours'
    }
    
    text = text.lower()
    tokens = [token for token in re.split(r'\W+', text) if token and len(token) > 1]
    tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
    
    return tokens

def _calculate_tf_idf_score(query_tokens: List[str], doc_tokens: List[str], 
                           total_docs: int, doc_freq: Dict[str, int]) -> float:
    """
    Calculate TF-IDF score for a document given query tokens.
    
    Args:
        query_tokens: List of query tokens
        doc_tokens: List of document tokens
        total_docs: Total number of documents in index
        doc_freq: Dictionary mapping tokens to document frequency
        
    Returns:
        TF-IDF score
    """
    if not doc_tokens:
        return 0.0
    
    doc_token_freq = Counter(doc_tokens)
    doc_length = len(doc_tokens)
    
    score = 0.0
    for token in query_tokens:
        if token in doc_token_freq:
            # TF (Term Frequency)
            tf = doc_token_freq[token] / doc_length
            
            # IDF (Inverse Document Frequency)
            if token in doc_freq and doc_freq[token] > 0:
                idf = math.log(total_docs / doc_freq[token])
            else:
                idf = 0.0
            
            score += tf * idf
    
    return score

def _generate_snippet(full_text: str, keywords: List[str], window_size: int = 200) -> str:
    """
    Generates a text snippet around the best occurrence of keywords.

    Args:
        full_text: The entire text of the document
        keywords: A list of keywords to search for
        window_size: The approximate number of characters for the snippet

    Returns:
        A snippet of text containing keywords, with ellipses if truncated
    """
    if not full_text or not keywords:
        return full_text[:window_size] + "..." if len(full_text) > window_size else full_text
    
    text_lower = full_text.lower()
    best_match_index = -1
    best_score = 0
    
    # Find the best match (most keywords in smallest area)
    for i in range(0, len(text_lower) - min(len(keywords[0]), 10)):
        score = 0
        for keyword in keywords:
            if text_lower[i:i+len(keyword)] == keyword:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match_index = i
    
    if best_match_index == -1:
        # Fallback: find first occurrence of any keyword
        for keyword in keywords:
            match_index = text_lower.find(keyword)
            if match_index != -1:
                best_match_index = match_index
                break
    
    if best_match_index == -1:
        return full_text[:window_size] + "..." if len(full_text) > window_size else full_text

    # Calculate start and end for the snippet
    start_index = max(0, best_match_index - window_size // 2)
    end_index = min(len(full_text), best_match_index + window_size // 2)

    snippet = full_text[start_index:end_index]

    # Add ellipses if the snippet is truncated
    if start_index > 0:
        snippet = "..." + snippet
    if end_index < len(full_text):
        snippet = snippet + "..."

    return snippet.strip()

def search_index(query_string: str, index_data: Dict[str, Any], 
                max_results: int = 50) -> List[Dict[str, str]]:
    """
    Searches the given index for documents matching the query.

    Args:
        query_string: The user's search query
        index_data: The loaded index data containing 'inverted_index' and 'document_store'
        max_results: Maximum number of results to return

    Returns:
        A list of dictionaries, each containing 'filepath' and 'snippet' for matching documents
    """
    if not index_data or 'inverted_index' not in index_data or 'document_store' not in index_data:
        logger.error("Invalid index data provided for search")
        return []

    inverted_index = index_data['inverted_index']
    document_store = index_data['document_store']
    
    if not document_store:
        return []

    query_tokens = _tokenize_text(query_string)
    if not query_tokens:
        return []

    # Find matching documents
    matching_doc_ids = set()
    for token in query_tokens:
        if token in inverted_index:
            matching_doc_ids.update(inverted_index[token])

    if not matching_doc_ids:
        return []

    # Calculate document frequency for IDF
    doc_freq = {}
    for token in query_tokens:
        if token in inverted_index:
            doc_freq[token] = len(inverted_index[token])

    # Score and rank results
    scored_results = []
    total_docs = len(document_store)
    
    for doc_id in matching_doc_ids:
        doc_info = document_store.get(doc_id)
        if not doc_info:
            continue
            
        filepath = doc_info['filepath']
        full_text = doc_info['text']
        
        # Tokenize document text
        doc_tokens = _tokenize_text(full_text)
        
        # Calculate TF-IDF score
        score = _calculate_tf_idf_score(query_tokens, doc_tokens, total_docs, doc_freq)
        
        # Generate snippet
        snippet = _generate_snippet(full_text, query_tokens)
        
        scored_results.append({
            'filepath': filepath,
            'snippet': snippet,
            'score': score,
            'doc_id': doc_id
        })

    # Sort by score (highest first) and limit results
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    
    # Return top results without score
    return [
        {
            'filepath': result['filepath'],
            'snippet': result['snippet']
        }
        for result in scored_results[:max_results]
    ]

def search_with_highlighting(query_string: str, index_data: Dict[str, Any], 
                           max_results: int = 50) -> List[Dict[str, Any]]:
    """
    Enhanced search that includes highlighting and additional metadata.
    
    Args:
        query_string: The user's search query
        index_data: The loaded index data
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries with filepath, snippet, score, and metadata
    """
    if not index_data or 'inverted_index' not in index_data or 'document_store' not in index_data:
        return []

    inverted_index = index_data['inverted_index']
    document_store = index_data['document_store']
    
    query_tokens = _tokenize_text(query_string)
    if not query_tokens:
        return []

    # Find matching documents
    matching_doc_ids = set()
    for token in query_tokens:
        if token in inverted_index:
            matching_doc_ids.update(inverted_index[token])

    if not matching_doc_ids:
        return []

    # Calculate document frequency
    doc_freq = {token: len(inverted_index[token]) for token in query_tokens if token in inverted_index}
    
    # Score and rank results
    scored_results = []
    total_docs = len(document_store)
    
    for doc_id in matching_doc_ids:
        doc_info = document_store.get(doc_id)
        if not doc_info:
            continue
            
        filepath = doc_info['filepath']
        full_text = doc_info['text']
        extension = doc_info.get('extension', '')
        
        # Tokenize and score
        doc_tokens = _tokenize_text(full_text)
        score = _calculate_tf_idf_score(query_tokens, doc_tokens, total_docs, doc_freq)
        
        # Generate highlighted snippet
        snippet = _generate_snippet(full_text, query_tokens)
        
        # Highlight keywords in snippet
        highlighted_snippet = snippet
        for token in query_tokens:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            highlighted_snippet = pattern.sub(f"**{token}**", highlighted_snippet)
        
        scored_results.append({
            'filepath': filepath,
            'snippet': highlighted_snippet,
            'score': score,
            'extension': extension,
            'doc_id': doc_id,
            'file_size': len(full_text)
        })

    # Sort by score and return top results
    scored_results.sort(key=lambda x: x['score'], reverse=True)
    return scored_results[:max_results]

# Test function for standalone testing
if __name__ == '__main__':
    # Create a dummy index for testing
    dummy_inverted_index = {
        'apple': {'doc1', 'doc3'},
        'fruit': {'doc1', 'doc2', 'doc3'},
        'orange': {'doc2'},
        'banana': {'doc3'},
        'delicious': {'doc1'},
        'health': {'doc2'},
        'tropical': {'doc3'}
    }
    
    dummy_document_store = {
        'doc1': {
            'filepath': '/path/to/doc1.txt', 
            'text': 'Apple is a fruit. Apple pie is delicious.',
            'extension': '.txt'
        },
        'doc2': {
            'filepath': '/path/to/doc2.txt', 
            'text': 'Orange is also a fruit. Oranges are good for health.',
            'extension': '.txt'
        },
        'doc3': {
            'filepath': '/path/to/doc3.txt', 
            'text': 'Banana is a yellow fruit that grows in tropical regions.',
            'extension': '.txt'
        },
    }
    
    dummy_index_data = {
        'inverted_index': dummy_inverted_index,
        'document_store': dummy_document_store,
        'indexed_directory': '/dummy/indexed/path'
    }

    print("--- Testing Search Functionality ---")

    test_queries = [
        "apple",
        "fruit",
        "orange health",
        "banana tropical",
        "delicious pie",
        "nonexistent word",
        "apple fruit delicious"
    ]

    for query in test_queries:
        print(f"\nSearching for: '{query}'")
        search_results = search_index(query, dummy_index_data)

        if search_results:
            for i, result in enumerate(search_results, 1):
                print(f"  {i}. File: {result['filepath']}")
                print(f"     Snippet: {result['snippet']}")
        else:
            print("  No results found.")

    print("\n--- Testing Enhanced Search ---")
    enhanced_results = search_with_highlighting("apple fruit", dummy_index_data)
    for result in enhanced_results:
        print(f"File: {result['filepath']}")
        print(f"Score: {result['score']:.3f}")
        print(f"Snippet: {result['snippet']}")
        print("-" * 40)
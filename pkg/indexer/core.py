import os
import re
import sys
import pickle
from typing import Dict, Set, List, Optional, Any
import logging
from collections import defaultdict

# Import our file parsing utility
from pkg.file_parsers.parsers import get_text_from_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File patterns to skip
SKIP_PATTERNS = [
    r'\.git/',
    r'node_modules/',
    r'\.DS_Store$',
    r'\.pyc$',
    r'\.log$',
    r'\.tmp$',
    r'\.cache/',
    r'__pycache__/',
    r'\.vscode/',
    r'\.idea/'
]

def _should_skip_file(filepath: str) -> bool:
    """Check if file should be skipped based on patterns."""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, filepath, re.IGNORECASE):
            return True
    return False

def _tokenize_text(text: str) -> List[str]:
    """
    Performs basic tokenization: converts to lowercase and splits by non-alphanumeric characters.
    Filters out empty strings and common stop words.
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of tokens
    """
    if not isinstance(text, str) or not text.strip():
        return []
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'that', 'over', 'too',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours'
    }
    
    text = text.lower()
    # Split by any character that is not a letter, number, or underscore
    tokens = [token for token in re.split(r'\W+', text) if token and len(token) > 1]
    
    # Filter out stop words and short tokens
    tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
    
    return tokens

def build_index(directory_path: str) -> Optional[Dict[str, Any]]:
    """
    Scans the specified directory, extracts text from supported files,
    and builds an inverted index and a document store.

    Args:
        directory_path: The path to the directory to scan.

    Returns:
        Dictionary containing inverted_index, document_store, and indexed_directory,
        or None if an error occurs.
    """
    if not os.path.isdir(directory_path):
        logger.error(f"Directory not found at {directory_path}")
        return None

    inverted_index: Dict[str, Set[str]] = defaultdict(set)
    document_store: Dict[str, Dict[str, str]] = {}
    doc_id_counter = 0
    processed_files = 0
    skipped_files = 0

    logger.info(f"Starting to index directory: {directory_path}")

    for root, dirs, files in os.walk(directory_path):
        # Skip directories that match our patterns
        dirs[:] = [d for d in dirs if not _should_skip_file(os.path.join(root, d))]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            
            # Skip files that match our patterns
            if _should_skip_file(filepath):
                skipped_files += 1
                continue

            try:
                extracted_text, file_ext = get_text_from_file(filepath)

                if extracted_text and extracted_text.strip():
                    doc_id = str(doc_id_counter)
                    document_store[doc_id] = {
                        'filepath': filepath,
                        'text': extracted_text,
                        'extension': file_ext
                    }
                    doc_id_counter += 1

                    # Tokenize the text
                    tokens = _tokenize_text(extracted_text)

                    # Add tokens to inverted index
                    for token in tokens:
                        inverted_index[token].add(doc_id)

                    processed_files += 1
                    
                    if processed_files % 100 == 0:
                        logger.info(f"Processed {processed_files} files...")
                        
            except Exception as e:
                logger.warning(f"Error processing file {filepath}: {e}")
                skipped_files += 1
                continue

    logger.info(f"Indexing complete. Processed {processed_files} files, skipped {skipped_files} files.")

    return {
        'inverted_index': dict(inverted_index),
        'document_store': document_store,
        'indexed_directory': directory_path,
        'stats': {
            'total_files': processed_files,
            'skipped_files': skipped_files,
            'unique_tokens': len(inverted_index),
            'total_documents': len(document_store)
        }
    }

def save_index(index_data: Dict[str, Any], filepath: str) -> bool:
    """
    Saves the index data to a file using pickle.

    Args:
        index_data: The dictionary containing index data
        filepath: The full path to the file where the index should be saved.

    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(index_data, f)
        logger.info(f"Index saved successfully to {filepath}")
        return True
    except (pickle.PickleError, OSError, IOError) as e:
        logger.error(f"Error saving index to {filepath}: {e}")
        return False

def load_index(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Loads the index data from a file using pickle.

    Args:
        filepath: The full path to the file from which the index should be loaded.

    Returns:
        The loaded index data, or None if the file does not exist or an error occurs.
    """
    if not os.path.exists(filepath):
        logger.warning(f"Index file not found at {filepath}")
        return None
        
    try:
        with open(filepath, 'rb') as f:
            index_data = pickle.load(f)
        logger.info(f"Index loaded successfully from {filepath}")
        return index_data
    except (pickle.PickleError, OSError, IOError) as e:
        logger.error(f"Error loading index from {filepath}: {e}")
        return None

def get_index_stats(index_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get statistics about the index.
    
    Args:
        index_data: The index data dictionary
        
    Returns:
        Dictionary containing index statistics
    """
    if not index_data:
        return {}
        
    stats = index_data.get('stats', {})
    inverted_index = index_data.get('inverted_index', {})
    document_store = index_data.get('document_store', {})
    
    # Calculate additional stats
    total_tokens = sum(len(doc_ids) for doc_ids in inverted_index.values())
    avg_tokens_per_doc = total_tokens / len(document_store) if document_store else 0
    
    return {
        **stats,
        'total_tokens': total_tokens,
        'avg_tokens_per_doc': round(avg_tokens_per_doc, 2),
        'most_common_tokens': sorted(
            [(token, len(doc_ids)) for token, doc_ids in inverted_index.items()],
            key=lambda x: x[1], reverse=True
        )[:10]
    }

# Test function for standalone testing
if __name__ == '__main__':
    test_data_dir = "test_data_for_indexer"
    os.makedirs(test_data_dir, exist_ok=True)
    index_file = os.path.join(test_data_dir, "test_index.pkl")

    # Create test files
    test_files = [
        ("doc1.txt", "Apple is a fruit. Apple pie is delicious."),
        ("doc2.txt", "Orange is also a fruit. Oranges are good for health."),
        ("doc3.txt", "Banana is a yellow fruit that grows in tropical regions."),
        ("doc4.txt", "The quick brown fox jumps over the lazy dog.")
    ]
    
    for filename, content in test_files:
        with open(os.path.join(test_data_dir, filename), "w", encoding="utf-8") as f:
            f.write(content)

    print(f"Building index for: {test_data_dir}")
    built_index = build_index(test_data_dir)

    if built_index:
        print("Index built successfully!")
        stats = get_index_stats(built_index)
        print(f"Statistics: {stats}")
        
        print(f"Saving index to: {index_file}")
        if save_index(built_index, index_file):
            print("Index saved successfully.")

            print(f"Loading index from: {index_file}")
            loaded_index = load_index(index_file)

            if loaded_index:
                print("Index loaded successfully.")
                print("\n--- Sample Index Data ---")
                for word in ['apple', 'fruit', 'orange', 'banana']:
                    if word in loaded_index['inverted_index']:
                        doc_ids = loaded_index['inverted_index'][word]
                        file_paths = [loaded_index['document_store'][doc_id]['filepath'] for doc_id in doc_ids]
                        print(f"'{word}': {file_paths}")
                    else:
                        print(f"'{word}': Not found")
            else:
                print("Failed to load index.")
        else:
            print("Failed to save index.")
    else:
        print("Index building failed.")

    # Clean up
    import shutil
    shutil.rmtree(test_data_dir)
    print("Test complete.")
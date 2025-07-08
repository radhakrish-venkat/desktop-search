import os
import re # For basic tokenization/cleaning
import sys # For sys.stderr in basic error prints
import pickle # New: For saving and loading the index

# Import our file parsing utility
from pkg.file_parsers.parsers import get_text_from_file

def _tokenize_text(text):
    """
    Performs basic tokenization: converts to lowercase and splits by non-alphanumeric characters.
    Filters out empty strings.
    """
    if not isinstance(text, str):
        return []
    text = text.lower()
    # Split by any character that is not a letter, number, or underscore, then filter out empty strings
    tokens = [token for token in re.split(r'\W+', text) if token]
    return tokens

def build_index(directory_path):
    """
    Scans the specified directory, extracts text from supported files,
    and builds an inverted index and a document store.

    Args:
        directory_path (str): The path to the directory to scan.

    Returns:
        dict: A dictionary containing:
            - 'inverted_index': A dict mapping words to sets of document IDs.
            - 'document_store': A dict mapping document IDs to document metadata (filepath, text).
            - 'indexed_directory': The path that was indexed.
        Returns None if an error occurs or directory is invalid.
    """
    inverted_index = {}  # {word: {doc_id1, doc_id2, ...}}
    document_store = {}  # {doc_id: {'filepath': 'path', 'text': 'full_text'}}
    doc_id_counter = 0

    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found at {directory_path}", file=sys.stderr)
        return None

    for root, _, files in os.walk(directory_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            # Skip common hidden/system files and directories
            if filename.startswith('.') or "node_modules" in filepath.lower():
                continue

            extracted_text, file_ext = get_text_from_file(filepath)

            if extracted_text is not None and extracted_text.strip():
                doc_id = str(doc_id_counter)
                document_store[doc_id] = {
                    'filepath': filepath,
                    'text': extracted_text
                }
                doc_id_counter += 1

                tokens = _tokenize_text(extracted_text)

                for token in tokens:
                    if token not in inverted_index:
                        inverted_index[token] = set()
                    inverted_index[token].add(doc_id)

    return {
        'inverted_index': inverted_index,
        'document_store': document_store,
        'indexed_directory': directory_path
    }

def save_index(index_data, filepath):
    """
    Saves the index data to a file using pickle.

    Args:
        index_data (dict): The dictionary containing 'inverted_index' and 'document_store'.
        filepath (str): The full path to the file where the index should be saved.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True) # Ensure directory exists
        with open(filepath, 'wb') as f:
            pickle.dump(index_data, f)
        return True
    except (pickle.PickleError, OSError, IOError) as e:
        print(f"Error saving index to {filepath}: {e}", file=sys.stderr)
        return False

def load_index(filepath):
    """
    Loads the index data from a file using pickle.

    Args:
        filepath (str): The full path to the file from which the index should be loaded.

    Returns:
        dict: The loaded index data, or None if the file does not exist or an error occurs.
    """
    if not os.path.exists(filepath):
        # print(f"Index file not found at {filepath}.", file=sys.stderr) # CLI will handle "no index" message
        return None
    try:
        with open(filepath, 'rb') as f:
            index_data = pickle.load(f)
        return index_data
    except (pickle.PickleError, OSError, IOError) as e:
        print(f"Error loading index from {filepath}: {e}", file=sys.stderr)
        return None

# The if __name__ == '__main__': block for testing will remain here,
# adapted to test save/load functionality as well.
if __name__ == '__main__':
    test_data_dir = "test_data_for_indexer"
    os.makedirs(test_data_dir, exist_ok=True)
    index_file = os.path.join(test_data_dir, "test_index.pkl")

    with open(os.path.join(test_data_dir, "doc1.txt"), "w", encoding="utf-8") as f:
        f.write("Apple is a fruit. Apple pie is delicious.")
    with open(os.path.join(test_data_dir, "doc2.txt"), "w", encoding="utf-8") as f:
        f.write("Orange is also a fruit. Oranges are good for health.")

    print(f"Building index for: {test_data_dir}")
    built_index = build_index(test_data_dir)

    if built_index:
        print(f"Saving index to: {index_file}")
        if save_index(built_index, index_file):
            print("Index saved successfully.")

            print(f"Loading index from: {index_file}")
            loaded_index = load_index(index_file)

            if loaded_index:
                print("Index loaded successfully.")
                print("\n--- Loaded Inverted Index Sample ---")
                for word in ['apple', 'fruit', 'orange']:
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

    import shutil
    shutil.rmtree(test_data_dir)
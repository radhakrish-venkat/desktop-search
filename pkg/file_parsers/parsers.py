import os
import sys
from typing import Tuple, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# File size limit (50MB) to prevent memory issues
MAX_FILE_SIZE = 50 * 1024 * 1024

try:
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pypdf not available. PDF files will be skipped.")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available. DOCX files will be skipped.")

try:
    import openpyxl
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False
    logger.warning("openpyxl not available. XLSX files will be skipped.")

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    logger.warning("python-pptx not available. PPTX files will be skipped.")

def _check_file_size(filepath: str) -> bool:
    """Check if file size is within acceptable limits."""
    try:
        size = os.path.getsize(filepath)
        return size <= MAX_FILE_SIZE
    except OSError:
        return False

def get_text_from_txt(filepath: str) -> str:
    """
    Extracts text from a plain text file (.txt).
    
    Args:
        filepath: Path to the text file
        
    Returns:
        Extracted text as string
    """
    if not _check_file_size(filepath):
        logger.warning(f"File too large: {filepath}")
        return ""
        
    try:
        # Try UTF-8 first, then fallback to other encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        logger.error(f"Could not decode text file: {filepath}")
        return ""
    except Exception as e:
        logger.error(f"Error reading TXT file {filepath}: {e}")
        return ""

def get_text_from_pdf(filepath: str) -> str:
    """
    Extracts text from a PDF file.
    
    Args:
        filepath: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    if not PDF_AVAILABLE:
        logger.warning(f"PDF support not available, skipping: {filepath}")
        return ""
        
    if not _check_file_size(filepath):
        logger.warning(f"PDF file too large: {filepath}")
        return ""
        
    text = ""
    try:
        with open(filepath, 'rb') as f:
            reader = pypdf.PdfReader(f)
            
            # Handle encrypted PDFs
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    logger.warning(f"Encrypted PDF requires password: {filepath}")
                    return ""

            # Extract text from all pages
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num} in {filepath}: {e}")
                    continue
                    
        return text.strip()
    except Exception as e:
        logger.error(f"Error reading PDF file {filepath}: {e}")
        return ""

def get_text_from_docx(filepath: str) -> str:
    """
    Extracts text from a Word document (.docx).
    
    Args:
        filepath: Path to the DOCX file
        
    Returns:
        Extracted text as string
    """
    if not DOCX_AVAILABLE:
        logger.warning(f"DOCX support not available, skipping: {filepath}")
        return ""
        
    if not _check_file_size(filepath):
        logger.warning(f"DOCX file too large: {filepath}")
        return ""
        
    text = ""
    try:
        document = Document(filepath)
        
        # Extract text from paragraphs
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                text += paragraph.text + "\n"
        
        # Remove trailing newline if present
        if text.endswith('\n'):
            text = text[:-1]
        
        # Extract text from tables
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if paragraph.text.strip():
                            text += paragraph.text + "\n"
                            
        return text.strip()
    except Exception as e:
        logger.error(f"Error reading DOCX file {filepath}: {e}")
        return ""

def get_text_from_xlsx(filepath: str) -> str:
    """
    Extracts text from an Excel workbook (.xlsx).
    
    Args:
        filepath: Path to the XLSX file
        
    Returns:
        Extracted text as string
    """
    if not XLSX_AVAILABLE:
        logger.warning(f"XLSX support not available, skipping: {filepath}")
        return ""
        
    if not _check_file_size(filepath):
        logger.warning(f"XLSX file too large: {filepath}")
        return ""
        
    text = ""
    try:
        workbook = openpyxl.load_workbook(filepath, data_only=True)
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text += f"--- Sheet: {sheet_name} ---\n"
            
            # Get the used range
            for row in sheet.iter_rows():
                row_text = []
                for cell in row:
                    if cell.value is not None:
                        row_text.append(str(cell.value))
                if row_text:
                    text += " ".join(row_text) + "\n"
                    
        return text.strip()
    except Exception as e:
        logger.error(f"Error reading XLSX file {filepath}: {e}")
        return ""

def get_text_from_pptx(filepath: str) -> str:
    """
    Extracts text from a PowerPoint presentation (.pptx).
    
    Args:
        filepath: Path to the PPTX file
        
    Returns:
        Extracted text as string
    """
    if not PPTX_AVAILABLE:
        logger.warning(f"PPTX support not available, skipping: {filepath}")
        return ""
        
    if not _check_file_size(filepath):
        logger.warning(f"PPTX file too large: {filepath}")
        return ""
        
    text = ""
    try:
        prs = Presentation(filepath)
        
        for slide_num, slide in enumerate(prs.slides):
            text += f"--- Slide {slide_num + 1} ---\n"
            
            for shape in slide.shapes:
                # Extract text from text frames
                if hasattr(shape, "text_frame") and shape.text_frame:  # type: ignore
                    text_frame = getattr(shape, "text_frame")
                    if text_frame.text.strip():
                        text += text_frame.text + "\n"
                
                # Extract text from tables
                elif hasattr(shape, "table") and shape.table:  # type: ignore
                    table = getattr(shape, "table")
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.text_frame.paragraphs:
                                if paragraph.text.strip():
                                    text += paragraph.text + "\n"
                                    
        return text.strip()
    except Exception as e:
        logger.error(f"Error reading PPTX file {filepath}: {e}")
        return ""

def get_text_from_file(filepath: str) -> Tuple[Optional[str], str]:
    """
    Dispatches to the correct text extraction function based on file extension.
    
    Args:
        filepath: Path to the file to extract text from
        
    Returns:
        Tuple of (extracted_text, file_extension)
    """
    # Check if file exists first
    if not os.path.exists(filepath):
        return None, os.path.splitext(filepath)[1].lower()
    
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    # Supported file types
    if ext in ['.txt', '.md', '.ini', '.cfg', '.conf', '.log', '.csv']:
        return get_text_from_txt(filepath), ext
    elif ext == '.pdf':
        return get_text_from_pdf(filepath), ext
    elif ext == '.docx':
        return get_text_from_docx(filepath), ext
    elif ext == '.xlsx':
        return get_text_from_xlsx(filepath), ext
    elif ext == '.pptx':
        return get_text_from_pptx(filepath), ext
    else:
        # Unsupported file type
        return None, ext

# Test function for standalone testing
if __name__ == '__main__':
    print("--- Running file_parsers.py standalone tests ---")
    
    # Test with a simple text file
    test_content = "This is a test document with some content."
    test_file = "test_document.txt"
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        text, ext = get_text_from_file(test_file)
        print(f"Test file ({ext}): {text}")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
    
    print("--- Test complete ---")
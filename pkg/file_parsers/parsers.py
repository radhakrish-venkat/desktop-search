import os
import PyPDF2
from docx import Document
import openpyxl
from pptx import Presentation
import sys # For printing errors to stderr

def get_text_from_txt(filepath):
    """
    Extracts text from a plain text file (.txt).
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading TXT file {filepath}: {e}", file=sys.stderr)
        return ""

def get_text_from_pdf(filepath):
    """
    Extracts text from a PDF file.
    Uses PyPDF2 to read text page by page.
    """
    text = ""
    try:
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # Check if the PDF is encrypted and attempt to decrypt if no password is set
            if reader.is_encrypted:
                try:
                    # An empty string might work for PDFs with no password but marked encrypted
                    reader.decrypt("")
                except PyPDF2.errors.FileDecryptionError:
                    print(f"Error: PDF file {filepath} is encrypted and requires a password.", file=sys.stderr)
                    return "" # Cannot decrypt, return empty text

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text: # Ensure there's text to add
                    text += page_text + "\n" # Add newline for better separation between pages
        return text
    except PyPDF2.errors.PdfReadError as e:
        print(f"Error reading PDF file {filepath} (corrupt or unreadable): {e}", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"Error reading PDF file {filepath}: {e}", file=sys.stderr)
        return ""

def get_text_from_docx(filepath):
    """
    Extracts text from a Word document (.docx).
    """
    text = ""
    try:
        document = Document(filepath)
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"
        # Add text from tables (basic support)
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error reading DOCX file {filepath}: {e}", file=sys.stderr)
        return ""

def get_text_from_xlsx(filepath):
    """
    Extracts text from an Excel workbook (.xlsx).
    Reads text from all sheets, cell by cell.
    """
    text = ""
    try:
        workbook = openpyxl.load_workbook(filepath)
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            text += f"--- Sheet: {sheet_name} ---\n" # Indicate sheet boundaries
            for row in sheet.iter_rows():
                row_text = []
                for cell in row:
                    if cell.value is not None:
                        row_text.append(str(cell.value))
                if row_text:
                    text += " ".join(row_text) + "\n"
        return text
    except Exception as e:
        print(f"Error reading XLSX file {filepath}: {e}", file=sys.stderr)
        return ""

def get_text_from_pptx(filepath):
    """
    Extracts text from a PowerPoint presentation (.pptx).
    Reads text from all shapes in all slides.
    """
    text = ""
    try:
        prs = Presentation(filepath)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text_frame") and shape.text_frame:
                    text += shape.text_frame.text + "\n"
                # Handle tables in PPTX (basic support)
                elif hasattr(shape, "table") and shape.table:
                    for r in shape.table.rows:
                        for c in r.cells:
                            for paragraph in c.text_frame.paragraphs:
                                text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error reading PPTX file {filepath}: {e}", file=sys.stderr)
        return ""

def get_text_from_file(filepath):
    """
    Dispatches to the correct text extraction function based on file extension.
    Returns the extracted text and the file extension (or None if not supported/error).
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()

    if ext == '.txt':
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
        # For unsupported types, return None, the indexer will skip it.
        # print(f"Unsupported file type: {filepath} (extension: {ext})", file=sys.stderr)
        return None, ext

# The if __name__ == '__main__': block for testing this module only.
if __name__ == '__main__':
    # You would typically place this test code in tests/pkg/file_parsers/test_parsers.py
    # For quick manual testing, you can use it here.

    print("--- Running file_parsers.py standalone tests ---")
    test_files_dir = "temp_parser_test_files"
    os.makedirs(test_files_dir, exist_ok=True)

    # Test .txt
    txt_path = os.path.join(test_files_dir, "sample.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("This is a plain text file.\nIt has multiple lines.\n123 numbers.")
    text, ext = get_text_from_file(txt_path)
    print(f"\nTXT File ({ext}):\n{text[:50]}...")
    os.remove(txt_path)

    # Test .docx (requires python-docx)
    try:
        from docx import Document
        docx_path = os.path.join(test_files_dir, "sample.docx")
        doc = Document()
        doc.add_paragraph("Hello from Word document.")
        table = doc.add_table(rows=1, cols=2)
        table.cell(0,0).text = "Table Header 1"
        table.cell(0,1).text = "Table Header 2"
        doc.save(docx_path)
        text, ext = get_text_from_file(docx_path)
        print(f"\nDOCX File ({ext}):\n{text[:100]}...")
        os.remove(docx_path)
    except ImportError:
        print("\nSkipping DOCX test: 'python-docx' not installed.")

    # Test .xlsx (requires openpyxl)
    try:
        import openpyxl
        xlsx_path = os.path.join(test_files_dir, "sample.xlsx")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws['A1'] = 'Product'
        ws['B1'] = 'Price'
        ws['A2'] = 'Laptop'
        ws['B2'] = 1200
        wb.save(xlsx_path)
        text, ext = get_text_from_file(xlsx_path)
        print(f"\nXLSX File ({ext}):\n{text[:100]}...")
        os.remove(xlsx_path)
    except ImportError:
        print("\nSkipping XLSX test: 'openpyxl' not installed.")

    # Test .pptx (requires python-pptx)
    try:
        from pptx import Presentation
        pptx_path = os.path.join(test_files_dir, "sample.pptx")
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = "Presentation Title"
        slide.placeholders[1].text = "Some body text here."
        prs.save(pptx_path)
        text, ext = get_text_from_file(pptx_path)
        print(f"\nPPTX File ({ext}):\n{text[:100]}...")
        os.remove(pptx_path)
    except ImportError:
        print("\nSkipping PPTX test: 'python-pptx' not installed.")

    # Test unsupported file
    unsupported_path = os.path.join(test_files_dir, "sample.xyz")
    with open(unsupported_path, "w") as f:
        f.write("This is an unsupported file.")
    text, ext = get_text_from_file(unsupported_path)
    print(f"\nUnsupported File ({ext}):\nExtracted text: {text}")
    os.remove(unsupported_path)

    # Test PDF (manual step, as creating complex PDFs programmatically is complex)
    print("\nTo test PDF: Place a 'sample.pdf' in the 'temp_parser_test_files' directory and run again.")
    pdf_path = os.path.join(test_files_dir, "sample.pdf")
    if os.path.exists(pdf_path):
        text, ext = get_text_from_file(pdf_path)
        print(f"\nPDF File ({ext}):\n{text[:200]}...")
    else:
        print("\nSkipping PDF test: 'sample.pdf' not found in test directory.")

    # Clean up test directory
    os.rmdir(test_files_dir)
    print("\n--- File Parsers Test Complete ---")
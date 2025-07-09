#!/usr/bin/env python3
"""Unit tests for file parsers module."""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the module to test
from pkg.file_parsers.parsers import (
    get_text_from_txt, get_text_from_pdf, get_text_from_docx,
    get_text_from_xlsx, get_text_from_pptx, get_text_from_file,
    _check_file_size, MAX_FILE_SIZE
)


class TestFileParsers(unittest.TestCase):
    """Test cases for file parsers."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_files = []

    def tearDown(self):
        """Clean up test fixtures."""
        for filepath in self.test_files:
            if os.path.exists(filepath):
                os.remove(filepath)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_file(self, filename, content, encoding='utf-8'):
        """Helper to create a test file."""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        self.test_files.append(filepath)
        return filepath

    def test_check_file_size(self):
        """Test file size checking functionality."""
        # Test small file
        small_file = self.create_test_file('small.txt', 'small content')
        self.assertTrue(_check_file_size(small_file))
        
        # Test large file (create a file larger than MAX_FILE_SIZE)
        large_file = os.path.join(self.test_dir, 'large.txt')
        with open(large_file, 'wb') as f:
            f.write(b'x' * (MAX_FILE_SIZE + 1024))
        self.test_files.append(large_file)
        self.assertFalse(_check_file_size(large_file))
        
        # Test non-existent file
        self.assertFalse(_check_file_size('/nonexistent/file.txt'))

    def test_get_text_from_txt(self):
        """Test text file parsing."""
        # Test basic text file
        content = "This is a test document.\nIt has multiple lines.\n123 numbers."
        filepath = self.create_test_file('test.txt', content)
        result = get_text_from_txt(filepath)
        self.assertEqual(result, content)
        
        # Test empty file
        empty_file = self.create_test_file('empty.txt', '')
        result = get_text_from_txt(empty_file)
        self.assertEqual(result, '')
        
        # Test file with special characters
        special_content = "Special chars: éñüß 你好 🚀"
        special_file = self.create_test_file('special.txt', special_content)
        result = get_text_from_txt(special_file)
        self.assertEqual(result, special_content)

    def test_get_text_from_txt_encoding_fallback(self):
        """Test text file parsing with encoding fallback."""
        # Test with latin-1 encoding
        content = "Test with latin-1: café résumé"
        filepath = os.path.join(self.test_dir, 'latin1.txt')
        with open(filepath, 'w', encoding='latin-1') as f:
            f.write(content)
        self.test_files.append(filepath)
        
        result = get_text_from_txt(filepath)
        self.assertEqual(result, content)

    def test_get_text_from_txt_large_file(self):
        """Test text file parsing with large file."""
        # Create a file that's too large
        large_file = os.path.join(self.test_dir, 'large.txt')
        with open(large_file, 'wb') as f:
            f.write(b'x' * (MAX_FILE_SIZE + 1024))
        self.test_files.append(large_file)
        
        result = get_text_from_txt(large_file)
        self.assertEqual(result, '')

    @patch('pkg.file_parsers.parsers.PDF_AVAILABLE', True)
    @patch('pkg.file_parsers.parsers.pypdf')
    def test_get_text_from_pdf(self, mock_pypdf):
        """Test PDF file parsing."""
        # Mock PDF reader
        mock_reader = MagicMock()
        mock_reader.is_encrypted = False
        mock_reader.pages = [
            MagicMock(extract_text=lambda: "Page 1 content"),
            MagicMock(extract_text=lambda: "Page 2 content")
        ]
        mock_pypdf.PdfReader.return_value = mock_reader
        
        filepath = self.create_test_file('test.pdf', 'fake pdf content')
        result = get_text_from_pdf(filepath)
        
        expected = "Page 1 content\nPage 2 content"
        self.assertEqual(result, expected)

    @patch('pkg.file_parsers.parsers.PDF_AVAILABLE', False)
    def test_get_text_from_pdf_not_available(self):
        """Test PDF parsing when PyPDF2 is not available."""
        filepath = self.create_test_file('test.pdf', 'fake content')
        result = get_text_from_pdf(filepath)
        self.assertEqual(result, '')

    @patch('pkg.file_parsers.parsers.DOCX_AVAILABLE', True)
    @patch('pkg.file_parsers.parsers.Document')
    def test_get_text_from_docx(self, mock_document):
        """Test DOCX file parsing."""
        # Mock document
        mock_doc = MagicMock()
        mock_doc.paragraphs = [
            MagicMock(text="Paragraph 1"),
            MagicMock(text="Paragraph 2"),
            MagicMock(text="")  # Empty paragraph
        ]
        mock_doc.tables = []
        mock_document.return_value = mock_doc
        
        filepath = self.create_test_file('test.docx', 'fake docx content')
        result = get_text_from_docx(filepath)
        
        expected = "Paragraph 1\nParagraph 2"
        self.assertEqual(result, expected)

    @patch('pkg.file_parsers.parsers.XLSX_AVAILABLE', True)
    @patch('pkg.file_parsers.parsers.openpyxl')
    def test_get_text_from_xlsx(self, mock_openpyxl):
        """Test XLSX file parsing."""
        # Mock workbook and worksheet
        mock_ws = MagicMock()
        mock_ws.iter_rows.return_value = [
            [MagicMock(value="A1"), MagicMock(value="B1")],
            [MagicMock(value="A2"), MagicMock(value="B2")],
            [MagicMock(value=None), MagicMock(value="B3")]
        ]
        
        mock_wb = MagicMock()
        mock_wb.sheetnames = ['Sheet1']
        mock_wb.__getitem__.return_value = mock_ws
        mock_openpyxl.load_workbook.return_value = mock_wb
        
        filepath = self.create_test_file('test.xlsx', 'fake xlsx content')
        result = get_text_from_xlsx(filepath)
        
        self.assertIn("Sheet: Sheet1", result)
        self.assertIn("A1 B1", result)
        self.assertIn("A2 B2", result)
        self.assertIn("B3", result)

    @patch('pkg.file_parsers.parsers.PPTX_AVAILABLE', True)
    @patch('pkg.file_parsers.parsers.Presentation')
    def test_get_text_from_pptx(self, mock_presentation):
        """Test PPTX file parsing."""
        # Mock presentation
        mock_shape = MagicMock()
        mock_shape.text_frame.text = "Slide content"
        mock_shape.table = None
        
        mock_slide = MagicMock()
        mock_slide.shapes = [mock_shape]
        
        mock_prs = MagicMock()
        mock_prs.slides = [mock_slide]
        mock_presentation.return_value = mock_prs
        
        filepath = self.create_test_file('test.pptx', 'fake pptx content')
        result = get_text_from_pptx(filepath)
        
        self.assertIn("Slide 1", result)
        self.assertIn("Slide content", result)

    def test_get_text_from_file_dispatch(self):
        """Test the main dispatch function."""
        # Test TXT file
        txt_file = self.create_test_file('test.txt', 'text content')
        result, ext = get_text_from_file(txt_file)
        self.assertEqual(result, 'text content')
        self.assertEqual(ext, '.txt')
        
        # Test unsupported file
        unsupported_file = self.create_test_file('test.xyz', 'unsupported content')
        result, ext = get_text_from_file(unsupported_file)
        self.assertIsNone(result)
        self.assertEqual(ext, '.xyz')

    def test_get_text_from_file_error_handling(self):
        """Test error handling in file parsing."""
        # Test non-existent file
        result, ext = get_text_from_file('/nonexistent/file.txt')
        self.assertIsNone(result)
        self.assertEqual(ext, '')  # Extension is empty for non-existent files

    def test_file_parsers_integration(self):
        """Integration test for file parsers."""
        # Create various test files
        files = [
            ('test1.txt', 'Text file content'),
            ('test2.txt', 'Another text file'),
            ('test3.xyz', 'Unsupported file type')
        ]
        
        for filename, content in files:
            filepath = self.create_test_file(filename, content)
            result, ext = get_text_from_file(filepath)
            
            if ext == '.txt':
                self.assertEqual(result, content)
            else:
                self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main() 
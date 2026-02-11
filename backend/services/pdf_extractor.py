"""
PDF Text Extraction Service
Uses pdfplumber for reliable text extraction from PDF invoices
"""

import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract all text content from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Concatenated text from all pages
    """
    text_content = ""
    
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")
    
    return text_content

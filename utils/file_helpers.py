"""
File Helper Utilities - Resume file upload and text extraction
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import pypdf
import docx


def allowed_file(filename):
    """
    Check if file extension is allowed
    
    Args:
        filename: Name of uploaded file
        
    Returns:
        True if extension is allowed, False otherwise
    """
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'docx', 'txt'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


def save_uploaded_file(file):
    """
    Save uploaded file to upload folder
    
    Args:
        file: FileStorage object from Flask request
        
    Returns:
        Full filepath where file was saved
        
    Raises:
        ValueError: If file is not allowed
    """
    if not file or file.filename == '':
        raise ValueError("No file provided")
    
    if not allowed_file(file.filename):
        raise ValueError("File type not allowed")
    
    filename = secure_filename(file.filename)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    filepath = os.path.join(upload_folder, filename)
    
    file.save(filepath)
    return filepath


def extract_text_from_file(filepath):
    """
    Extract text from uploaded resume file
    
    Args:
        filepath: Path to the resume file
        
    Returns:
        Extracted text as string
        
    Raises:
        Exception: If extraction fails
    """
    filename_lower = filepath.lower()
    
    try:
        if filename_lower.endswith('.pdf'):
            return _extract_from_pdf(filepath)
        elif filename_lower.endswith('.docx'):
            return _extract_from_docx(filepath)
        elif filename_lower.endswith('.txt'):
            return _extract_from_txt(filepath)
        else:
            raise ValueError(f"Unsupported file type: {filepath}")
            
    except Exception as e:
        current_app.logger.error(f"Error extracting text from {filepath}: {e}")
        raise


def _extract_from_pdf(filepath):
    """Extract text from PDF file"""
    text = ""
    with open(filepath, 'rb') as file:
        pdf_reader = pypdf.PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    return text


def _extract_from_docx(filepath):
    """Extract text from DOCX file"""
    doc = docx.Document(filepath)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
    return text


def _extract_from_txt(filepath):
    """Extract text from TXT file"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()


def cleanup_file(filepath):
    """
    Delete a file if it exists
    
    Args:
        filepath: Path to file to delete
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        current_app.logger.error(f"Error deleting file {filepath}: {e}")

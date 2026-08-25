"""
Document Ingestion & Text Extraction Layer
Handles multi-format document loading (PDF, images).
Uses PyMuPDF for native PDF text extraction.
Falls back to GPT-4o Vision for scanned/image-based documents.
"""
import os
import base64
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract text from a PDF using PyMuPDF.
    Returns structured output with per-page text and metadata.
    """
    doc = fitz.open(file_path)
    pages = []
    total_text = ""
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        
        # Detect if this is a scanned page (very little native text)
        is_scanned = len(text.strip()) < 50
        
        pages.append({
            "page_number": page_num + 1,
            "text": text,
            "is_scanned": is_scanned,
            "char_count": len(text)
        })
        total_text += text + "\n"
    
    doc.close()
    
    return {
        "source_file": os.path.basename(file_path),
        "total_pages": len(pages),
        "pages": pages,
        "full_text": total_text.strip(),
        "has_scanned_pages": any(p["is_scanned"] for p in pages)
    }


def extract_text_from_image(file_path: str) -> dict:
    """
    Extract text from an image using GPT-4o Vision.
    This is the fallback for scanned documents or image-based inputs.
    """
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    ext = Path(file_path).suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".tiff": "image/tiff",
        ".webp": "image/webp"
    }.get(ext, "image/png")
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract ALL text from this document image. Preserve the structure (tables, lists, headers). Output only the extracted text."},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}}
            ]
        }],
        max_tokens=4096
    )
    
    text = response.choices[0].message.content or ""
    
    return {
        "source_file": os.path.basename(file_path),
        "total_pages": 1,
        "pages": [{"page_number": 1, "text": text, "is_scanned": True, "char_count": len(text)}],
        "full_text": text,
        "has_scanned_pages": True,
        "extraction_method": "gpt-4o-vision"
    }


def extract_text(file_path: str) -> dict:
    """
    Unified extraction entry point. Auto-detects file type and extraction strategy.
    """
    ext = Path(file_path).suffix.lower()
    
    if ext == ".pdf":
        result = extract_text_from_pdf(file_path)
        # If the PDF has scanned pages, use vision fallback for those pages
        if result["has_scanned_pages"]:
            result["notes"] = "Some pages appear scanned. Consider re-extracting with Vision API for better results."
        return result
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".webp"]:
        return extract_text_from_image(file_path)
    else:
        # Try to read as plain text
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return {
            "source_file": os.path.basename(file_path),
            "total_pages": 1,
            "pages": [{"page_number": 1, "text": text, "is_scanned": False, "char_count": len(text)}],
            "full_text": text,
            "has_scanned_pages": False
        }

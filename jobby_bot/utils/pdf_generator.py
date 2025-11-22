"""ATS-friendly PDF generator using Chrome CDP method (AIHawk approach)."""

from pathlib import Path
from .chrome_pdf_generator import create_resume_pdf_chrome, create_cover_letter_pdf_chrome
from .html_content_generator import generate_resume_html, generate_cover_letter_html


def create_resume_pdf(content: str, output_path: str) -> str:
    """
    Create resume PDF using Chrome CDP method (AIHawk approach).

    This provides pixel-perfect formatting by rendering HTML in Chrome
    and using the browser's native print-to-PDF capability.

    Args:
        content: Resume content in plain text
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    # Generate HTML from plain text content
    html_content = generate_resume_html(content)

    # Convert HTML to PDF using Chrome CDP
    return create_resume_pdf_chrome(html_content, output_path)


def create_cover_letter_pdf(content: str, output_path: str) -> str:
    """
    Create cover letter PDF using Chrome CDP method.

    Args:
        content: Cover letter content in plain text
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    # Generate HTML from plain text content
    html_content = generate_cover_letter_html(content)

    # Convert HTML to PDF using Chrome CDP
    return create_cover_letter_pdf_chrome(html_content, output_path)

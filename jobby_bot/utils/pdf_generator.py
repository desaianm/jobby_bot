"""ATS-friendly PDF generator using WeasyPrint (Harvard Career Services format)."""

from pathlib import Path
from weasyprint import HTML, CSS
from .html_content_generator import generate_resume_html, generate_cover_letter_html


def create_resume_pdf(content: str, output_path: str) -> str:
    """
    Create resume PDF using WeasyPrint.

    Uses Harvard Career Services format:
    - Georgia font (professional serif)
    - Centered name with underline
    - Section headers with underlines
    - Proper bullet point alignment (hanging indent)
    - Job title LEFT, date RIGHT layout
    - Clickable hyperlinks

    Args:
        content: Resume content in plain text
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    # Generate HTML from plain text content
    html_content = generate_resume_html(content)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert HTML to PDF using WeasyPrint
    HTML(string=html_content).write_pdf(output_path)

    return output_path


def create_cover_letter_pdf(content: str, output_path: str) -> str:
    """
    Create cover letter PDF using WeasyPrint.

    Uses Harvard Career Services format:
    - Georgia font (professional serif)
    - Clean paragraph spacing
    - Proper margins (1 inch)
    - Clickable hyperlinks

    Args:
        content: Cover letter content in plain text
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    # Generate HTML from plain text content
    html_content = generate_cover_letter_html(content)

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Convert HTML to PDF using WeasyPrint
    HTML(string=html_content).write_pdf(output_path)

    return output_path

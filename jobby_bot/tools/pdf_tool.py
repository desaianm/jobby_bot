"""PDF generation tool for resume and cover letter creation."""

from typing import Literal
from claude_code_sdk import Tool, ToolResult


class GenerateResumePDF(Tool):
    """Generate a professional PDF resume from plain text content."""

    name: Literal["GenerateResumePDF"] = "GenerateResumePDF"
    description: str = """Generate a professional PDF resume from plain text content.

    Uses Harvard Career Services formatting:
    - Georgia font (professional serif)
    - Proper section headers with underlines
    - Bullet points with hanging indent
    - Job title LEFT, date RIGHT layout
    - Clickable hyperlinks for email/URLs

    Input: Plain text resume content
    Output: PDF file path
    """

    content: str
    output_path: str

    def execute(self) -> ToolResult:
        """Generate the resume PDF."""
        try:
            from jobby_bot.utils.pdf_generator import create_resume_pdf

            result_path = create_resume_pdf(self.content, self.output_path)
            return ToolResult(output=f"Resume PDF created: {result_path}")
        except Exception as e:
            return ToolResult(output=f"Error generating resume PDF: {str(e)}", is_error=True)


class GenerateCoverLetterPDF(Tool):
    """Generate a professional PDF cover letter from plain text content."""

    name: Literal["GenerateCoverLetterPDF"] = "GenerateCoverLetterPDF"
    description: str = """Generate a professional PDF cover letter from plain text content.

    Uses matching Harvard Career Services formatting:
    - Georgia font (professional serif)
    - Proper paragraph spacing
    - Clean, professional layout

    Input: Plain text cover letter content
    Output: PDF file path
    """

    content: str
    output_path: str

    def execute(self) -> ToolResult:
        """Generate the cover letter PDF."""
        try:
            from jobby_bot.utils.pdf_generator import create_cover_letter_pdf

            result_path = create_cover_letter_pdf(self.content, self.output_path)
            return ToolResult(output=f"Cover letter PDF created: {result_path}")
        except Exception as e:
            return ToolResult(output=f"Error generating cover letter PDF: {str(e)}", is_error=True)


class ConvertTextToHTML(Tool):
    """Convert plain text resume/cover letter to formatted HTML."""

    name: Literal["ConvertTextToHTML"] = "ConvertTextToHTML"
    description: str = """Convert plain text content to formatted HTML.

    Supports:
    - Resume: Parses name, contact, sections, job entries, bullets
    - Cover Letter: Parses paragraphs with proper spacing

    Returns HTML string that can be rendered or converted to PDF.
    """

    content: str
    doc_type: Literal["resume", "cover_letter"] = "resume"

    def execute(self) -> ToolResult:
        """Convert text to HTML."""
        try:
            from jobby_bot.utils.html_content_generator import (
                generate_resume_html,
                generate_cover_letter_html,
            )

            if self.doc_type == "resume":
                html = generate_resume_html(self.content)
            else:
                html = generate_cover_letter_html(self.content)

            return ToolResult(output=html)
        except Exception as e:
            return ToolResult(output=f"Error converting to HTML: {str(e)}", is_error=True)

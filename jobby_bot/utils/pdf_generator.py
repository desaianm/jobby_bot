"""Simple ATS-friendly PDF generator for resumes and cover letters."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import black
from pathlib import Path


def create_resume_pdf(content: str, output_path: str) -> str:
    """
    Create a simple, ATS-friendly resume PDF.

    Args:
        content: Resume content in plain text with sections
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    # Define simple styles
    styles = getSampleStyleSheet()

    # Custom styles for ATS compatibility
    name_style = ParagraphStyle(
        'CustomName',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=black,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    contact_style = ParagraphStyle(
        'CustomContact',
        parent=styles['Normal'],
        fontSize=10,
        textColor=black,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )

    section_header_style = ParagraphStyle(
        'CustomSectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=black,
        spaceAfter=6,
        spaceBefore=12,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderPadding=0,
        borderColor=black,
        borderRadius=0,
        backColor=None
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=black,
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=14
    )

    bullet_style = ParagraphStyle(
        'CustomBullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=black,
        spaceAfter=4,
        leftIndent=20,
        fontName='Helvetica',
        leading=14,
        bulletIndent=10
    )

    # Build the PDF content
    story = []

    # Parse content into sections
    lines = content.split('\n')
    current_section = None

    for line in lines:
        line = line.strip()

        if not line:
            story.append(Spacer(1, 0.1*inch))
            continue

        # Detect name (first non-empty line, all caps or title case)
        if not current_section and len(story) == 0:
            story.append(Paragraph(line, name_style))
            continue

        # Detect contact info (email, phone, location)
        if '@' in line or '|' in line or 'linkedin.com' in line.lower() or 'github.com' in line.lower():
            story.append(Paragraph(line, contact_style))
            continue

        # Detect section headers (ALL CAPS or specific keywords)
        if (line.isupper() or
            line.startswith('##') or
            any(keyword in line for keyword in ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 'SUMMARY', 'PROFESSIONAL', 'WORK'])):
            current_section = line.replace('#', '').strip()
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph(current_section, section_header_style))
            continue

        # Detect bullet points
        if line.startswith('•') or line.startswith('-') or line.startswith('*'):
            bullet_text = line.lstrip('•-* ').strip()
            story.append(Paragraph(f"• {bullet_text}", bullet_style))
            continue

        # Detect job title / company (contains | or dates)
        if '|' in line or any(year in line for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
            story.append(Paragraph(f"<b>{line}</b>", body_style))
            continue

        # Regular body text
        story.append(Paragraph(line, body_style))

    # Build PDF
    doc.build(story)

    return output_path


def create_cover_letter_pdf(content: str, output_path: str) -> str:
    """
    Create a simple, professional cover letter PDF.

    Args:
        content: Cover letter content in plain text
        output_path: Where to save the PDF

    Returns:
        Path to the created PDF file
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=1*inch,
        leftMargin=1*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )

    # Define styles
    styles = getSampleStyleSheet()

    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )

    date_style = ParagraphStyle(
        'CustomDate',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceAfter=20,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=16
    )

    signature_style = ParagraphStyle(
        'CustomSignature',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceAfter=6,
        spaceBefore=12,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )

    # Build content
    story = []

    lines = content.split('\n')
    in_header = True
    in_body = False

    for line in lines:
        line = line.strip()

        if not line:
            if in_body:
                story.append(Spacer(1, 0.15*inch))
            continue

        # Header section (name, contact, date)
        if in_header:
            if any(keyword in line.lower() for keyword in ['dear', 'hiring', 'manager', 'recruiter']):
                in_header = False
                in_body = True
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(line, body_style))
            elif any(char in line for char in ['@', '|']) or 'linkedin' in line.lower():
                story.append(Paragraph(line, header_style))
            elif any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']):
                story.append(Paragraph(line, date_style))
            else:
                story.append(Paragraph(line, header_style))

        # Body paragraphs
        elif in_body:
            if line.startswith('Sincerely') or line.startswith('Best regards') or line.startswith('Thank you'):
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(line, signature_style))
            else:
                story.append(Paragraph(line, body_style))

    # Build PDF
    doc.build(story)

    return output_path


def create_simple_text_pdf(text: str, output_path: str, title: str = None) -> str:
    """
    Create a very simple PDF from plain text.

    Args:
        text: Plain text content
        output_path: Where to save the PDF
        title: Optional title for the document

    Returns:
        Path to the created PDF file
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    story = []

    # Add title if provided
    if title:
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=14,
            textColor=black,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 0.3*inch))

    # Add body text
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=11,
        textColor=black,
        spaceAfter=12,
        fontName='Helvetica',
        leading=16
    )

    paragraphs = text.split('\n\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip().replace('\n', '<br/>'), body_style))

    # Build PDF
    doc.build(story)

    return output_path

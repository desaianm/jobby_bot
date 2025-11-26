"""Generate HTML content for resumes and cover letters with proper formatting."""

import re


def generate_resume_html(content: str) -> str:
    """
    Generate HTML for resume from plain text content.

    Expected input format:
    ```
    Name
    email | phone | location

    SUMMARY
    Paragraph text...

    SKILLS
    Category: skill1, skill2, skill3
    Category2: skill4, skill5

    EXPERIENCE
    Position, Company | Date Range
    - Bullet point 1
    - Bullet point 2

    EDUCATION
    Degree in Field
    Institution | Date
    GPA: X.XX

    CERTIFICATIONS
    - Cert 1 (Issuer)
    - Cert 2 (Issuer)
    ```

    Args:
        content: Resume content in plain text

    Returns:
        Complete HTML document string
    """
    lines = content.split('\n')

    html_body = []
    current_section = None  # 'summary', 'skills', 'experience', 'education', 'certifications'
    is_first_line = True
    contact_collected = False

    # Section content collectors - each section wrapped to avoid page breaks
    current_section_html = []  # Collect current section content
    current_job_html = []  # Collect current job entry (title + bullets)

    for line in lines:
        line_stripped = line.strip()

        # Skip empty lines and separators
        if not line_stripped:
            continue
        if len(line_stripped) > 20 and line_stripped.count('=') > 15:
            continue
        if len(line_stripped) > 20 and line_stripped.count('-') > 15:
            continue

        # NAME - First non-empty line
        if is_first_line:
            html_body.append(f'<h1 class="name">{line_stripped}</h1>')
            is_first_line = False
            continue

        # CONTACT INFO - Line with email or pipes (before any section header)
        if not contact_collected and current_section is None:
            if '@' in line_stripped or ('|' in line_stripped and len(line_stripped) < 100):
                # Convert email to mailto link
                contact_html = re.sub(
                    r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                    r'<a href="mailto:\1">\1</a>',
                    line_stripped
                )
                # Convert URLs to links
                contact_html = re.sub(
                    r'(https?://[^\s|]+)',
                    r'<a href="\1">\1</a>',
                    contact_html
                )
                html_body.append(f'<div class="contact">{contact_html}</div>')
                contact_collected = True
                continue

        # SECTION HEADERS - Detect and track current section
        upper_line = line_stripped.upper()
        is_section_header = False

        section_keywords = {
            'summary': ['SUMMARY', 'PROFESSIONAL SUMMARY', 'OBJECTIVE', 'PROFILE'],
            'skills': ['SKILLS', 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'COMPETENCIES'],
            'experience': ['EXPERIENCE', 'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EMPLOYMENT'],
            'education': ['EDUCATION', 'ACADEMIC'],
            'certifications': ['CERTIFICATIONS', 'CERTIFICATES', 'LICENSES', 'AWARDS', 'CREDENTIALS'],
            'projects': ['PROJECTS', 'KEY PROJECTS']
        }

        for section_type, keywords in section_keywords.items():
            if any(kw in upper_line for kw in keywords) and len(line_stripped.split()) <= 4:
                # Flush previous job entry if any
                if current_job_html:
                    current_section_html.append(f'<div class="job-entry">{"".join(current_job_html)}</div>')
                    current_job_html = []

                # Flush previous section if any
                if current_section_html:
                    html_body.append(f'<div class="section-container">{"".join(current_section_html)}</div>')
                    current_section_html = []

                current_section = section_type
                is_section_header = True

                # Start new section with header
                current_section_html.append(f'<h2 class="section">{line_stripped}</h2>')
                break

        if is_section_header:
            continue

        # SECTION-SPECIFIC FORMATTING

        # --- SUMMARY SECTION: Paragraph text ---
        if current_section == 'summary':
            current_section_html.append(f'<div class="summary-text">{line_stripped}</div>')
            continue

        # --- SKILLS SECTION: "Category: skill1, skill2, skill3" format ---
        if current_section == 'skills':
            if ':' in line_stripped:
                colon_pos = line_stripped.find(':')
                category = line_stripped[:colon_pos].strip()
                skills_text = line_stripped[colon_pos+1:].strip()
                current_section_html.append(f'<div class="skill-category"><strong>{category}:</strong> {skills_text}</div>')
            else:
                # Fallback: plain text or comma-separated without category
                current_section_html.append(f'<div class="skill-line">{line_stripped}</div>')
            continue

        # --- EXPERIENCE/PROJECTS SECTION: Job titles + bullets ---
        if current_section in ['experience', 'projects']:
            # Check if this is a JOB TITLE line (has comma and pipe with date)
            # Format: "Position, Company | Date" or "Position, Company | Present"
            if ',' in line_stripped and '|' in line_stripped and not line_stripped.startswith('-'):
                pipe_match = re.search(r'\|\s*(.+)$', line_stripped)
                if pipe_match:
                    # Flush previous job entry if starting a new one
                    if current_job_html:
                        current_section_html.append(f'<div class="job-entry">{"".join(current_job_html)}</div>')
                        current_job_html = []

                    date_part = pipe_match.group(1).strip()
                    title_part = line_stripped[:pipe_match.start()].strip().rstrip('|').strip()
                    current_job_html.append(f'<div class="job-row"><span class="job-title">{title_part}</span><span class="job-date">{date_part}</span></div>')
                    continue

            # Check if this is a job title without pipe (short line with comma)
            if ',' in line_stripped and not line_stripped.startswith('-') and len(line_stripped.split()) <= 8:
                # Flush previous job entry if starting a new one
                if current_job_html:
                    current_section_html.append(f'<div class="job-entry">{"".join(current_job_html)}</div>')
                    current_job_html = []

                current_job_html.append(f'<div class="job-row"><span class="job-title">{line_stripped}</span><span class="job-date"></span></div>')
                continue

            # Bullet points - add to current job entry
            if line_stripped.startswith('-') or line_stripped.startswith('•') or line_stripped.startswith('*'):
                bullet_text = line_stripped.lstrip('-•* ').strip()
                current_job_html.append(f'<div class="bullet"><span class="bullet-char">•</span><span class="bullet-text">{bullet_text}</span></div>')
                continue

            # Regular text in experience (treat as description)
            current_job_html.append(f'<div class="body">{line_stripped}</div>')
            continue

        # --- EDUCATION SECTION ---
        if current_section == 'education':
            # Check for institution line with pipe and date
            if '|' in line_stripped:
                pipe_match = re.search(r'\|\s*(.+)$', line_stripped)
                if pipe_match:
                    date_part = pipe_match.group(1).strip()
                    inst_part = line_stripped[:pipe_match.start()].strip().rstrip('|').strip()
                    current_section_html.append(f'<div class="edu-row"><span class="edu-inst">{inst_part}</span><span class="edu-date">{date_part}</span></div>')
                    continue

            # GPA line
            if line_stripped.upper().startswith('GPA'):
                current_section_html.append(f'<div class="edu-detail">{line_stripped}</div>')
                continue

            # Degree/program line (usually first line after header)
            current_section_html.append(f'<div class="edu-degree">{line_stripped}</div>')
            continue

        # --- CERTIFICATIONS SECTION ---
        if current_section == 'certifications':
            if line_stripped.startswith('-') or line_stripped.startswith('•') or line_stripped.startswith('*'):
                bullet_text = line_stripped.lstrip('-•* ').strip()
                current_section_html.append(f'<div class="bullet"><span class="bullet-char">•</span><span class="bullet-text">{bullet_text}</span></div>')
            else:
                current_section_html.append(f'<div class="cert-item">{line_stripped}</div>')
            continue

        # DEFAULT: Regular body text
        current_section_html.append(f'<div class="body">{line_stripped}</div>')

    # Flush any remaining job entry
    if current_job_html:
        current_section_html.append(f'<div class="job-entry">{"".join(current_job_html)}</div>')

    # Flush any remaining section
    if current_section_html:
        html_body.append(f'<div class="section-container">{"".join(current_section_html)}</div>')

    # Build complete HTML
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @page {{
            size: letter;
            margin: 0.6in 0.65in;
        }}

        body {{
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 10pt;
            line-height: 1.4;
            margin: 0;
            padding: 0;
            color: #000;
        }}

        /* NAME: 18pt Bold, centered, underlined */
        .name {{
            font-size: 18pt;
            font-weight: bold;
            text-align: center;
            margin: 0 0 4pt 0;
            padding: 0 0 4pt 0;
            border-bottom: 1px solid #000;
        }}

        /* CONTACT: 10pt, centered */
        .contact {{
            font-size: 10pt;
            text-align: center;
            margin: 4pt 0 12pt 0;
            line-height: 1.4;
        }}

        .contact a {{
            color: #0066cc;
            text-decoration: underline;
        }}

        /* SECTION HEADERS: 11pt Bold, underlined */
        .section {{
            font-size: 11pt;
            font-weight: bold;
            margin: 14pt 0 6pt 0;
            padding: 0 0 2pt 0;
            border-bottom: 1px solid #000;
        }}

        /* SUMMARY: Justified paragraph */
        .summary-text {{
            font-size: 10pt;
            line-height: 1.4;
            margin: 0 0 6pt 0;
            text-align: justify;
        }}

        /* SKILLS: Category with bold label */
        .skill-category {{
            font-size: 10pt;
            margin: 0 0 4pt 0;
            line-height: 1.4;
        }}

        .skill-line {{
            font-size: 10pt;
            margin: 0 0 4pt 0;
        }}

        /* JOB ROW: Title left, date right */
        .job-row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin: 10pt 0 4pt 0;
        }}

        .job-title {{
            font-size: 10pt;
            font-weight: bold;
        }}

        .job-date {{
            font-size: 10pt;
            font-style: italic;
        }}

        /* BULLETS: Hanging indent */
        .bullet {{
            display: flex;
            align-items: flex-start;
            font-size: 10pt;
            margin: 0 0 3pt 0;
            line-height: 1.4;
        }}

        .bullet-char {{
            flex-shrink: 0;
            width: 12pt;
            margin-right: 4pt;
        }}

        .bullet-text {{
            flex: 1;
        }}

        /* EDUCATION */
        .edu-degree {{
            font-size: 10pt;
            font-weight: bold;
            margin: 4pt 0 2pt 0;
        }}

        .edu-row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            font-size: 10pt;
            margin: 0 0 2pt 0;
        }}

        .edu-inst {{
            font-size: 10pt;
        }}

        .edu-date {{
            font-size: 10pt;
            font-style: italic;
        }}

        .edu-detail {{
            font-size: 10pt;
            margin: 0 0 2pt 0;
        }}

        /* SECTION CONTAINERS: Keep each section together on same page */
        .section-container {{
            page-break-inside: avoid;
            break-inside: avoid;
        }}

        /* JOB ENTRIES: Keep job title + bullets together */
        .job-entry {{
            page-break-inside: avoid;
            break-inside: avoid;
            margin-bottom: 4pt;
        }}

        .cert-item {{
            font-size: 10pt;
            margin: 0 0 2pt 0;
        }}

        /* BODY TEXT */
        .body {{
            font-size: 10pt;
            margin: 0 0 4pt 0;
            line-height: 1.3;
        }}
    </style>
</head>
<body>
    {''.join(html_body)}
</body>
</html>"""

    return html_content


def generate_cover_letter_html(content: str) -> str:
    """
    Generate HTML for cover letter from plain text content.

    Args:
        content: Cover letter content in plain text

    Returns:
        Complete HTML document string
    """
    lines = content.split('\n')

    html_body = []
    for line in lines:
        line_stripped = line.strip()
        if line_stripped:
            html_body.append(f'<p>{line_stripped}</p>')
        else:
            html_body.append('<div style="height: 10pt;"></div>')

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @page {{
            size: letter;
            margin: 1in;
        }}

        body {{
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 11pt;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            color: #000;
        }}

        p {{
            margin: 0 0 12pt 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    {''.join(html_body)}
</body>
</html>"""

    return html_content

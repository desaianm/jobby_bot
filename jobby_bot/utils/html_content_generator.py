"""Generate HTML content for resumes and cover letters (AIHawk approach)."""

import re


def normalize_sentence_case(text: str) -> str:
    """
    Convert ALL CAPS text to proper sentence case while preserving acronyms/names.

    Examples:
    - "BUILDING AI-POWERED SYSTEMS" -> "Building AI-powered systems"
    - "LANGCHAIN, LANGGRAPH" -> "LangChain, LangGraph"
    """
    # Common tech terms to preserve casing
    preserve_terms = {
        'AI': 'AI', 'ML': 'ML', 'API': 'API', 'REST': 'REST', 'AWS': 'AWS',
        'CI/CD': 'CI/CD', 'SQL': 'SQL', 'LANGCHAIN': 'LangChain',
        'LANGGRAPH': 'LangGraph', 'CREWAI': 'CrewAI', 'AUTOGEN': 'Autogen',
        'DSPY': 'DSPy', 'GRAPHRAG': 'GraphRAG', 'LLM': 'LLM', 'RAG': 'RAG',
        'RLHF': 'RLHF', 'PYTHON': 'Python', 'JAVASCRIPT': 'JavaScript',
        'TYPESCRIPT': 'TypeScript', 'REACT': 'React', 'ANGULAR': 'Angular',
        'DOCKER': 'Docker', 'KUBERNETES': 'Kubernetes', 'LINUX': 'Linux',
        'GITHUB': 'GitHub', 'MONGODB': 'MongoDB', 'PYTORCH': 'PyTorch',
        'TENSORFLOW': 'TensorFlow', 'PANDAS': 'Pandas', 'FASTAPI': 'FastAPI',
        'OPENAI': 'OpenAI', 'CLAUDE': 'Claude', 'CHATGPT': 'ChatGPT',
        'LLAMAINDEX': 'LlamaIndex', 'WEAVIATE': 'Weaviate', 'PINECONE': 'Pinecone',
        'MEMGPT': 'MemGPT', 'WEBSOCKETS': 'WebSockets', 'DEVOPS': 'DevOps',
        'UI': 'UI', 'UX': 'UX', 'PDF': 'PDF', 'JSON': 'JSON', 'HTTP': 'HTTP',
        'HTTPS': 'HTTPS', 'CSS': 'CSS', 'HTML': 'HTML', 'S3': 'S3',
        'EC2': 'EC2', 'LAMBDA': 'Lambda', 'SKLEARN': 'Scikit-Learn',
        'KERAS': 'Keras', 'PYDANTIC': 'Pydantic', 'STREAMLIT': 'Streamlit',
        'DATABRICKS': 'Databricks', 'COHERE': 'Cohere'
    }

    # If not all caps (has lowercase), return as-is
    if not text.isupper() or len(text) < 10:
        return text

    # Convert to title case first
    result = text.capitalize()

    # Restore preserved terms
    for term_upper, term_proper in preserve_terms.items():
        # Replace whole words only (with word boundaries)
        pattern = r'\b' + re.escape(term_upper.capitalize()) + r'\b'
        result = re.sub(pattern, term_proper, result, flags=re.IGNORECASE)

    return result


def generate_resume_html(content: str) -> str:
    """
    Generate HTML for resume from plain text content.
    Matching Resume_AI.docx style with proper bullet points.

    Args:
        content: Resume content in plain text

    Returns:
        Complete HTML document string
    """
    import re

    # Parse content
    lines = content.split('\n')

    html_body = []
    is_first_line = True
    contact_lines = []
    in_contact = False
    after_contact = False
    in_experience_section = False  # Track if we're in Work Experience
    bullet_count = 0  # Track bullets per job (limit to 3)
    MAX_BULLETS_PER_JOB = 3

    for line in lines:
        line_stripped = line.strip()

        # Skip separators
        if (len(line_stripped) > 20 and
            (line_stripped.count('=') > 20 or
             line_stripped.count('-') > 20 or
             line_stripped.count('_') > 20)):
            continue

        # Empty lines - minimal spacing
        if not line_stripped:
            continue

        # NAME - Keep original case
        if is_first_line:
            html_body.append(f'<h1 class="name">{line_stripped}</h1>')
            is_first_line = False
            in_contact = True
            continue

        # CONTACT INFO - Single line with pipe separators
        if in_contact:
            if ('@' in line_stripped or '|' in line_stripped or
                'linkedin' in line_stripped.lower() or
                'github' in line_stripped.lower()):
                contact_lines.append(line_stripped)
                continue
            else:
                # End of contact, output as single line with hyperlinks
                if contact_lines:
                    contact_text = ' | '.join(contact_lines) if len(contact_lines) > 1 else contact_lines[0]
                    # Convert URLs to hyperlinks
                    contact_text = re.sub(
                        r'(https?://[^\s|]+)',
                        r'<a href="\1">\1</a>',
                        contact_text
                    )
                    # Convert email to mailto link
                    contact_text = re.sub(
                        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                        r'<a href="mailto:\1">\1</a>',
                        contact_text
                    )
                    html_body.append(f'<div class="contact">{contact_text}</div>')
                in_contact = False
                after_contact = True

        # SECTION HEADERS - 12pt Bold
        word_count = len(line_stripped.split())
        is_header_keyword = any(kw in line_stripped.upper() for kw in
                                ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 'SUMMARY',
                                 'PROFESSIONAL SUMMARY', 'WORK EXPERIENCE', 'COMPETENCIES',
                                 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'PROFESSIONAL EXPERIENCE'])

        if word_count <= 6 and is_header_keyword:
            section_title = line_stripped.replace('#', '').strip()
            html_body.append(f'<h2 class="section">{section_title}</h2>')
            # Track if we're entering experience/projects section
            in_experience_section = any(kw in line_stripped.upper() for kw in ['EXPERIENCE', 'PROJECTS'])
            after_company_line = False
            continue

        # EXPLICIT BULLET POINTS - limit to MAX_BULLETS_PER_JOB
        if line_stripped.startswith('•') or line_stripped.startswith('-') or line_stripped.startswith('*'):
            if bullet_count < MAX_BULLETS_PER_JOB:
                bullet_text = line_stripped.lstrip('•-* ').strip()
                html_body.append(f'<div class="bullet"><span class="bullet-char">•</span><span class="bullet-text">{bullet_text}</span></div>')
                bullet_count += 1
            continue

        # JOB TITLES WITH DATES - Split into two columns, reset bullet count
        date_pattern = r'((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\d{4}\s*[-–]\s*(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|Current|Present)?\s*\d{0,4})'
        if any(year in line_stripped for year in ['2020', '2021', '2022', '2023', '2024', '2025']):
            match = re.search(date_pattern, line_stripped, re.IGNORECASE)
            if match:
                date_part = match.group(1).strip()
                title_part = line_stripped[:match.start()].strip().rstrip('-–').strip()
                if title_part:
                    html_body.append(f'<div class="job-row"><span class="job-title">{title_part}</span><span class="job-date">{date_part}</span></div>')
                    bullet_count = 0  # Reset for new job
                    continue

        # COMPANY NAME - Usually follows job title
        if any(loc in line_stripped.lower() for loc in ['toronto', 'canada', 'remote', 'new york', 'san francisco', 'university']):
            html_body.append(f'<div class="company">{line_stripped}</div>')
            after_company_line = True
            continue

        # SKILLS LINES - colon-separated key:value pairs
        if ':' in line_stripped and word_count <= 15:
            html_body.append(f'<div class="skill-line">{line_stripped}</div>')
            continue

        # ACHIEVEMENT LINES - Auto-add bullets for long sentences in experience section (limit to 3)
        if in_experience_section and len(line_stripped) > 50:
            if bullet_count < MAX_BULLETS_PER_JOB:
                html_body.append(f'<div class="bullet"><span class="bullet-char">•</span><span class="bullet-text">{line_stripped}</span></div>')
                bullet_count += 1
            continue

        # REGULAR BODY TEXT
        html_body.append(f'<div class="body">{line_stripped}</div>')

    # Build complete HTML - Clean professional resume style
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
            margin: 0;
            padding: 0;
            color: #000;
            line-height: 1.4;
            font-size: 10pt;
        }}

        /* Name: 18pt Bold, CENTERED, with underline */
        .name {{
            font-size: 18pt;
            font-weight: bold;
            margin: 0 0 4pt 0;
            padding: 0 0 4pt 0;
            text-align: center;
            color: #000;
            border-bottom: 1px solid #000;
        }}

        /* Contact: 10pt, CENTERED */
        .contact {{
            font-size: 10pt;
            margin: 4pt 0 12pt 0;
            padding: 0;
            line-height: 1.4;
            text-align: center;
            color: #000;
        }}

        /* Section Headers: 11pt Bold with underline */
        .section {{
            font-size: 11pt;
            font-weight: bold;
            margin: 12pt 0 6pt 0;
            padding: 0 0 2pt 0;
            color: #000;
            border-bottom: 1px solid #000;
        }}

        /* Job Title Row: flexbox for title LEFT, date RIGHT */
        .job-row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin: 2pt 0 2pt 0;
            padding: 0;
        }}

        /* Job Title: 10pt Bold */
        .job-title {{
            font-size: 10pt;
            font-weight: bold;
            color: #000;
        }}

        /* Job Date: 10pt, right-aligned */
        .job-date {{
            font-size: 10pt;
            color: #000;
        }}

        /* Company Row: company LEFT, location RIGHT - adds space ABOVE for separation */
        .company-row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin: 16pt 0 0 0;
            padding: 0;
        }}

        /* Company: 10pt Bold */
        .company {{
            font-size: 10pt;
            font-weight: bold;
            color: #000;
        }}

        /* Location: 10pt, right-aligned */
        .location {{
            font-size: 10pt;
            color: #000;
        }}

        /* Body Text: 10pt */
        .body {{
            font-size: 10pt;
            margin: 0 0 4pt 0;
            padding: 0;
            line-height: 1.3;
            color: #000;
        }}

        /* Bullets: flexbox for proper hanging indent */
        .bullet {{
            display: flex;
            align-items: flex-start;
            font-size: 10pt;
            margin: 0 0 6pt 0;
            line-height: 1.4;
            color: #000;
        }}

        .bullet-char {{
            flex-shrink: 0;
            width: 12pt;
            margin-right: 4pt;
        }}

        .bullet-text {{
            flex: 1;
        }}

        /* Skills line: 10pt for category:values format */
        .skill-line {{
            font-size: 10pt;
            margin: 0 0 4pt 0;
            padding: 0;
            line-height: 1.3;
            color: #000;
        }}

        /* Links: blue with underline */
        a {{
            color: #0066cc;
            text-decoration: underline;
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
    Uses Calibri to match Harvard Career Services style.

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
            font-family: Arial, Helvetica, sans-serif;
            font-size: 11pt;
            line-height: 1.15;
            margin: 0;
            padding: 0;
            color: #000;
        }}

        p {{
            margin: 0 0 10pt 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    {''.join(html_body)}
</body>
</html>"""

    return html_content

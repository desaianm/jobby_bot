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

    Args:
        content: Resume content in plain text

    Returns:
        Complete HTML document string
    """
    # Parse content
    lines = content.split('\n')

    html_body = []
    is_first_line = True
    contact_lines = []
    in_contact = False
    after_contact = False

    for line in lines:
        line_stripped = line.strip()

        # Skip separators
        if (len(line_stripped) > 20 and
            (line_stripped.count('=') > 20 or
             line_stripped.count('-') > 20 or
             line_stripped.count('_') > 20)):
            continue

        # Empty lines
        if not line_stripped:
            if after_contact and not in_contact:
                html_body.append('<div class="spacing"></div>')
            continue

        # NAME - Make it ALL CAPS
        if is_first_line:
            name_upper = line_stripped.upper()
            html_body.append(f'<h1 class="name">{name_upper}</h1>')
            is_first_line = False
            in_contact = True
            continue

        # CONTACT INFO - Collect all contact lines
        if in_contact:
            # Check if this is still contact info
            if ('@' in line_stripped or '|' in line_stripped or
                'linkedin' in line_stripped.lower() or
                'github' in line_stripped.lower() or
                'toronto' in line_stripped.lower() or
                'canada' in line_stripped.lower()):
                # Remove URLs but keep the text clean
                clean_line = line_stripped.replace('https://', '').replace('http://', '')
                contact_lines.append(clean_line)
                continue
            else:
                # End of contact, output all contact lines
                if contact_lines:
                    for contact_line in contact_lines:
                        html_body.append(f'<div class="contact">{contact_line}</div>')
                in_contact = False
                after_contact = True

        # SECTION HEADERS - Bold with underline
        # Only treat as header if it's short (< 6 words) AND contains header keywords
        word_count = len(line_stripped.split())
        is_header_keyword = any(kw in line_stripped.upper() for kw in
                                ['EXPERIENCE', 'EDUCATION', 'SKILLS', 'PROJECTS', 'SUMMARY',
                                 'PROFESSIONAL SUMMARY', 'WORK EXPERIENCE', 'COMPETENCIES',
                                 'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'PROFESSIONAL EXPERIENCE'])

        if word_count <= 6 and is_header_keyword:
            section_title = line_stripped.replace('#', '').strip()
            html_body.append(f'<h2 class="section">{section_title}</h2>')
            continue

        # BULLET POINTS - normalize if all caps
        if line_stripped.startswith('•') or line_stripped.startswith('-') or line_stripped.startswith('*'):
            bullet_text = line_stripped.lstrip('•-* ').strip()
            bullet_text = normalize_sentence_case(bullet_text)
            html_body.append(f'<div class="bullet">• {bullet_text}</div>')
            continue

        # JOB TITLES / DATES - normalize if all caps
        if '|' in line_stripped or any(year in line_stripped for year in
                                       ['2020', '2021', '2022', '2023', '2024', '2025']):
            normalized_line = normalize_sentence_case(line_stripped)
            html_body.append(f'<div class="job-title">{normalized_line}</div>')
            continue

        # REGULAR BODY TEXT - normalize if all caps
        normalized_line = normalize_sentence_case(line_stripped)
        html_body.append(f'<div class="body">{normalized_line}</div>')

    # Build complete HTML document
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @page {{
            size: letter;
            margin: 0.75in;
        }}

        body {{
            font-family: Calibri, 'Trebuchet MS', 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            color: #000;
        }}

        /* Name: Large, bold, ALL CAPS, left-aligned */
        .name {{
            font-size: 22pt;
            font-weight: bold;
            margin: 0 0 8pt 0;
            padding: 0;
            text-align: left;
            color: #000;
        }}

        /* Contact: Normal size, left-aligned, black text */
        .contact {{
            font-size: 10pt;
            margin: 0;
            padding: 0;
            line-height: 1.3;
            color: #000;
        }}

        /* Section Headers: Bold with bottom border */
        .section {{
            font-size: 12pt;
            font-weight: bold;
            margin: 12pt 0 6pt 0;
            padding: 0 0 2pt 0;
            border-bottom: 2px solid #000;
            color: #000;
            text-transform: uppercase;
        }}

        /* Job Titles: Bold */
        .job-title {{
            font-size: 10pt;
            font-weight: bold;
            margin: 6pt 0 2pt 0;
            padding: 0;
            line-height: 1.2;
            color: #000;
        }}

        /* Body Text */
        .body {{
            font-size: 10pt;
            margin: 0;
            padding: 0;
            line-height: 1.3;
            color: #000;
        }}

        /* Bullets */
        .bullet {{
            font-size: 10pt;
            margin: 0 0 0 0;
            padding: 0 0 0 20pt;
            text-indent: -20pt;
            line-height: 1.3;
            color: #000;
        }}

        /* Spacing */
        .spacing {{
            height: 6pt;
        }}

        /* Remove all link styling */
        a {{
            color: #000;
            text-decoration: none;
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
            html_body.append('<div style="height: 6pt;"></div>')

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
            font-family: Calibri, 'Trebuchet MS', 'Segoe UI', sans-serif;
            font-size: 11pt;
            line-height: 1.4;
            margin: 0;
            padding: 0;
            color: #000;
        }}

        p {{
            margin: 0 0 6pt 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    {''.join(html_body)}
</body>
</html>"""

    return html_content

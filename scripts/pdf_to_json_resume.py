#!/usr/bin/env python3
"""Convert PDF resume to JSON Resume format for Jobby Bot.

This script extracts text from a PDF resume and uses Claude to convert it
into the JSON Resume format required by Jobby Bot.

Usage:
    python scripts/pdf_to_json_resume.py path/to/resume.pdf
    python scripts/pdf_to_json_resume.py path/to/resume.pdf --output custom_resume.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber is required. Install it with: pip install pdfplumber")
    sys.exit(1)

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic is required. Install it with: pip install anthropic")
    sys.exit(1)

from dotenv import load_dotenv


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    print(f"📄 Reading PDF: {pdf_path}")

    text_content = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    text_content.append(f"--- Page {page_num} ---\n{text}")

        full_text = "\n\n".join(text_content)

        if not full_text.strip():
            print("❌ Error: No text could be extracted from the PDF")
            print("   Make sure the PDF is not scanned/image-based")
            return None

        print(f"✅ Extracted {len(full_text)} characters from {len(text_content)} pages")
        return full_text

    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return None


def convert_to_json_resume(resume_text: str, api_key: str) -> dict:
    """Use Claude to convert resume text to JSON Resume format."""
    print("\n🤖 Converting to JSON Resume format using Claude...")

    client = Anthropic(api_key=api_key)

    prompt = f"""You are a resume parser. Convert the following resume text into JSON Resume format (https://jsonresume.org/schema/).

Resume Text:
{resume_text}

Instructions:
1. Extract ALL information from the resume
2. Follow the JSON Resume schema exactly
3. Include these sections: basics, work, education, skills, projects (if any), certificates (if any)
4. For work experience, create detailed highlights (bullet points)
5. Organize skills by category (Backend, Frontend, Cloud, etc.)
6. Preserve all dates, companies, job titles, and accomplishments
7. Return ONLY valid JSON - no markdown, no explanations

JSON Resume Schema:
{{
  "basics": {{
    "name": "Full Name",
    "label": "Job Title/Role",
    "email": "email@example.com",
    "phone": "(555) 123-4567",
    "url": "https://website.com",
    "summary": "Professional summary/objective",
    "location": {{
      "city": "City",
      "region": "State/Region",
      "countryCode": "US"
    }},
    "profiles": [
      {{"network": "LinkedIn", "url": "https://linkedin.com/in/..."}},
      {{"network": "GitHub", "url": "https://github.com/..."}}
    ]
  }},
  "work": [
    {{
      "name": "Company Name",
      "position": "Job Title",
      "url": "https://company.com",
      "startDate": "2020-01",
      "endDate": "Present",
      "summary": "Brief role description",
      "highlights": [
        "Achievement or responsibility with metrics",
        "Another accomplishment"
      ]
    }}
  ],
  "education": [
    {{
      "institution": "University Name",
      "url": "https://university.edu",
      "area": "Computer Science",
      "studyType": "Bachelor of Science",
      "startDate": "2014-09",
      "endDate": "2018-05",
      "score": "3.7",
      "courses": ["Course 1", "Course 2"]
    }}
  ],
  "skills": [
    {{
      "name": "Category Name",
      "level": "Expert/Advanced/Intermediate",
      "keywords": ["Skill1", "Skill2", "Skill3"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "What the project does",
      "highlights": ["Achievement 1", "Achievement 2"],
      "keywords": ["Tech1", "Tech2"],
      "url": "https://github.com/..."
    }}
  ],
  "certificates": [
    {{
      "name": "Certification Name",
      "date": "2022-06",
      "issuer": "Issuing Organization",
      "url": "https://..."
    }}
  ]
}}

Now convert the resume above into this format. Return ONLY the JSON object."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Remove ```json or ``` from start
            response_text = response_text.split("\n", 1)[1]
            # Remove ``` from end
            response_text = response_text.rsplit("```", 1)[0]

        response_text = response_text.strip()

        # Parse JSON
        resume_json = json.loads(response_text)

        print("✅ Successfully converted to JSON Resume format")
        return resume_json

    except json.JSONDecodeError as e:
        print(f"❌ Error: Claude returned invalid JSON: {e}")
        print(f"Response: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        return None


def save_json_resume(resume_data: dict, output_path: str):
    """Save the JSON resume to a file."""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(resume_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Saved JSON resume to: {output_path}")
        print(f"\n📊 Summary:")
        print(f"   Name: {resume_data.get('basics', {}).get('name', 'N/A')}")
        print(f"   Email: {resume_data.get('basics', {}).get('email', 'N/A')}")
        print(f"   Work Experience: {len(resume_data.get('work', []))} positions")
        print(f"   Education: {len(resume_data.get('education', []))} entries")
        print(f"   Skills: {len(resume_data.get('skills', []))} categories")
        print(f"   Projects: {len(resume_data.get('projects', []))} projects")

        print("\n🎯 Next steps:")
        print(f"   1. Review the generated file: {output_path}")
        print("   2. Make any necessary corrections")
        print("   3. Use with Jobby Bot: poetry run python -m jobby_bot.agent")

        return True

    except Exception as e:
        print(f"❌ Error saving JSON file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF resume to JSON Resume format for Jobby Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert PDF and save to default location
  python scripts/pdf_to_json_resume.py my_resume.pdf

  # Convert PDF and save to custom location
  python scripts/pdf_to_json_resume.py my_resume.pdf --output custom.json

  # Convert PDF with custom API key
  ANTHROPIC_API_KEY=sk-ant-xxx python scripts/pdf_to_json_resume.py resume.pdf
        """
    )

    parser.add_argument(
        "pdf_file",
        help="Path to the PDF resume file"
    )

    parser.add_argument(
        "-o", "--output",
        default="user_data/base_resume.json",
        help="Output path for JSON resume (default: user_data/base_resume.json)"
    )

    parser.add_argument(
        "--preview-text",
        action="store_true",
        help="Preview extracted text without converting"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key and not args.preview_text:
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print("   Set it in .env file or export it:")
        print("   export ANTHROPIC_API_KEY=sk-ant-xxx")
        sys.exit(1)

    # Check if PDF file exists
    if not Path(args.pdf_file).exists():
        print(f"❌ Error: PDF file not found: {args.pdf_file}")
        sys.exit(1)

    # Extract text from PDF
    resume_text = extract_text_from_pdf(args.pdf_file)
    if not resume_text:
        sys.exit(1)

    # Preview mode - just show extracted text
    if args.preview_text:
        print("\n" + "="*60)
        print("EXTRACTED TEXT PREVIEW")
        print("="*60)
        print(resume_text)
        print("="*60)
        return

    # Convert to JSON Resume format
    resume_json = convert_to_json_resume(resume_text, api_key)
    if not resume_json:
        sys.exit(1)

    # Save to file
    if save_json_resume(resume_json, args.output):
        print("\n✅ Conversion complete!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()

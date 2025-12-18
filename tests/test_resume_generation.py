"""Test script for resume generation to verify PDF quality."""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from jobby_bot.utils.pdf_generator import create_resume_pdf
from jobby_bot.utils.html_content_generator import generate_resume_html


def load_base_resume() -> dict:
    """Load the base resume JSON."""
    resume_path = project_root / "user_data" / "base_resume.json"
    if not resume_path.exists():
        resume_path = project_root / "jobby_bot" / "user_data" / "base_resume.json"

    with open(resume_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_resume_text_from_json(resume_data: dict, job_title: str = None, company: str = None) -> str:
    """
    Generate plain text resume content from JSON Resume format.

    This simulates what the Resume Writer agent should produce.
    """
    basics = resume_data.get("basics", {})
    work = resume_data.get("work", [])
    education = resume_data.get("education", [])
    skills = resume_data.get("skills", [])
    certifications = resume_data.get("certifications", [])

    lines = []

    # Name
    lines.append(basics.get("name", "Name Not Found"))

    # Contact
    contact_parts = []
    if basics.get("email"):
        contact_parts.append(basics["email"])
    if basics.get("phone"):
        contact_parts.append(basics["phone"])
    location = basics.get("location", {})
    if location.get("city") and location.get("region"):
        contact_parts.append(f"{location['city']}, {location['region']}")
    if contact_parts:
        lines.append(" | ".join(contact_parts))

    lines.append("")

    # Summary
    lines.append("SUMMARY")
    summary = basics.get("summary", "")
    if summary:
        lines.append(summary)

    lines.append("")

    # Skills
    lines.append("SKILLS")
    for skill_category in skills:
        category_name = skill_category.get("name", "General")
        keywords = skill_category.get("keywords", [])
        if keywords:
            lines.append(f"{category_name}: {', '.join(keywords)}")

    lines.append("")

    # Experience
    lines.append("EXPERIENCE")
    lines.append("")
    for job in work:
        position = job.get("position", "Position Unknown")
        company_name = job.get("name", "Company Unknown")
        start_date = job.get("startDate", "")
        end_date = job.get("endDate", "Present")

        date_range = f"{start_date} - {end_date}" if start_date else end_date
        lines.append(f"{position}, {company_name} | {date_range}")

        # Add summary as bullet point
        summary = job.get("summary", "")
        if summary:
            lines.append(f"- {summary}")

        # Add highlights as bullet points
        highlights = job.get("highlights", [])
        for highlight in highlights:
            lines.append(f"- {highlight}")

        # If no summary or highlights, add generic bullets based on position
        if not summary and not highlights:
            lines.append(f"- Performed duties as {position}")

        lines.append("")

    # Education
    lines.append("EDUCATION")
    for edu in education:
        study_type = edu.get("studyType", "")
        area = edu.get("area", "")
        degree_line = f"{study_type}"
        if area and area.lower() not in study_type.lower():
            degree_line += f" in {area}"
        lines.append(degree_line)

        institution = edu.get("institution", "")
        end_date = edu.get("endDate", "")
        if institution:
            lines.append(f"{institution} | {end_date}")

        score = edu.get("score", "")
        if score:
            lines.append(f"GPA: {score}")

        lines.append("")

    # Certifications
    if certifications:
        lines.append("CERTIFICATIONS")
        for cert in certifications:
            name = cert.get("name", "")
            issuer = cert.get("issuer", "")
            if name:
                if issuer:
                    lines.append(f"- {name} ({issuer})")
                else:
                    lines.append(f"- {name}")

    return "\n".join(lines)


def test_resume_generation():
    """Test the full resume generation pipeline."""
    print("=" * 60)
    print("RESUME GENERATION TEST")
    print("=" * 60)

    # Create output directory
    output_dir = project_root / "output" / "resumes"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load base resume
    print("\n1. Loading base resume...")
    resume_data = load_base_resume()
    print(f"   Name: {resume_data.get('basics', {}).get('name', 'N/A')}")
    print(f"   Work entries: {len(resume_data.get('work', []))}")
    print(f"   Education entries: {len(resume_data.get('education', []))}")
    print(f"   Skills categories: {len(resume_data.get('skills', []))}")
    print(f"   Certifications: {len(resume_data.get('certifications', []))}")

    # Generate text content
    print("\n2. Generating resume text content...")
    text_content = generate_resume_text_from_json(resume_data)

    # Save text file
    txt_path = output_dir / "test_generated_resume.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text_content)
    print(f"   Saved: {txt_path}")

    # Print text content for review
    print("\n" + "-" * 40)
    print("GENERATED TEXT CONTENT:")
    print("-" * 40)
    print(text_content)
    print("-" * 40)

    # Generate HTML
    print("\n3. Generating HTML...")
    html_content = generate_resume_html(text_content)

    html_path = output_dir / "test_generated_resume.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"   Saved: {html_path}")

    # Generate PDF
    print("\n4. Generating PDF...")
    pdf_path = output_dir / "test_generated_resume.pdf"
    try:
        create_resume_pdf(text_content, str(pdf_path))
        print(f"   Saved: {pdf_path}")
        print("   PDF generation: SUCCESS")
    except Exception as e:
        print(f"   PDF generation FAILED: {e}")
        return False

    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Text file: {txt_path}")
    print(f"HTML file: {html_path}")
    print(f"PDF file:  {pdf_path}")
    print("\nOpen the PDF to verify formatting quality.")
    print("=" * 60)

    return True


def test_specific_formatting():
    """Test specific formatting scenarios that might cause issues."""
    print("\n" + "=" * 60)
    print("FORMATTING EDGE CASE TESTS")
    print("=" * 60)

    output_dir = project_root / "output" / "resumes"

    # Test case 1: Resume with missing date
    test_cases = [
        {
            "name": "missing_dates",
            "content": """John Doe
john@example.com | 555-1234 | New York, NY

SUMMARY
Experienced software engineer with 5+ years of experience.

SKILLS
Programming: Python, JavaScript, Go
Tools: Docker, Kubernetes, AWS

EXPERIENCE

Software Engineer, TechCorp | 2020 - Present
- Built scalable microservices
- Led team of 5 engineers

Junior Developer, StartupXYZ | 2018 - 2020
- Developed web applications
- Wrote unit tests

EDUCATION
Bachelor of Science in Computer Science
MIT | 2018
GPA: 3.8/4.0

CERTIFICATIONS
- AWS Solutions Architect (Amazon)
- Kubernetes Administrator (CNCF)
"""
        },
        {
            "name": "long_bullets",
            "content": """Jane Smith
jane@email.com | 123-456-7890 | San Francisco, CA

SUMMARY
Senior product manager with extensive experience leading cross-functional teams to deliver innovative solutions in the fintech space.

SKILLS
Product: Roadmapping, User Research, A/B Testing, Data Analysis
Technical: SQL, Python, Jira, Confluence, Figma

EXPERIENCE

Senior Product Manager, FinTech Inc | 2021 - Present
- Led the development and launch of a new mobile banking feature that increased user engagement by 45% and reduced customer support tickets by 30%
- Collaborated with engineering, design, and marketing teams to define product requirements and ensure successful delivery of quarterly milestones
- Conducted extensive user research including surveys, interviews, and usability testing to inform product decisions
- Managed a product backlog of 200+ items and prioritized based on business value and technical feasibility

Product Manager, eCommerce Co | 2018 - 2021
- Owned the checkout experience resulting in 15% improvement in conversion rate
- Implemented A/B testing framework for continuous experimentation

EDUCATION
MBA in Business Administration
Stanford University | 2018

CERTIFICATIONS
- Certified Scrum Product Owner (Scrum Alliance)
"""
        }
    ]

    for test_case in test_cases:
        name = test_case["name"]
        content = test_case["content"]

        print(f"\nTest case: {name}")

        txt_path = output_dir / f"test_{name}.txt"
        pdf_path = output_dir / f"test_{name}.pdf"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)

        try:
            create_resume_pdf(content, str(pdf_path))
            print(f"   PDF created: {pdf_path}")
        except Exception as e:
            print(f"   FAILED: {e}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    success = test_resume_generation()
    test_specific_formatting()

    if success:
        print("\nAll tests completed. Check output/resumes/ for generated files.")
    else:
        print("\nSome tests failed. Check errors above.")

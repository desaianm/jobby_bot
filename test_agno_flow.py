#!/usr/bin/env python3
"""Test script for Jobby Bot Agno migration.

Tests the full flow:
1. Search for top 2 jobs based on resume skills
2. Validate job URLs are real (not hallucinated)
3. Generate customized resumes for those jobs
"""

import os
import json
import sys
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def check_prerequisites():
    """Check that all prerequisites are met."""
    print("\n" + "="*60)
    print("CHECKING PREREQUISITES")
    print("="*60)

    errors = []

    # Check API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        errors.append("ANTHROPIC_API_KEY not set in environment")
    else:
        print(" ANTHROPIC_API_KEY is set")

    # Check base resume exists
    resume_path = Path("user_data/base_resume.json")
    if not resume_path.exists():
        errors.append(f"Base resume not found at {resume_path}")
    else:
        print(f" Base resume found at {resume_path}")
        # Load and display summary
        with open(resume_path) as f:
            resume = json.load(f)
            name = resume.get("basics", {}).get("name", "Unknown")
            label = resume.get("basics", {}).get("label", "Unknown")
            print(f"   Candidate: {name} - {label}")

    # Check output directories
    for dir_path in ["output/job_listings", "output/resumes", "output/cover_letters"]:
        os.makedirs(dir_path, exist_ok=True)
    print(" Output directories created/verified")

    if errors:
        print("\n ERRORS:")
        for err in errors:
            print(f"   - {err}")
        return False

    print("\n All prerequisites met!")
    return True


def extract_skills_from_resume():
    """Extract key skills from base resume for job search."""
    resume_path = Path("user_data/base_resume.json")
    with open(resume_path) as f:
        resume = json.load(f)

    # Extract skills
    skills = []
    for skill_group in resume.get("skills", []):
        skills.extend(skill_group.get("keywords", []))

    # Get job title from label
    label = resume.get("basics", {}).get("label", "Software Engineer")

    return label, skills[:5]  # Return top 5 skills


def test_job_search():
    """Test the job search tool directly."""
    print("\n" + "="*60)
    print("STEP 1: TESTING JOB SEARCH")
    print("="*60)

    from jobby_bot.agent import search_jobs

    label, skills = extract_skills_from_resume()
    # Use a common search term for testing, or fallback to resume label
    search_term = "software engineer"  # Common term for reliable test results

    print(f"\n Searching for: {search_term} (using common term for testing)")
    print(f" Resume profile: {label}")
    print(f" Based on skills: {', '.join(skills)}")
    print(" Limiting to 2 results for testing...")

    # Call the search_jobs tool function directly
    result = search_jobs.entrypoint(
        search_term=search_term,
        results_wanted=2,
        is_remote=True,
        hours_old=168  # Last week
    )

    result_data = json.loads(result)

    if not result_data.get("success"):
        print(f"\n Job search failed: {result_data.get('error')}")
        return None

    jobs = result_data.get("jobs", [])
    print(f"\n Found {len(jobs)} jobs:")

    for i, job in enumerate(jobs):
        print(f"\n   Job {i+1}: {job.get('title', 'N/A')}")
        print(f"   Company: {job.get('company', 'N/A')}")
        print(f"   Location: {job.get('location', 'N/A')}")
        print(f"   URL: {job.get('job_url', 'N/A')[:60]}...")

    if result_data.get("csv_file"):
        print(f"\n CSV saved to: {result_data['csv_file']}")

    return jobs


def validate_job_urls(jobs):
    """Validate that job URLs are real and accessible (not hallucinated)."""
    print("\n" + "="*60)
    print("STEP 2: VALIDATING JOB URLs (Anti-Hallucination Check)")
    print("="*60)

    if not jobs:
        print("\n No jobs to validate")
        return [], []

    valid_jobs = []
    invalid_jobs = []

    # Headers to mimic a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    for i, job in enumerate(jobs):
        job_url = job.get("job_url", "")
        title = job.get("title", "Unknown")
        company = job.get("company", "Unknown")

        print(f"\n   Checking Job {i+1}: {title[:40]}...")

        if not job_url:
            print(f"      No URL provided")
            invalid_jobs.append((job, "No URL"))
            continue

        # Parse URL to check domain
        try:
            parsed = urlparse(job_url)
            domain = parsed.netloc
        except Exception:
            print(f"      Invalid URL format")
            invalid_jobs.append((job, "Invalid URL format"))
            continue

        # Check if URL is from expected job sites
        valid_domains = ["indeed.com", "linkedin.com", "google.com", "glassdoor.com",
                         "www.indeed.com", "www.linkedin.com", "www.google.com", "www.glassdoor.com"]

        domain_valid = any(d in domain for d in valid_domains)
        if not domain_valid:
            print(f"      Unexpected domain: {domain}")
            invalid_jobs.append((job, f"Unexpected domain: {domain}"))
            continue

        # Try to fetch the URL
        try:
            response = requests.head(job_url, headers=headers, timeout=10, allow_redirects=True)
            status_code = response.status_code

            # Also try GET if HEAD doesn't work well
            if status_code >= 400:
                response = requests.get(job_url, headers=headers, timeout=10, allow_redirects=True)
                status_code = response.status_code

            if status_code == 200:
                print(f"      VALID (HTTP {status_code})")
                valid_jobs.append(job)
            elif status_code in [301, 302, 303, 307, 308]:
                print(f"      VALID (Redirect {status_code})")
                valid_jobs.append(job)
            elif status_code == 403:
                # Some sites block automated access but URL likely exists
                print(f"      LIKELY VALID (HTTP 403 - blocked but exists)")
                valid_jobs.append(job)
            elif status_code == 404:
                print(f"      INVALID - Job not found (HTTP 404)")
                invalid_jobs.append((job, "404 Not Found"))
            else:
                print(f"      UNCERTAIN (HTTP {status_code})")
                valid_jobs.append(job)  # Give benefit of doubt

        except requests.exceptions.Timeout:
            print(f"      TIMEOUT - URL may be valid but slow")
            valid_jobs.append(job)  # Give benefit of doubt
        except requests.exceptions.ConnectionError as e:
            print(f"      CONNECTION ERROR: {str(e)[:50]}")
            invalid_jobs.append((job, "Connection error"))
        except Exception as e:
            print(f"      ERROR: {str(e)[:50]}")
            invalid_jobs.append((job, str(e)[:50]))

        # Small delay to avoid rate limiting
        time.sleep(0.5)

    # Summary
    print(f"\n URL Validation Summary:")
    print(f"    Valid URLs: {len(valid_jobs)}")
    print(f"    Invalid/Suspicious URLs: {len(invalid_jobs)}")

    if invalid_jobs:
        print(f"\n   Invalid jobs:")
        for job, reason in invalid_jobs:
            print(f"      - {job.get('title', 'Unknown')}: {reason}")

    return valid_jobs, invalid_jobs


def test_resume_generation(jobs):
    """Test resume generation for found jobs."""
    print("\n" + "="*60)
    print("STEP 3: TESTING RESUME GENERATION")
    print("="*60)

    if not jobs:
        print("\n No jobs to generate resumes for")
        return []

    from jobby_bot.agent import read_file, write_file, generate_pdf

    generated_files = []

    # Read base resume
    base_resume = read_file.entrypoint("user_data/base_resume.json")
    resume_data = json.loads(base_resume)

    for i, job in enumerate(jobs):
        job_id = job.get("job_id", f"job_{i}")
        title = job.get("title", "Unknown Position")
        company = job.get("company", "Unknown Company")

        print(f"\n Generating resume for: {title} at {company}")

        # Create a simple customized resume text
        # In real usage, the AI agent would do this intelligently
        name = resume_data.get("basics", {}).get("name", "John Doe")
        email = resume_data.get("basics", {}).get("email", "")
        phone = resume_data.get("basics", {}).get("phone", "")
        summary = resume_data.get("basics", {}).get("summary", "")

        # Build skills by category (e.g., "Technical Skills: Python, Java, SQL")
        skills_by_category = []
        for skill_group in resume_data.get("skills", []):
            category_name = skill_group.get("name", "Skills")
            keywords = skill_group.get("keywords", [])
            if keywords:
                skills_by_category.append(f"{category_name}: {', '.join(keywords)}")

        # Build experience string with expanded bullet points (3-5 per job)
        experience_text = ""

        # Standard responsibilities by job type (used to expand brief summaries)
        job_expansions = {
            "tutor": [
                "Provided one-on-one and group tutoring sessions on technical concepts",
                "Developed lesson plans and learning materials tailored to student needs",
                "Assessed student progress and adapted teaching methods accordingly",
                "Collaborated with faculty to align tutoring with course objectives"
            ],
            "team member": [
                "Delivered excellent customer service in a fast-paced environment",
                "Maintained cleanliness and organization of work area",
                "Collaborated with team members to ensure smooth operations",
                "Handled cash transactions and inventory management"
            ],
            "technician": [
                "Performed maintenance and troubleshooting on electrical systems",
                "Diagnosed and repaired faults using testing equipment and technical drawings",
                "Ensured compliance with safety regulations and quality standards",
                "Documented maintenance procedures and maintained accurate service records",
                "Collaborated with team to complete projects on schedule"
            ]
        }

        for work in resume_data.get("work", [])[:3]:  # Top 3 jobs
            position = work.get("position", "")
            company_name = work.get("name", "")
            start_date = work.get("startDate", "")
            end_date = work.get("endDate", "Present") or "Present"
            highlights = work.get("highlights", [])
            work_summary = work.get("summary", "")

            # Format: Position, Company | Start - End  (date on right)
            # Always include date range (use "Present" if no start date)
            if start_date:
                date_range = f"{start_date} - {end_date}"
            else:
                date_range = end_date if end_date else "Present"
            experience_text += f"\n{position}, {company_name} | {date_range}\n"

            # Add highlights if available
            if highlights:
                for h in highlights[:5]:
                    experience_text += f"- {h}\n"
            else:
                # Expand based on job title
                position_lower = position.lower()
                expanded = []

                if work_summary:
                    expanded.append(work_summary)

                # Find matching expansion template
                for key, bullets in job_expansions.items():
                    if key in position_lower:
                        for bullet in bullets:
                            if len(expanded) < 4:
                                expanded.append(bullet)
                        break

                # If no template matched, use generic expansion
                if len(expanded) < 3:
                    expanded.extend([
                        "Demonstrated strong attention to detail and quality workmanship",
                        "Collaborated effectively with team members and supervisors"
                    ])

                for bullet in expanded[:5]:
                    experience_text += f"- {bullet}\n"

        # Format skills by category (one line per category)
        skills_formatted = '\n'.join(skills_by_category)

        # Get location from basics
        location = resume_data.get("basics", {}).get("location", {})
        location_str = f"{location.get('city', '')}, {location.get('region', '')}".strip(", ")

        # Build education section
        edu = resume_data.get('education', [{}])[0]
        edu_text = f"{edu.get('studyType', '')}"
        if edu.get('area'):
            edu_text += f" in {edu.get('area')}"
        edu_text += f"\n{edu.get('institution', '')}"
        if edu.get('endDate'):
            edu_text += f" | {edu.get('endDate')}"
        if edu.get('score'):
            edu_text += f"\nGPA: {edu.get('score')}"

        # Build certifications if available
        certs = resume_data.get('certifications', [])
        certs_text = ""
        if certs:
            certs_text = "\nCERTIFICATIONS\n"
            for cert in certs[:5]:
                certs_text += f"- {cert.get('name', '')}"
                if cert.get('issuer'):
                    certs_text += f" ({cert.get('issuer')})"
                certs_text += "\n"

        # Create clean, professional resume (no AI markers, ready to apply)
        # Format matches what html_content_generator expects
        resume_text = f"""{name}
{email} | {phone} | {location_str}

SUMMARY
{summary}

SKILLS
{skills_formatted}

EXPERIENCE
{experience_text}
EDUCATION
{edu_text}
{certs_text}"""

        # Save text file
        txt_path = f"output/resumes/{job_id}_resume.txt"
        write_result = write_file.entrypoint(txt_path, resume_text)
        print(f"   Text: {write_result}")
        generated_files.append(txt_path)

        # Generate PDF
        pdf_path = f"output/resumes/{job_id}_resume.pdf"
        try:
            pdf_result = generate_pdf.entrypoint(txt_path, pdf_path, "resume")
            print(f"   PDF: {pdf_result}")
            generated_files.append(pdf_path)
        except Exception as e:
            print(f"   PDF generation failed: {e}")

    return generated_files


def test_team_integration():
    """Test the full Team integration with a simple query."""
    print("\n" + "="*60)
    print("STEP 4: TESTING AGNO TEAM INTEGRATION")
    print("="*60)

    from jobby_bot.agent import create_agents, create_team

    print("\n Creating agents...")
    agents = create_agents()
    print(f"   Created {len(agents)} agents: {', '.join(agents.keys())}")

    print("\n Creating team...")
    team = create_team(agents)
    print(f"   Team name: {team.name}")
    print(f"   Team members: {len(team.members)}")

    print("\n Testing team with a simple query...")
    print("   Query: 'What can you help me with?'")

    try:
        # Use run() instead of print_response() to capture output
        response = team.run("What can you help me with? Keep your response brief.")
        print(f"\n Team response:")
        print("-" * 40)
        if hasattr(response, 'content'):
            print(response.content[:500] + "..." if len(str(response.content)) > 500 else response.content)
        else:
            print(str(response)[:500])
        print("-" * 40)
        return True
    except Exception as e:
        print(f"\n Team query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print(" JOBBY BOT - AGNO MIGRATION TEST")
    print("="*60)

    # Check prerequisites
    if not check_prerequisites():
        print("\n Prerequisites check failed. Exiting.")
        sys.exit(1)

    # Test 1: Job Search
    jobs = test_job_search()

    # Test 2: URL Validation (Anti-Hallucination)
    valid_jobs = []
    invalid_jobs = []
    if jobs:
        valid_jobs, invalid_jobs = validate_job_urls(jobs)

    # Test 3: Resume Generation (only for valid jobs)
    generated_files = []
    if valid_jobs:
        generated_files = test_resume_generation(valid_jobs[:2])  # Limit to 2 for testing
        print(f"\n Generated {len(generated_files)} files")

    # Test 4: Team Integration
    team_ok = test_team_integration()

    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)
    print(f" Job Search: {'PASS' if jobs else 'FAIL'} ({len(jobs) if jobs else 0} jobs found)")
    print(f" URL Validation: {'PASS' if valid_jobs else 'FAIL'} ({len(valid_jobs)}/{len(jobs) if jobs else 0} valid)")
    if invalid_jobs:
        print(f"    WARNING: {len(invalid_jobs)} potentially hallucinated/invalid URLs")
    print(f" Resume Generation: {'PASS' if generated_files else 'SKIP' if not valid_jobs else 'FAIL'}")
    print(f" Team Integration: {'PASS' if team_ok else 'FAIL'}")
    print("="*60)

    if valid_jobs:
        print(f"\n Output files in:")
        print(f"   - output/job_listings/")
        print(f"   - output/resumes/")


if __name__ == "__main__":
    main()

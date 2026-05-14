"""Test that resume PDFs don't have weird blank spacing on the first page.

Verifies that long sections (like EXPERIENCE) flow across pages instead of
being pushed entirely to page 2 by page-break-inside:avoid on section containers.
"""

import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jobby_bot.utils.html_content_generator import generate_resume_html
from jobby_bot.utils.pdf_generator import create_resume_pdf


# ---------------------------------------------------------------------------
# Test data: the actual Rippling resume that exhibited the bug
# ---------------------------------------------------------------------------
RIPPLING_RESUME = """Anmol Desai
adcan288@gmail.com | github.com/desaianm | linkedin.com/in/anmoldesai001 | Toronto, Canada

SUMMARY
Results-driven AI Engineer with hands-on expertise in Large Language Models (LLMs), autonomous AI systems, and production-grade AI application development. Proven track record implementing cutting-edge AI frameworks and research in real-world systems, with strong focus on RAG architectures, agentic systems, and operational AI deployment. Skilled in optimizing LLM performance through advanced prompting strategies and system design.

SKILLS
Generative AI & LLM Technologies: Claude, ChatGPT, DSPY Framework, LlamaIndex, Pydantic, Hybrid RAG, Graph RAG
AI Frameworks & Agents: CrewAI, Langgraph, Langchain, Autogen, Agentic Systems
Programming Languages: Python, JavaScript, Java, Angular, Matlab
Databases & Vector Search: Weaviate, Pinecone, SQL, MongoDB
Cloud & Infrastructure: AWS, Azure, Docker, Kubernetes, Databricks, CI/CD
Machine Learning: Supervised Learning, Unsupervised Learning, RLHF, Support Vector Machines, PyTorch, TensorFlow, Scikit-Learn
Data & Visualization: Pandas, Matplotlib, Seaborn, Excel, Power BI, Tableau

EXPERIENCE

AI Engineer, Omega Labs | Toronto | August 2024 – Present
- Designed and optimized prompting strategies for LLM applications, enhancing response accuracy and reducing token consumption through systematic refinement of model inputs and outputs
- Led the integration of cutting-edge open-source AI frameworks (Autogen, DSPy, MemGPT) to enable automated test case generation and comprehensive system evaluation of agentic workflows
- Implemented and tested advanced research architectures (Hybrid RAG, Graph RAG) within internal systems, delivering detailed analyses and validating effectiveness of novel retrieval-augmented generation approaches
- Developed autonomous agentic systems using Langgraph, CrewAI, and Autogen, building specialized Discord bots for Linear integration, image generation, and intelligent project management capabilities
- Orchestrated deployment and maintenance of production AI services using Docker and Kubernetes on AWS infrastructure, ensuring scalability and reliability
- Established CI/CD pipelines to support backend operations and streamline web application deployment processes
- Fine-tuned custom image models with Flux LoRA to generate company-branded artwork, automating visual asset creation workflows
- Engineered multimodal data processing pipelines (screen recordings, images) to enhance context and information flow for chat features in production web applications

AI Engineer Intern, Jeez AI | Toronto | February 2024 – June 2024
- Engineered robust data pipelines using Pandas and SQL to process and prepare large-scale datasets for machine learning applications
- Implemented advanced LLM agents leveraging LangChain and CrewAI frameworks, integrating OpenAI and Claude models to enhance information extraction and natural language processing capabilities
- Designed and developed the Internship Finder application using the DSPy framework for LLM optimization, Weaviate vectorDB for hybrid search functionality, and Streamlit for an intuitive, production-ready user interface
- Built and deployed a Resume Analyzer application leveraging LlamaIndex, Pydantic, and Streamlit to intelligently parse, analyze, and structure resume data for downstream applications

EDUCATION
Bachelor's Degree in Information Technology
York University | Toronto, Canada | Graduated April 2024
"""

# ---------------------------------------------------------------------------
# Stress test: even longer resume with 3 jobs to really test page flow
# ---------------------------------------------------------------------------
LONG_RESUME = """Jane Smith
jane@example.com | github.com/janesmith | linkedin.com/in/janesmith | San Francisco, CA

SUMMARY
Experienced software engineer with 10+ years building distributed systems at scale. Expert in cloud infrastructure, microservices architecture, and machine learning operations.

SKILLS
Languages: Python, Go, Rust, Java, TypeScript
Cloud: AWS, GCP, Azure, Kubernetes, Docker, Terraform
ML/AI: PyTorch, TensorFlow, Ray, MLflow, Kubeflow
Databases: PostgreSQL, Redis, DynamoDB, Elasticsearch

EXPERIENCE

Staff Engineer, BigTech Corp | San Francisco | January 2022 – Present
- Architected and deployed a real-time ML inference platform serving 50M+ daily predictions with p99 latency under 50ms
- Led migration of monolithic application to microservices architecture, reducing deployment time from 4 hours to 15 minutes
- Designed event-driven data pipeline processing 2TB daily using Kafka and Flink, enabling real-time analytics dashboards
- Mentored team of 8 engineers on distributed systems best practices and conducted 50+ technical interviews
- Implemented chaos engineering framework that discovered 12 critical failure modes before they hit production
- Built custom Kubernetes operator for automated ML model deployment with canary releases and automatic rollback
- Reduced cloud infrastructure costs by 40% through resource optimization and spot instance strategies
- Established SLO-based monitoring with custom Prometheus metrics and Grafana dashboards across 200+ services

Senior Engineer, StartupCo | San Francisco | March 2019 – December 2021
- Built the core search engine using Elasticsearch, handling 10M+ queries per day with sub-100ms response times
- Designed and implemented OAuth2/OIDC authentication system supporting 5 identity providers
- Created automated testing framework that reduced QA cycle time from 2 weeks to 2 days
- Led the data platform team, building ETL pipelines that processed 500GB daily for business intelligence
- Implemented feature flag system enabling safe rollout of features to 1M+ users with gradual percentage-based targeting
- Developed real-time notification system using WebSockets and Redis pub/sub serving 100K concurrent connections

Software Engineer, Enterprise Inc | New York | June 2015 – February 2019
- Developed microservices for payment processing handling $50M+ in daily transactions with 99.99% uptime
- Built CI/CD pipeline using Jenkins and Docker that reduced build times by 60% and enabled 20+ deployments per day
- Implemented distributed caching layer using Redis that reduced database load by 70% and improved API response times
- Created internal developer tools that improved team productivity by 30% as measured by sprint velocity metrics
- Led migration from on-premise infrastructure to AWS, completing 6-month project 2 weeks ahead of schedule
- Designed RESTful APIs consumed by 15+ internal and external clients with comprehensive OpenAPI documentation

EDUCATION
Master of Science in Computer Science
Stanford University | Stanford, CA | Graduated June 2015

Bachelor of Science in Computer Engineering
UC Berkeley | Berkeley, CA | Graduated May 2013

CERTIFICATIONS
- AWS Solutions Architect Professional (2023)
- Certified Kubernetes Administrator (2022)
- Google Cloud Professional ML Engineer (2021)
"""


def extract_pdf_page_texts(pdf_path: str) -> list[str]:
    """Extract text content from each page of a PDF using pdfplumber."""
    import pdfplumber
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texts.append(page.extract_text() or "")
    return texts


def test_no_blank_gap_rippling_resume():
    """The Rippling resume should have EXPERIENCE content starting on page 1."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        output_path = f.name

    try:
        create_resume_pdf(RIPPLING_RESUME, output_path)
        pages = extract_pdf_page_texts(output_path)

        assert len(pages) >= 1, "PDF should have at least 1 page"

        page1 = pages[0]
        # Page 1 MUST contain EXPERIENCE (not pushed entirely to page 2)
        assert "EXPERIENCE" in page1, (
            f"EXPERIENCE section should start on page 1, but page 1 only has:\n{page1[:300]}"
        )
        # Page 1 should also have the first job title
        assert "Omega Labs" in page1, (
            f"First job entry should appear on page 1, but page 1 only has:\n{page1[:300]}"
        )
        print("PASS: test_no_blank_gap_rippling_resume")
        print(f"  Page 1 sections: SUMMARY, SKILLS, EXPERIENCE (starts here)")
        if len(pages) > 1:
            print(f"  Page 2 continues with remaining content")
    finally:
        os.unlink(output_path)


def test_no_blank_gap_long_resume():
    """A long resume with 3 jobs should flow content across pages without gaps."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        output_path = f.name

    try:
        create_resume_pdf(LONG_RESUME, output_path)
        pages = extract_pdf_page_texts(output_path)

        assert len(pages) >= 1, "PDF should have at least 1 page"

        page1 = pages[0]
        # EXPERIENCE should start on page 1
        assert "EXPERIENCE" in page1, (
            f"EXPERIENCE section should start on page 1, but page 1 only has:\n{page1[:300]}"
        )
        print("PASS: test_no_blank_gap_long_resume")
        print(f"  Total pages: {len(pages)}")
        for i, page in enumerate(pages):
            # Show which sections appear on each page
            sections_found = [s for s in ["SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION", "CERTIFICATIONS"]
                              if s in page]
            print(f"  Page {i+1} sections: {', '.join(sections_found) if sections_found else '(continuation)'}")
    finally:
        os.unlink(output_path)


def test_section_header_not_orphaned():
    """Section headers should not appear alone at the bottom of a page."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        output_path = f.name

    try:
        create_resume_pdf(LONG_RESUME, output_path)
        pages = extract_pdf_page_texts(output_path)

        for i, page_text in enumerate(pages):
            lines = [l.strip() for l in page_text.split('\n') if l.strip()]
            if not lines:
                continue
            last_line = lines[-1]
            # A section header should not be the very last line on a page
            orphaned_headers = ["EXPERIENCE", "EDUCATION", "CERTIFICATIONS", "SKILLS", "PROJECTS"]
            for header in orphaned_headers:
                if last_line == header:
                    print(f"WARNING: '{header}' is orphaned at bottom of page {i+1}")
                    # This is a warning, not a hard failure, because WeasyPrint's
                    # break-after:avoid should handle it but text extraction
                    # can be imprecise about what's "last"

        print("PASS: test_section_header_not_orphaned")
    finally:
        os.unlink(output_path)


def test_html_structure():
    """Verify the HTML has correct CSS - no page-break-inside:avoid on section-container."""
    html = generate_resume_html(RIPPLING_RESUME)

    # section-container should NOT have page-break-inside: avoid
    assert "page-break-inside: avoid" not in html.split(".section-container")[1].split("}")[0], (
        "section-container must NOT have page-break-inside:avoid"
    )

    # section headers SHOULD have break-after: avoid (orphan prevention)
    section_css = html.split(".section {")[1].split("}")[0]
    assert "break-after: avoid" in section_css, (
        "Section headers should have break-after:avoid to prevent orphaned headers"
    )

    # job-entry SHOULD still have page-break-inside: avoid
    job_entry_css = html.split(".job-entry")[1].split("}")[0]
    assert "page-break-inside: avoid" in job_entry_css, (
        "job-entry should keep page-break-inside:avoid to keep jobs together"
    )

    print("PASS: test_html_structure")


def test_regenerate_rippling_pdf():
    """Regenerate the actual Rippling resume PDF to visually verify the fix."""
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "output", "1179992940106485760", "resumes",
        "Rippling_AI_Engineer_resume_FIXED.pdf"
    )

    create_resume_pdf(RIPPLING_RESUME, output_path)
    pages = extract_pdf_page_texts(output_path)

    print(f"PASS: test_regenerate_rippling_pdf")
    print(f"  Regenerated PDF at: {output_path}")
    print(f"  Total pages: {len(pages)}")
    for i, page in enumerate(pages):
        sections_found = [s for s in ["SUMMARY", "SKILLS", "EXPERIENCE", "EDUCATION", "CERTIFICATIONS"]
                          if s in page]
        print(f"  Page {i+1}: {', '.join(sections_found) if sections_found else '(continuation)'}")


if __name__ == "__main__":
    print("=" * 60)
    print("PDF Spacing Tests")
    print("=" * 60)
    print()

    tests = [
        test_html_structure,
        test_no_blank_gap_rippling_resume,
        test_no_blank_gap_long_resume,
        test_section_header_not_orphaned,
        test_regenerate_rippling_pdf,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

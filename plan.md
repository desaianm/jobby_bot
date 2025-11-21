
- Job Application Multi Agent system

Goal: Automate the entire job application process from searching to submitting applications.

- Job Finder Agent( Web tools + jobspsy access)
- Resume Writer Agent (writing tools, for pdf rewriting using latex support)
- Notion Agent (notion db access for storing job applications to apply)
    saves job title, link, description, apply status, resume file, cover letter
- Uses Latest AI models from claude : `claude-haiku-4-5-20251001` (cheap and fast) 
- best for agentic workflows: `claude-sonnet-4-5-20250929` (balanced performance and expensive cost)
- Job Application Agent, applies to jobs in the notion db

use claude agent sdk like how research-agent uses.


use this as tool in the job finder agent.
- JobSpy: `pip install -U python-jobspy` 
 ```
 import csv
from jobspy import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "google"], # "glassdoor", "bayt", "naukri", "bdjobs"
    search_term="software engineer",
    google_search_term="software engineer jobs near San Francisco, CA since yesterday",
    location="San Francisco, CA",
    results_wanted=20,
    hours_old=72,
    country_indeed='USA',
    
    # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
)
print(f"Found {len(jobs)} jobs")
print(jobs.head())
jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False) # to_excel
  ```

- Use Claude Agent SDK for all agents, similar to research-agent pattern.
  - Each agent should be a separate class inheriting from ClaudeAgent
  - use xml tags and mirror prompts given there for subagents, including proper formatting.


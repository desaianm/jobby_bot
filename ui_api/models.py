"""Pydantic models for Job Ops UI API."""

from typing import Optional

from pydantic import BaseModel, Field


class Job(BaseModel):
    id: int
    external_id: Optional[str] = None
    title: str
    company: str
    location: Optional[str] = None
    job_url: Optional[str] = None
    site: Optional[str] = None
    date_posted: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None
    status: str  # discovered | ready | applied | interview | rejected | offer
    fit_score: Optional[int] = Field(default=None, ge=0, le=100)
    fit_assessment: Optional[str] = None
    tailored_summary: Optional[str] = None
    resume_path: Optional[str] = None
    cover_letter_path: Optional[str] = None
    created_at: Optional[str] = None
    status_updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class JobUpdate(BaseModel):
    """Fields that the UI can mutate on a job record."""

    status: Optional[str] = Field(
        default=None, pattern="^(discovered|ready|applied|interview|rejected|offer|archived)$"
    )
    fit_score: Optional[int] = Field(default=None, ge=0, le=100)
    fit_assessment: Optional[str] = None
    tailored_summary: Optional[str] = None


class PipelineRequest(BaseModel):
    """Parameters for a job-search pipeline run."""

    search_term: str = Field(..., min_length=1, description="Job title / keywords")
    location: Optional[str] = Field(default="", description="City, state, or country")
    is_remote: Optional[bool] = Field(default=False, description="Remote jobs only")
    results_wanted: Optional[int] = Field(
        default=20, ge=1, le=200, description="Max results per site"
    )
    hours_old: Optional[int] = Field(
        default=72, ge=1, description="Only return jobs posted within this many hours"
    )
    country_indeed: Optional[str] = Field(
        default="Canada", description="Country for Indeed/Glassdoor (e.g. Canada, USA)"
    )


class PipelineResponse(BaseModel):
    success: bool
    jobs_found: int
    jobs_inserted: int
    jobs: list[Job]


class StatsResponse(BaseModel):
    discovered: int
    ready: int
    applied: int
    interview: int
    rejected: int
    offer: int
    total: int

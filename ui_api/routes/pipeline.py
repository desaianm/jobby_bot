"""Pipeline route — runs a job search via the jobby_bot search_jobs tool."""

import json
import logging

from fastapi import APIRouter, HTTPException

from ui_api.database import get_jobs, insert_jobs
from ui_api.models import Job, PipelineRequest, PipelineResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


def _clean(val: object) -> str:
    """Convert a value to string, treating NaN/None as empty."""
    s = str(val) if val is not None else ""
    return "" if s.lower() in ("nan", "none", "null") else s


def _search_and_map(req: PipelineRequest) -> list[dict]:
    """Call jobby_bot's search_jobs tool and map results to insert_jobs format."""
    try:
        from jobby_bot.agent import search_jobs
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="jobby_bot package not found. Ensure it is installed.",
        ) from exc

    try:
        result_json = search_jobs.entrypoint(
            search_term=req.search_term,
            location=req.location or "",
            is_remote=req.is_remote,
            results_wanted=req.results_wanted,
            hours_old=req.hours_old,
            country_indeed=req.country_indeed or "Canada",
        )
    except Exception as exc:
        logger.exception("search_jobs failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Job search failed: {exc}") from exc

    result = json.loads(result_json)

    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=f"Job search error: {result.get('error', 'unknown')}",
        )

    # Map search_jobs output fields → insert_jobs expected fields
    mapped = []
    for job in result.get("jobs", []):
        mapped.append({
            "id": _clean(job.get("job_id", "")),
            "title": _clean(job.get("title", "")),
            "company": _clean(job.get("company", "")),
            "location": _clean(job.get("location", "")),
            "job_url": _clean(job.get("job_url", "")),
            "site": _clean(job.get("site", "")),
            "date_posted": _clean(job.get("date_posted", "")),
            "description": _clean(job.get("description") or job.get("description_preview") or ""),
            "salary": _clean(job.get("salary", "")),
        })

    return mapped


@router.post("/run", response_model=PipelineResponse, summary="Run job search pipeline")
def run_pipeline(req: PipelineRequest) -> PipelineResponse:
    """Search for real jobs via jobby_bot and persist them to the database."""
    raw_jobs = _search_and_map(req)
    jobs_found = len(raw_jobs)

    jobs_inserted = insert_jobs(raw_jobs)

    all_discovered = get_jobs(status="discovered")
    returned_jobs = all_discovered[:jobs_inserted] if jobs_inserted else []

    return PipelineResponse(
        success=True,
        jobs_found=jobs_found,
        jobs_inserted=jobs_inserted,
        jobs=[Job(**row) for row in returned_jobs],
    )

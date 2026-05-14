"""Job CRUD routes for Job Ops UI API."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ui_api.database import (
    get_job,
    get_job_counts,
    get_jobs,
    update_job_fields,
)
from ui_api.models import Job, JobUpdate, StatsResponse

router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs", response_model=list[Job], summary="List jobs")
def list_jobs(
    status: Optional[str] = Query(
        default=None,
        description="Filter by status: discovered | ready | applied | all",
    )
) -> list[Job]:
    """Return all jobs, optionally filtered by status.

    Pass `status=all` (or omit the parameter) to return every job.
    """
    effective_status = None if (status is None or status == "all") else status
    rows = get_jobs(status=effective_status)
    return [Job(**row) for row in rows]


@router.get("/jobs/{job_id}", response_model=Job, summary="Get a single job")
def get_single_job(job_id: int) -> Job:
    """Return one job by its integer ID."""
    row = get_job(job_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return Job(**row)


@router.patch("/jobs/{job_id}", response_model=Job, summary="Update a job")
def patch_job(job_id: int, payload: JobUpdate) -> Job:
    """Partially update a job record.

    Only the fields present in the request body are written; omitted fields
    are left unchanged.
    """
    # Gather only the fields that were explicitly set in the payload
    updates = payload.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update.")

    try:
        updated = update_job_fields(job_id, **updates)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    row = get_job(job_id)
    return Job(**row)


@router.get("/stats", response_model=StatsResponse, summary="Job counts by status")
def get_stats() -> StatsResponse:
    """Return the number of jobs in each status bucket plus a grand total."""
    counts = get_job_counts()
    return StatsResponse(**counts)

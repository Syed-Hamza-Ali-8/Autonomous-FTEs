"""API routers for the Candidate Screening Agent."""

from .candidates import router as candidates_router
from .approvals import router as approvals_router
from .jobs import router as jobs_router
from .applications import router as applications_router

__all__ = ["candidates_router", "approvals_router", "jobs_router", "applications_router"]

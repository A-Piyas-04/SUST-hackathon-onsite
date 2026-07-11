"""Uvicorn entry shim.

Run from the backend directory:

    uvicorn main:app --reload

Equivalent to:

    uvicorn app.main:app --reload
"""

from app.main import app

__all__ = ["app"]

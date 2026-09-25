from __future__ import annotations

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    message: str
    rows_loaded: int
    filename: str


class DateFilter(BaseModel):
    start_date: str | None = None
    end_date: str | None = None
    category: str | None = None

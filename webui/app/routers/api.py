"""
API router combining dataset and task endpoints
Author: Cascade (AI assistant)

Provides lightweight endpoints for:
- GET /api/datasets
- GET /api/tasks?dataset=training&search=abc&limit=100&offset=0

Phase 0: discovery only, no runs yet.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ..services.dataset_service import list_datasets, list_tasks

api_router = APIRouter()


@api_router.get("/datasets", response_model=List[str])
def get_datasets() -> List[str]:
    datasets = list_datasets()
    if not datasets:
        # Helpful message if dataset root is misconfigured
        raise HTTPException(status_code=404, detail="No datasets found. Check DATASET_ROOT in .env")
    return datasets


@api_router.get("/tasks")
def get_tasks(
    dataset: str = Query(..., description="Dataset name, e.g., 'training' or 'evaluation'"),
    search: Optional[str] = Query(None, description="Optional search filter (substring match on filename)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    if dataset not in list_datasets():
        raise HTTPException(status_code=400, detail=f"Unknown dataset: {dataset}")
    items = list_tasks(dataset=dataset, search=search, limit=limit, offset=offset)
    return items

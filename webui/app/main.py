"""
FastAPI application entrypoint for saturn-arc WebUI
Author: Cascade (AI assistant)

What this file does:
- Creates the FastAPI app and configures templating (Jinja2)
- Includes API routers for datasets and tasks
- Serves a simple home page to browse/filter tasks from ARC-AGI-2/data
- Reads settings from .env (e.g., DATASET_ROOT, WEB_CONCURRENCY)

Notes:
- This Phase 0 scaffold focuses on dataset/task discovery only.
- No solver runs or DB usage yet (added in Phase 1).
"""

import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .routers.api import api_router
from .services.dataset_service import list_datasets

# Create app
app = FastAPI(title="saturn-arc WebUI", version="0.1.0")

# Templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Static (optional placeholder if we add CSS/JS later)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# API routers
app.include_router(api_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the home page with dataset options and a simple task filter/search UI.
    """
    datasets = list_datasets()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "datasets": datasets}
    )

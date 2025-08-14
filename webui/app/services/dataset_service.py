"""
Dataset and task discovery utilities for saturn-arc WebUI
Author: Cascade (AI assistant)

This module provides functions to:
- Resolve the dataset root directory (from .env or default)
- List available datasets (subdirectories)
- List tasks (JSON files) with simple filtering and pagination

Defaults are hobbyist-friendly and Windows-aware.
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env if present (project root)
load_dotenv()

# Default relative dataset root (from repo root)
DEFAULT_DATASET_ROOT = os.path.join("ARC-AGI-2", "data")


def project_root() -> str:
    """Return absolute path to the repo root based on this file location."""
    # webui/app/services/dataset_service.py -> go up 3 levels to repo root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def dataset_root() -> str:
    """Resolve dataset root from env or use default under the repo root."""
    root = os.getenv("DATASET_ROOT", DEFAULT_DATASET_ROOT)
    if not os.path.isabs(root):
        root = os.path.join(project_root(), root)
    return root


def list_datasets() -> List[str]:
    """Return dataset directory names (e.g., ['training', 'evaluation']) present under the dataset root."""
    root = dataset_root()
    if not os.path.isdir(root):
        return []
    names = []
    for entry in os.listdir(root):
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            names.append(entry)
    # Prefer training/evaluation order
    names_sorted = sorted(names, key=lambda n: {"training": 0, "evaluation": 1}.get(n, 99))
    return names_sorted


def list_tasks(dataset: str, search: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, str]]:
    """
    List task JSON files for a dataset with optional substring search and pagination.
    Returns: list of { name: <stem>, path: <absolute path> }
    """
    root = dataset_root()
    ds_dir = os.path.join(root, dataset)
    if not os.path.isdir(ds_dir):
        return []

    files = [f for f in os.listdir(ds_dir) if f.lower().endswith('.json')]
    # Simple substring filter
    if search:
        s = search.lower()
        files = [f for f in files if s in f.lower()]

    files.sort()
    sliced = files[offset: offset + limit]

    items: List[Dict[str, str]] = []
    for filename in sliced:
        name = os.path.splitext(filename)[0]
        items.append({
            "name": name,
            "path": os.path.join(ds_dir, filename)
        })
    return items

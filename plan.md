# WebUI Implementation Plan for saturn-arc

Author: GPT-5 (medium reasoning)

Purpose: This plan outlines how we will add a simple, effective Web UI to operate the existing ARC-AGI visual solver without disrupting core code. It focuses on usability, observability, saving and exporting results, and persisting them in a database.


## Goals

- Make it easy to run a single task or a batch from the browser.
- Visualize inputs, outputs, predictions, and intermediate images produced in `img_tmp/`.
- Persist run metadata and artifacts in a local database (SQLite first, optional Postgres later).
- Export runs (ZIP with JSON metadata + images) and aggregated CSV summaries.
- Keep the core solver unchanged; integrate via a thin backend wrapper.
- Windows-friendly install and run experience; no heavy FE toolchain required for v1.
- Allow users to browse, filter, and select puzzles directly from `ARC-AGI-2/data/`.


## Scope (Phased)

- Phase 1 (MVP): Single-task run UI, dataset/task picker with filters from `ARC-AGI-2/data/`, run history, run detail view, export one run as ZIP/JSON, CSV of runs, SQLite persistence, env-based API keys.
- Phase 2: Batch runs (parallel workers), bulk export, simple compare view (predicted vs actual), cancellation if queued.
- Phase 3: Observability & UX: live logs/streaming status, thumbnails for images, filtering by status/success, tagging, notes, and cost controls (concurrency limit, rate limit, optional cost capture).
- Phase 4: Packaging: one command to launch web app on Windows, optional Docker, optional Postgres.


## Architecture Overview

- Backend: Node.js web service (Express) to:
  - Invoke the Python solver via a child process (Phase 1): spawn Python to run a small runner script that calls `ARCVisualSolver` and returns JSON.
  - Manage a lightweight in-process job queue (in-memory) with configurable concurrency (default 5 via `WEB_CONCURRENCY`).
  - Persist runs and artifact metadata in SQLite using a Node driver (better-sqlite3 or sqlite3, see Data Model).
  - Serve server-rendered UI (EJS templates) for easy Windows setup.
  - Provide JSON REST endpoints for automation.
- Frontend: Server-rendered HTML (EJS) + minimal JS. No SPA build step for v1.
- Storage:
  - Images: continue using `img_tmp/` with file names including `task_name` and image roles.
  - DB: `webui-node/webui_data/app.db` (SQLite). Optional Postgres later.
  - Exports: `webui-node/webui_data/exports/` for ZIP/CSV.
- Configuration: `.env` for secrets and settings (e.g., `OPENAI_API_KEY`, `DATASET_ROOT`, `WEB_CONCURRENCY`, `PORT`). Default concurrency is 5.


## Integration Points (existing code)

- `arc_visual_solver.py` → class `ARCVisualSolver`:
  - We will create a small Python runner script that imports `ARCVisualSolver` and runs `solve(<task_json_path>)`, then prints a JSON summary to stdout.
  - Node will spawn this runner via `child_process.spawn` (Phase 1). The solver will continue saving images to `img_tmp/`.
- `run_batch.py`:
  - Reuse its dataset discovery approach (list JSON files under `ARC-AGI-2/data/<dataset>/`). Batch submission logic will live in the Node backend.
- `arc_visualizer.py`/`arc_stdin_visualizer.py`:
  - No changes needed; optional future utilities for visualization.


## Core Features & Pages (v1)

- Dashboard
  - List recent runs with status, task name, dataset, success flag, duration, phases.
  - Filters: status (queued/running/success/fail), dataset, task name search.
- New Run
  - Dataset picker: training/evaluation.
  - Task picker: list available `.json` tasks.
  - Options: cell size (read-only for v1), concurrency cap (global), run notes.
- Run Detail
  - Status, timestamps, duration, success, phases, logs (tail), response summary.
  - Images: thumbnails linking to full-size images in `img_tmp/` (train*, test_input, test_output if present, prediction).
  - Actions: export this run (ZIP), download metadata JSON, copy paths.
- Exports
  - Download CSV summary of runs (id, dataset, task, status, success, time, phases, prediction dims, image paths).
  - Bulk export selection as ZIPs.


## REST API (v1)

- GET /api/datasets → { datasets: ["training", "evaluation"] }
- GET /api/tasks?dataset=training&search=abc&limit=100&offset=0 → [{ name, path }]
- POST /api/runs → { dataset, task_name, task_path, notes } → { run_id }
- GET /api/runs → list with filters
- GET /api/runs/{id} → run metadata + status
- GET /api/runs/{id}/artifacts → list of artifact file paths and types
- POST /api/runs/{id}/export → produce ZIP, return path
- GET /api/exports/runs.csv → CSV of runs


## Data Model (SQLite via better-sqlite3 or sqlite3 on Node)

- Run
  - id (uuid)
  - created_at, started_at, finished_at
  - dataset (training/evaluation)
  - task_name, task_path
  - status (queued/running/success/fail)
  - success (bool)
  - duration_seconds (float)
  - phases (int)
  - prediction_rows (int), prediction_cols (int)
  - notes (text)
  - error_message (text)
- Artifact
  - id (uuid)
  - run_id (fk)
  - type (train_input, train_output, test_input, test_output, tool, final_prediction, other)
  - file_path (string)
  - label (string)
- Setting (optional for v2)
  - key, value (string) for toggles like concurrency, rate limiting


## Job Execution Model

- In-process queue in Node with a fixed worker concurrency (`WEB_CONCURRENCY`, default 5).
- Each job:
  - Validates the task JSON path and dataset membership.
  - Creates a DB Run entry (status=queued → running), timestamps `started_at`.
  - Spawns Python runner to invoke `ARCVisualSolver` with the task path.
  - Parses JSON result, infers prediction dimensions, scans `img_tmp/` for files matching `task_name_*` produced during the run, and records them as Artifacts.
  - Captures stdout/stderr to a per-run log file; stores a short summary snippet in DB.
  - Updates status/success/`finished_at`/duration.


## Exports

- Single run export: ZIP containing:
  - run.json (all run metadata)
  - artifacts/ (copied images)
- CSV export: aggregate over selected runs or all runs.
- Paths are Windows-friendly; we avoid absolute paths in exported metadata where possible.


## UI/UX Notes

- Keep it simple and clean (Bootstrap or Pico.css).
- No heavy SPA build step for v1; templates + small JS for polling run status.
- Show warnings about cost/time before starting batch runs.


## Configuration & Security

- Read `OPENAI_API_KEY` from `.env` on server side only; never exposed to browser.
- `.env` may also include: `DATASET_ROOT=ARC-AGI-2/data`, `WEB_CONCURRENCY=5`, `APP_BASE_URL`, `DB_URL`.
- Optional auth (Phase 3+) if we later expose externally.


## Directory Additions (new)

- webui-node/
  - views/ (EJS templates)
  - public/ (static assets)
  - scripts/ (Windows helper scripts to run the app)
  - server.js (Express entrypoint)
  - package.json (Node dependencies)
  - webui_data/ (app.db, exports/)
  - (Phase 1) python/solver_runner.py (invoked by Node child process)


## Delivery Plan & Milestones

- Phase 0: Project scaffolding (webui skeleton, requirements, basic home page that loads datasets and tasks) [~0.5 day]
- Phase 1: Single-task run end-to-end (submit → queue → run → persist → display artifacts → export ZIP/CSV) [~1.5 days]
- Phase 2: Batch runs + filters + bulk export [~1 day]
- Phase 3: Live logs/polling, thumbnails, simple comparison UX, notes/tags [~1 day]
- Phase 4: Windows packaging (command script), docs, optional Docker [~0.5 day]


## Acceptance Criteria (v1)

- User can select a dataset and task, start a run, and see its status update without a page refresh.
- Users can browse `ARC-AGI-2/data/`, filter tasks (search), and select which puzzles to run.
- Run detail page shows success/failure, duration, phases, and links to artifacts found in `img_tmp/`.
- DB contains a row per run and artifacts per image produced during the run.
- User can export a run (ZIP) and download CSV of all runs.
- No changes required to the existing solver files to achieve the above.


## Decisions

- Database: Use SQLite at `webui_data/app.db`.
- UI Style: Simple Bootstrap-like styling for MVP; no SPA build step.
- Exports: Per-run ZIP (JSON + images) and CSV summary.
- Concurrency: Default `WEB_CONCURRENCY=5` suitable for ≤5 hobbyist users.


## Risks & Mitigations

- API changes in OpenAI client: we isolate solver invocation in a service so updates are localized.
- Large image volumes in `img_tmp/`: we add periodic cleanup settings and reference integrity checks.
- Long-running runs: we cap concurrency, provide status polling, and consider cancellation in Phase 2.


## Next Step

- Implement Phase 1:
  - Add SQLite persistence (create `webui-node/webui_data/app.db` on first run; use better-sqlite3 or sqlite3).
  - Implement run submission endpoint and in-memory queue with concurrency from `WEB_CONCURRENCY`.
  - Add Python `solver_runner.py` and wire Node child process execution.
  - Build Run list/detail pages with artifact discovery from `img_tmp/`.
  - Implement single-run ZIP export and CSV export of runs.

---

## DB Schema (SQL)

We will initialize the SQLite database with the following tables:

```
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  started_at TEXT,
  finished_at TEXT,
  dataset TEXT NOT NULL,
  task_name TEXT NOT NULL,
  task_path TEXT NOT NULL,
  status TEXT NOT NULL,                -- queued | running | success | fail
  success INTEGER NOT NULL DEFAULT 0,  -- 0/1
  duration_seconds REAL,
  phases INTEGER,
  prediction_rows INTEGER,
  prediction_cols INTEGER,
  notes TEXT,
  error_message TEXT,
  log_path TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL,
  type TEXT NOT NULL,                  -- train_input | train_output | test_input | test_output | tool | final_prediction | other
  file_path TEXT NOT NULL,
  label TEXT,
  FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_run ON artifacts(run_id);
```

Statuses are restricted to: queued, running, success, fail.

## Environment Variables

- OPENAI_API_KEY: used by the Python solver (server-side only)
- DATASET_ROOT: default `ARC-AGI-2/data`
- WEB_CONCURRENCY: default `5`
- PORT: Node server port, default `5000`
- DB_PATH: optional override, default `webui-node/webui_data/app.db`

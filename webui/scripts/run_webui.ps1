#
# Windows PowerShell launcher for saturn-arc WebUI
# Author: Cascade (AI assistant)
#
# What this script does:
# - Activates your Python environment (if already active, skip)
# - Runs the FastAPI app with uvicorn in autoreload mode
# - Reads .env automatically via the app
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File webui\scripts\run_webui.ps1
#
param(
    [int]$Port = 8000
)

# Change to repo root (this script resides in webui\scripts)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

# Ensure webui requirements installed (uncomment if desired)
# python -m pip install -r webui\requirements-webui.txt

# Start the server
python -m uvicorn webui.app.main:app --host 127.0.0.1 --port $Port --reload

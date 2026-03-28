$ErrorActionPreference = "Stop"
Set-Location "$PSScriptRoot\backend"
$env:RAG_INGEST_ON_STARTUP = "false"
uvicorn app.main:app --host 127.0.0.1 --port 8000

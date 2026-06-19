<#
.SYNOPSIS
    Production-grade initialization script for kt-rag-project (PowerShell version).
.DESCRIPTION
    Automates workspace initialization via 'uv', creates and activates the venv,
    populates the project folder structure, and synchronizes dependencies.
    Designed for Windows PowerShell and PowerShell Core (cross-platform).
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "========================================================================"
Write-Host "Starting production environment initialization (PowerShell)"
Write-Host "========================================================================"

# 1. Verify Prerequisites
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "'uv' package manager is not installed or not available in the current PATH.`nPlease install uv (https://github.com/astral-sh/uv) and try again."
    exit 1
}

# 2. Verify and Target Current Directory Context
$currentDir = Split-Path -Leaf (Get-Location)
if ($currentDir -ne 'kt-rag-project' -and (Test-Path 'kt-rag-project')) {
    Write-Host "Navigating into detected 'kt-rag-project' subdirectory..."
    Set-Location 'kt-rag-project'
}

# 3. Initialize UV Workspace Environment and Create Virtual Environment
Write-Host "Initializing bare uv workspace..."
& uv init --bare

Write-Host "Creating virtual environment (.venv)..."
& uv venv

# 4. Environment Activation Sequence (Cross-Platform Compatibility)
Write-Host "Detecting host PowerShell platform..."
if (Test-Path '.venv\Scripts\Activate.ps1') {
    Write-Host "Activating virtual environment using .venv\Scripts\Activate.ps1"
    & "${PWD}\ .venv\Scripts\Activate.ps1" 2>$null
    # Use dot-sourcing if above fails
    if (-not $?) {
        . .\.venv\Scripts\Activate.ps1
    }
}
elseif (Test-Path '.venv/bin/Activate.ps1') {
    Write-Host "Activating virtual environment using .venv/bin/Activate.ps1"
    . .venv/bin/Activate.ps1
}
elseif (Test-Path '.venv/bin/activate') {
    Write-Host "Found POSIX activation script .venv/bin/activate — attempting to source using bash"
    bash -lc ". .venv/bin/activate; echo 'Activated via bash'"
}
else {
    Write-Error "Virtual environment activation script not found at expected locations.";
    exit 1
}

# 5. Build Production Directory Architecture
Write-Host "Generating structural directory trees..."
$dirs = @('src','data/videos','data/captions','data/transcripts','data/documents','chroma_db')
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

# 6. Generate Decoupled Application Modules (src/)
Write-Host "Populating application source modules inside src/..."
$files = @('src/config.py','src/transcriber.py','src/ingest.py','src/rag_chain.py','src/app.py')
foreach ($f in $files) {
    New-Item -ItemType File -Force -Path $f | Out-Null
}

# 7. Generate Root Configuration and Deployment Infrastructure
Write-Host "Populating deployment configurations and manifest files..."
New-Item -ItemType File -Force -Path Dockerfile | Out-Null
New-Item -ItemType File -Force -Path docker-compose.yml | Out-Null
if (-not (Test-Path README.md)) { New-Item -ItemType File -Force -Path README.md | Out-Null }

# 8. Core Dependency Population & Synchronization
if (Test-Path requirements.txt) {
    Write-Host "requirements.txt found — using existing manifest."
}
else {
    Write-Host "requirements.txt not found — creating a minimal placeholder manifest."
    @(
        'ollama',
        'chromadb',
        'faster-whisper',
        'streamlit',
        'langchain'
    ) | Out-File -FilePath requirements.txt -Encoding utf8
    Write-Host "Wrote minimal requirements.txt — consider replacing with full manifest."
}

Write-Host "Synchronizing project workspace dependencies via uv..."
& uv add -r requirements.txt

Write-Host "========================================================================"
Write-Host "Initialization workflow completed successfully."
Write-Host "Active Context: Virtual environment (.venv) should be engaged and synced." 
Write-Host "Current Directory Target: $(Get-Location)"
Write-Host "========================================================================"

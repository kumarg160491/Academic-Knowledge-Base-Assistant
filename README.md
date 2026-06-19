# Academic Knowledge Base Assistant

A fully local Retrieval-Augmented Generation (RAG) assistant designed to ingest lecture video recordings, seminars, research papers, and academic reference materials, allowing students and educators to retrieve grounded answers.

This project runs locally using **Ollama** for LLM generation and embeddings, **ChromaDB** for vector storage, and **Faster-Whisper** for video transcriptions.

---

## Features

- **Multi-Source Ingestion**: Ingest recorded lectures and presentations (MP4/MKV/AVI) with optional subtitles (VTT/SRT), alongside reference documents (PDF, DOCX, TXT, CSV, XLSX, PPTX, Py, SQL, Markdown, JSON).
- **Video-Optional Ingestion**: Support for document-only ingestion. If no video file is provided, the pipeline processes the academic papers, textbooks, and syllabus files directly.
- **Built-in Guardrails**:
  - **Input Guardrail**: Analyzes queries for prompt injection attacks and filters out-of-domain/off-topic questions using a zero-temperature LLM pass.
  - **Output Guardrail (Faithfulness Check)**: Post-verifies LLM responses against the retrieved context to detect and flag potential hallucinations.
- **Streamlit Interactive UI**: Toggle safety guardrails on-the-fly, view check reports, select ingested lectures or topics to query, and search the local knowledge base.

---

## Tech Stack

- **Core Framework**: LangChain (LCEL)
- **Frontend**: Streamlit
- **Local LLM & Embeddings**: Ollama (llama3.2 & nomic-embed-text)
- **Transcription**: Faster-Whisper
- **Vector Database**: ChromaDB

---

## Setup & Installation

### 1. Prerequisites
Ensure you have the following installed:
- Python 3.12+
- Ollama (running locally)
- FFmpeg (required for whisper transcriptions)

### 2. Install & Start Ollama Models
Make sure Ollama is running and pull the required models:
```bash
# Pull the LLM model
ollama pull llama3.2

# Pull the Embedding model
ollama pull nomic-embed-text
```

### 3. Clone and Setup Environment
Using Python's `uv` or `pip`:
```bash
# Clone the repository
cd kt-knowledge-rag

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```
---

### Automated setup script

This repository includes `setup_project.sh` — a production-grade initialization script that automates creating a virtual environment, populating the project folder structure, and installing dependencies via `uv`.

- **Purpose:** Bootstraps the workspace by creating `.venv`, writing `requirements.txt`, and generating basic `src/`, `data/`, and `chroma_db/` folders and placeholder files.
- **Prerequisites:** Ensure `uv` is installed and available on your `PATH` (see https://github.com/astral-sh/uv).
- **Usage:**
```bash
# Make executable (optional) and run from repository root
chmod +x setup_project.sh
./setup_project.sh

# Or run explicitly with bash
bash setup_project.sh
```
- **Notes / Warnings:**
   - Run the script from the project root. If a `kt-rag-project` subdirectory exists, the script may `cd` into it.
   - The script will create or overwrite files such as `requirements.txt`, `README.md`, `Dockerfile`, and `docker-compose.yml`, and touch several `src/` files. Review the script before running on an existing project.
   - After the script completes the virtual environment will be activated and `uv` will have synchronized the dependencies listed in `requirements.txt`.

---

### PowerShell setup script

A Windows/PowerShell-friendly equivalent is provided as `setup_project.ps1`.

- **Purpose:** Same bootstrap actions as `setup_project.sh`, but implemented for PowerShell and PowerShell Core.
- **Prerequisites:** PowerShell (Windows PowerShell or PowerShell Core) and `uv` available in `PATH`.
- **Usage (Windows PowerShell):**
```powershell
# From repository root
.\setup_project.ps1
```
- **Usage (PowerShell Core on macOS/Linux):**
```bash
# Run PowerShell Core then execute the script
pwsh ./setup_project.ps1
```

### Which script to use

- **`setup_project.sh`**: Recommended for POSIX environments — Linux, macOS, and Git Bash / MSYS on Windows.
- **`setup_project.ps1`**: Recommended for Windows PowerShell and PowerShell Core (cross-platform) users.


## How to Run the App

1. Ensure Ollama is running:
   ```bash
   ollama serve
   ```
2. Start the Streamlit application:
   ```bash
   uv run streamlit run src/app.py
   ```
3. Open `http://localhost:8501` in your browser.

---

## How to Use

### 1. Ingest Academic Content
1. Enter a unique **Session Name** (e.g. `machine-learning-lecture-1` or `research-paper-analysis`).
2. Upload a lecture video (MP4/MKV) OR upload reference files (PDF, DOCX, TXT, etc.).
3. Click **Ingest KT Session** (form button).
4. The form will automatically reset, showing `Ingestion completed. Proceed with asking the question.` upon success.

### 2. Querying & Safety
1. Choose to query **All Sessions** or filter by a specific ingested lecture/topic.
2. Toggle **Enable Guardrails** in the sidebar to enforce input topic-filtering and output hallucination checks.
3. Enter your question and click **Ask**.
4. The response will include the answer and an expandable **Guardrail Status Report** detailing the safety checks.

#!/bin/bash

# ==============================================================================
# Script Name:        setup_project.sh
# Description:        Production-grade initialization script for kt-rag-project.
#                     Automates workspace initialization via 'uv', creates and 
#                     activates the venv, injects unpinned dependencies, and 
#                     populates the project folder structure.
# Compatibility:      POSIX (Linux, macOS) and Windows (via Git Bash/MSYS).
# ==============================================================================

# Strict mode: Exit immediately if any command fails, or if uninitialized variables are referenced.
set -euo pipefail

echo "========================================================================"
echo "Starting production environment initialization inside existing root directory"
echo "========================================================================"

# 1. Verify Prerequisites
if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' package manager is not installed or not available in the current PATH." >&2
    echo "Please install uv (https://github.com/astral-sh/uv) and try again." >&2
    exit 1
fi

# 2. Verify and Target Current Directory Context
CURRENT_DIR=$(basename "$(pwd)")
if [ "$CURRENT_DIR" != "kt-rag-project" ] && [ -d "kt-rag-project" ]; then
    echo "Navigating into detected 'kt-rag-project' subdirectory..."
    cd kt-rag-project
fi

# 3. Initialize UV Workspace Environment and Create Virtual Environment
echo "Initializing bare uv workspace..."
uv init --bare

echo "Creating virtual environment (.venv)..."
uv venv

# 4. Environment Activation Sequence (Cross-Platform Compatibility)
OS_TYPE="$(uname)"
echo "Detecting operating system host: $OS_TYPE"

echo "Activating virtual environment..."
case "$OS_TYPE" in
    CYGWIN*|MINGW*|MSYS*)
        if [ -f ".venv/Scripts/activate" ]; then
            source .venv/Scripts/activate
        else
            echo "Error: Virtual environment activation script not found at .venv/Scripts/activate" >&2
            exit 1
        fi
        ;;
    Darwin*|Linux*)
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
        else
            echo "Error: Virtual environment activation script not found at .venv/bin/activate" >&2
            exit 1
        fi
        ;;
    *)
        echo "Unknown OS type detected. Attempting standard POSIX/Windows fallbacks..."
        source .venv/bin/activate || source .venv/Scripts/activate || {
            echo "Error: Failed to safely determine virtual environment activation path." >&2
            exit 1
        }
        ;;
esac

# 5. Build Production Directory Architecture
echo "Generating structural directory trees..."
mkdir -p src \
         data/videos \
         data/captions \
         data/transcripts \
         data/documents \
         chroma_db

# 6. Generate Decoupled Application Modules (src/)
echo "Populating application source modules inside src/..."
touch src/config.py \
      src/transcriber.py \
      src/ingest.py \
      src/rag_chain.py \
      src/app.py

# 7. Generate Root Configuration and Deployment Infrastructure
echo "Populating deployment configurations and manifest files..."
touch Dockerfile \
      docker-compose.yml \
      README.md

# 8. Core Dependency Population & Synchronization (Versions Omitted)
echo "Writing unpinned package manifest to requirements.txt..."
cat << 'EOF' > requirements.txt
aiofiles
aiohappyeyeballs
aiohttp
aiosignal
altair
annotated-doc
annotated-types
anyio
arxiv
asttokens
attrs
av
backoff
bcrypt
beautifulsoup4
black
blinker
blis
boto3
botocore
build
cachetools
catalogue
certifi
chardet
charset-normalizer
chromadb
click
cloudpathlib
comm
confection
contourpy
ctranslate2
cuda-bindings
cuda-pathfinder
cuda-toolkit
cycler
cymem
debugpy
decorator
distro
dotenv
durationpy
emoji
et-xmlfile
executing
faster-whisper
feedparser
ffmpeg-python
filelock
filetype
flatbuffers
fonttools
frozenlist
fsspec
future
gitdb
gitpython
googleapis-common-protos
greenlet
groq
grpcio
h11
hf-xet
html5lib
httpcore
httptools
httpx
httpx-sse
huggingface-hub
idna
importlib-resources
installer
ipykernel
ipython
ipython-pygments-lexers
isort
itsdangerous
jedi
jinja2
jiter
jmespath
joblib
jsonpatch
jsonpointer
jsonschema
jsonschema-specifications
jupyter-client
jupyter-core
kiwisolver
kubernetes
lance-namespace
lance-namespace-urllib3-client
langchain
langchain-chroma
langchain-classic
langchain-community
langchain-core
langchain-faiss
langchain-groq
langchain-huggingface
langchain-ollama
langchain-openai
langchain-protocol
langchain-text-splitters
langdetect
langgraph
langgraph-checkpoint
langgraph-prebuilt
langgraph-sdk
langsmith
llvmlite
lxml
markdown-it-py
markupsafe
matplotlib
matplotlib-inline
mdurl
mmh3
mpmath
multidict
murmurhash
mypy-extensions
narwhals
nest-asyncio
networkx
nltk
numba
numpy
nvidia-cublas
nvidia-cuda-cupti
nvidia-cuda-nvrtc
nvidia-cuda-runtime
nvidia-cudnn-cu13
nvidia-cufft
nvidia-cufile
nvidia-curand
nvidia-cusolver
nvidia-cusparse
nvidia-cusparselt-cu13
nvidia-nccl-cu13
nvidia-nvjitlink
nvidia-nvshmem-cu13
nvidia-nvtx
oauthlib
olefile
ollama
onnxruntime
openai
openpyxl
opentelemetry-api
opentelemetry-exporter-otlp-proto-common
opentelemetry-exporter-otlp-proto-grpc
opentelemetry-proto
opentelemetry-sdk
opentelemetry-semantic-conventions
orjson
ormsgpack
overrides
packaging
pandas
parso
pathspec
pexpect
pillow
pip
platformdirs
preshed
prompt-toolkit
propcache
protobuf
psutil
ptyprocess
pure-eval
pyarrow
pybase64
pydantic
pydantic-core
pydantic-settings
pydeck
pygments
pylance
pyparsing
pypdf
pypdfium2
pypika
pyproject-hooks
pysrt
python-dateutil
python-docx
python-dotenv
python-iso639
python-magic
python-multipart
python-oxmsg
python-pptx
pytokens
pyyaml
pyzmq
rapidfuzz
referencing
regex
requests
requests-oauthlib
requests-toolbelt
rich
rpds-py
s3transfer
sacremoses
scikit-learn
scipy
sentence-transformers
sentencepiece
setuptools
sgmllib3k
shellingham
six
smart-open
smmap
sniffio
soupsieve
spacy
spacy-legacy
spacy-loggers
sqlalchemy
srsly
stack-data
starlette
streamlit
sympy
tenacity
thinc
threadpoolctl
tiktoken
tokenizers
toml
torch
tornado
tqdm
traitlets
transformers
triton
typer
typing-extensions
typing-inspection
unstructured
unstructured-client
urllib3
uuid-utils
uv
uvicorn
uvloop
wasabi
watchdog
watchfiles
wcwidth
weasel
webencodings
websocket-client
websockets
webvtt-py
wikipedia
wrapt
xlsxwriter
xxhash
yarl
zstandard
EOF

echo "Synchronizing project workspace dependencies via uv..."
uv add -r requirements.txt

echo "========================================================================"
echo "Initialization workflow completed successfully."
echo "========================================================================"
echo "Active Context: Virtual environment (.venv) is engaged and synced."
echo "Current Directory Target: $(pwd)"
echo "========================================================================"
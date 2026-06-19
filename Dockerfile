FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml .
RUN uv sync

COPY . .

RUN mkdir -p data/videos data/captions data/transcripts data/documents chroma_db

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
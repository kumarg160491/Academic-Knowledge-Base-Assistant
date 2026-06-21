# config.py
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OllamaConfig:
    base_url   : str   = "http://ollama:11434"
    model      : str   = "llama3.2"
    embedding  : str   = "nomic-embed-text"
    temperature: float = 0.1


@dataclass(frozen=True)
class ChromaConfig:
    db_path        : str = "./chroma_db"
    collection_name: str = "kt_knowledge_base"


@dataclass(frozen=True)
class RetrieverConfig:
    search_type: str = "similarity"
    top_k      : int = 5


@dataclass(frozen=True)
class DataConfig:
    videos_dir     : str = "data/videos"
    captions_dir   : str = "data/captions"
    transcripts_dir: str = "data/transcripts"
    documents_dir  : str = "data/documents"
    chunk_size     : int = 600
    chunk_overlap  : int = 100


@dataclass(frozen=True)
class WhisperConfig:
    model_size : str  = "base"       # tiny | base | small | medium
    device     : str  = "cpu"        # cpu | cuda
    language   : str  = "en"
    beam_size  : int  = 5


@dataclass(frozen=True)
class AppConfig:
    ollama   : OllamaConfig   = field(default_factory=OllamaConfig)
    chroma   : ChromaConfig   = field(default_factory=ChromaConfig)
    retriever: RetrieverConfig= field(default_factory=RetrieverConfig)
    data     : DataConfig     = field(default_factory=DataConfig)
    whisper  : WhisperConfig  = field(default_factory=WhisperConfig)


cfg = AppConfig()
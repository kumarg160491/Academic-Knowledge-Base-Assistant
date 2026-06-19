import os
import logging
import webvtt
import pysrt
from faster_whisper import WhisperModel
from config import cfg

logger = logging.getLogger(__name__)


def parse_vtt(caption_path: str) -> str:
    lines = []
    for caption in webvtt.read(caption_path):
        text = caption.text.strip()
        timestamp = caption.start
        if text:
            # Format time boundaries cleanly for LLM consumption
            lines.append(f"[{timestamp}] {text}")
    transcript = "\n".join(lines)
    logger.info(f"Parsed VTT asset: {caption_path} ({len(lines)} segments)")
    return transcript


def parse_srt(caption_path: str) -> str:
    subs = pysrt.open(caption_path)
    lines = []
    for sub in subs:
        timestamp = str(sub.start).split(",")[0]
        text = sub.text.replace("\n", " ").strip()
        if text:
            lines.append(f"[{timestamp}] {text}")
    transcript = "\n".join(lines)
    logger.info(f"Parsed SRT asset: {caption_path} ({len(lines)} segments)")
    return transcript


def transcribe_with_whisper(video_path: str) -> str:
    logger.info(f"Initializing Faster-Whisper computational engine: {cfg.whisper.model_size}")
    model = WhisperModel(
        cfg.whisper.model_size,
        device=cfg.whisper.device,
        compute_type="int8"
    )
    
    logger.info(f"Processing deep-learning audio transcription against target: {video_path}")
    segments, info = model.transcribe(
        video_path,
        beam_size=cfg.whisper.beam_size,
        language=cfg.whisper.language,
    )
    
    lines = []
    for segment in segments:
        timestamp = _seconds_to_timestamp(segment.start)
        text = segment.text.strip()
        if text:
            lines.append(f"[{timestamp}] {text}")

    transcript = "\n".join(lines)
    logger.info(f"Whisper inference loop resolved safely ({len(lines)} chunks loaded)")
    return transcript


def extract_transcript(session_name: str, video_path: str, caption_path: str = None) -> str:
    transcript_file = os.path.join(cfg.data.transcripts_dir, f"{session_name}.txt")

    if os.path.exists(transcript_file):
        logger.info(f"Cache hit identified. Pulling compilation matrix from: {transcript_file}")
        with open(transcript_file, "r", encoding="utf-8") as f:
            return f.read()

    transcript = None
    if caption_path and os.path.exists(caption_path):
        ext = os.path.splitext(caption_path)[-1].lower()
        if ext == ".vtt":
            transcript = parse_vtt(caption_path)
        elif ext == ".srt":
            transcript = parse_srt(caption_path)
        else:
            logger.warning(f"Unsupported manual format index: {ext}. Reverting to AI transcript pipelines.")

    if not transcript:
        logger.info("Direct session sidecar captions missing. Invoking Whisper audio pipeline extraction step.")
        transcript = transcribe_with_whisper(video_path)

    os.makedirs(cfg.data.transcripts_dir, exist_ok=True)
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write(transcript)
    logger.info(f"Static context matrix backed up cleanly to: {transcript_file}")

    return transcript


def _seconds_to_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(description="Transcribe audio with faster-whisper")
    parser.add_argument("--input", required=True, help="Path to an input audio file")
    parser.add_argument("--model", default=os.environ.get("OPENCLAW_VOICE_MODEL", "base"))
    parser.add_argument("--language", default=os.environ.get("OPENCLAW_VOICE_LANGUAGE") or None)
    parser.add_argument("--device", default=os.environ.get("OPENCLAW_VOICE_DEVICE", "cpu"))
    parser.add_argument("--compute-type", default=os.environ.get("OPENCLAW_VOICE_COMPUTE_TYPE", "int8"))
    parser.add_argument("--beam-size", type=int, default=int(os.environ.get("OPENCLAW_VOICE_BEAM_SIZE", "5")))
    parser.add_argument("--model-dir", default=os.environ.get("OPENCLAW_VOICE_MODEL_DIR") or None)
    return parser.parse_args()


def main():
    args = parse_args()
    audio_path = Path(args.input).expanduser().resolve()
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    from faster_whisper import WhisperModel

    model = WhisperModel(
        args.model,
        device=args.device,
        compute_type=args.compute_type,
        download_root=args.model_dir,
        cpu_threads=max(1, os.cpu_count() or 1),
    )
    segments, info = model.transcribe(
        str(audio_path),
        language=args.language,
        beam_size=max(1, args.beam_size),
        vad_filter=True,
        condition_on_previous_text=False,
    )
    text = " ".join(segment.text.strip() for segment in segments if segment.text and segment.text.strip()).strip()
    payload = {
        "text": text,
        "language": getattr(info, "language", None),
        "duration": getattr(info, "duration", None),
        "duration_after_vad": getattr(info, "duration_after_vad", None),
    }
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - CLI error path
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""Hermes BT Unit Ready command TTS provider.

Usage:
  mimo_bt_unit_tts_command.py --input TEXT_FILE --output OUT_FILE [--format mp3|wav|m4a]

Reads target text, synthesizes a low/reliable BT Unit style voice through MiMo
V2.5 voice design, then applies light unit-comms processing and fixed loudness.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
ENV_FILE = HERMES_HOME / ".env"


def load_env() -> None:
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ffmpeg_bin() -> str:
    for candidate in ("/opt/homebrew/bin/ffmpeg", "ffmpeg"):
        try:
            subprocess.run([candidate, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=5)
            return candidate
        except Exception:
            continue
    raise RuntimeError("ffmpeg not found")


def synthesize(text: str) -> bytes:
    load_env()
    api_key = os.environ.get("XIAOMI_API_KEY") or os.environ.get("MIMO_API_KEY") or os.environ.get("XIAOMI_TOKEN")
    base_url = os.environ.get("XIAOMI_BASE_URL") or "https://api.xiaomimimo.com/v1"
    if not api_key:
        raise RuntimeError("missing XIAOMI_API_KEY/MIMO_API_KEY/XIAOMI_TOKEN")

    # Keep desktop voice replies compact; long answers as audio are disruptive.
    cleaned = " ".join(text.split())
    if len(cleaned) > 900:
        cleaned = cleaned[:900].rstrip() + "。"

    voice_prompt = (
        "低沉可靠的机体 AI 声线，中性偏男性，稳定、克制、带保护性，像重型机甲本体在回应驾驶员。"
        "这是 Hermes 控制台语音对话回复：根据语义调整节奏和语气，确认类短促，解释类平稳，"
        "提醒类稍加重音；称呼用户时放慢半拍。不要喊叫，不要播音腔，不要英文腔；中文自然、有停顿。"
    )
    payload = {
        "model": "mimo-v2.5-tts-voicedesign",
        "messages": [
            {"role": "user", "content": voice_prompt},
            {"role": "assistant", "content": cleaned},
        ],
        "audio": {"format": "wav", "optimize_text_preview": False},
    }
    req = urllib.request.Request(
        base_url.rstrip() + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}", "api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as response:
        obj = json.loads(response.read())
    return base64.b64decode(obj["choices"][0]["message"]["audio"]["data"])


def process_audio(raw_wav: Path, output: Path, fmt: str) -> None:
    ffmpeg = ffmpeg_bin()
    output.parent.mkdir(parents=True, exist_ok=True)
    codec_args = []
    if fmt == "wav":
        codec_args = ["-c:a", "pcm_s16le"]
    elif fmt in {"mp3", "m4a"}:
        codec_args = ["-c:a", "aac"] if fmt == "m4a" else ["-c:a", "libmp3lame", "-b:a", "128k"]
    elif fmt == "ogg":
        codec_args = ["-c:a", "libopus", "-b:a", "64k"]
    else:
        codec_args = ["-c:a", "aac"]
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(raw_wav),
            "-af",
            "highpass=f=70,lowpass=f=6200,acompressor=threshold=-18dB:ratio=2.4:attack=16:release=170,volume=1.25,aecho=0.20:0.10:18:0.035,loudnorm=I=-16:TP=-1.5:LRA=11",
            "-ar",
            "24000",
            "-ac",
            "1",
            *codec_args,
            str(output),
        ],
        check=True,
        timeout=120,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--format", default=None)
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    fmt = (args.format or output_path.suffix.lstrip(".") or "mp3").lower()
    text = input_path.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError("empty TTS input")
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "raw.wav"
        raw.write_bytes(synthesize(text))
        process_audio(raw, output_path, fmt)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"mimo_bt_unit_tts_command failed: {exc}", file=sys.stderr)
        raise SystemExit(1)

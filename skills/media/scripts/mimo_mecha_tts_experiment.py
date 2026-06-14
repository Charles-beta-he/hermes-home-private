#!/usr/bin/env python3
"""Generate sci-fi / mecha boot-voice candidates with MiMo V2.5 TTS.

Environment:
  XIAOMI_API_KEY or MIMO_API_KEY
  XIAOMI_BASE_URL optional, defaults to https://api.xiaomimimo.com/v1

Usage:
  python scripts/mimo_mecha_tts_experiment.py \
    --text-file /path/to/script.txt \
    --out-dir /tmp/mecha-voice \
    --preset pacific-rim

This script intentionally uses abstract style directions and does not clone or imitate
any specific actor/character voice.
"""
import argparse
import base64
import json
import os
import subprocess
import urllib.request
from pathlib import Path


def load_dotenv() -> None:
    env = Path.home() / ".hermes/.env"
    if not env.exists():
        return
    for line in env.read_text(errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


PROMPTS = {
    "pacific-rim": [
        {
            "name": "jaeger_ai_voicedesign",
            "model": "mimo-v2.5-tts-voicedesign",
            "user": "女性化但不过分拟人的大型机甲 cockpit AI 声线。冷静、精密、无情绪波动，像 Jaeger 启动时的系统 A.I. 汇报。声音干净、稍低、带轻微电子质感；语速中慢，停顿短促，状态词如 online、locked、nominal、green 要清晰。不要可爱，不要播音腔，不要逐字机械蹦字，不要模仿任何具体演员或现成角色，只取好莱坞重型机甲驾驶舱系统汇报的抽象质感。",
            "audio": {"format": "wav", "optimize_text_preview": False},
        },
        {
            "name": "loccent_operator_voicedesign",
            "model": "mimo-v2.5-tts-voicedesign",
            "user": "成熟女性 Mission Control / LOCCENT Operator 声线，冷静、专业、低压、战术指挥感。像大型机甲出动前的控制中心状态播报：不是情绪表演，而是精准、克制、带轻微压迫感的系统汇报。英文技术术语发音稳定，中文自然连贯，语速中等偏慢。",
            "audio": {"format": "wav", "optimize_text_preview": False},
        },
        {
            "name": "preset_bingtang_system_ai",
            "model": "mimo-v2.5-tts",
            "user": "用冷静、克制、偏科幻系统 A.I. 的中文女性声线朗读。像重型机甲驾驶舱状态汇报，语速中慢，停顿短促，英文技术词清晰；不要活泼，不要甜美，不要播音腔。",
            "audio": {"format": "wav", "voice": "冰糖"},
        },
    ],
    "hermes-operator": [
        {
            "name": "mecha_operator_voicedesign",
            "model": "mimo-v2.5-tts-voicedesign",
            "user": "三十多岁的中文男性系统 Operator 声线，低沉、磁性、克制、专业，像近未来重型机甲驾驶舱里的任务控制 AI。语速中慢，咬字清晰但自然，英文技术术语发音稳定；有战备感和压迫感，但不要像机器人逐字朗读，不要夸张表演。",
            "audio": {"format": "wav", "optimize_text_preview": False},
        }
    ],
}


def call_mimo(base_url: str, api_key: str, model: str, user: str, text: str, audio: dict) -> bytes:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user}, {"role": "assistant", "content": text}],
        "audio": audio,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}", "api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        obj = json.loads(resp.read())
    return base64.b64decode(obj["choices"][0]["message"]["audio"]["data"])


def ffmpeg_variant(wav: Path, suffix: str, afilter: str) -> Path | None:
    out = wav.with_name(wav.stem + suffix + ".m4a")
    try:
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-af", afilter, str(out)], check=True)
        return out
    except Exception:
        return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--preset", default="pacific-rim", choices=sorted(PROMPTS))
    args = ap.parse_args()

    load_dotenv()
    api_key = os.environ.get("XIAOMI_API_KEY") or os.environ.get("MIMO_API_KEY")
    if not api_key:
        raise SystemExit("Missing XIAOMI_API_KEY/MIMO_API_KEY")
    base_url = os.environ.get("XIAOMI_BASE_URL") or "https://api.xiaomimimo.com/v1"
    text = Path(args.text_file).read_text(encoding="utf-8").strip()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = []
    for case in PROMPTS[args.preset]:
        wav = out_dir / f"{case['name']}.wav"
        wav.write_bytes(call_mimo(base_url, api_key, case["model"], case["user"], text, case["audio"]))
        raw = ffmpeg_variant(wav, "", "anull")
        cockpit = ffmpeg_variant(wav, "_cockpit_ai", "highpass=f=115,lowpass=f=5600,acompressor=threshold=-18dB:ratio=2.8:attack=10:release=145,volume=1.38,aecho=0.45:0.22:24:0.07")
        comms = ffmpeg_variant(wav, "_jaeger_comms", "highpass=f=180,lowpass=f=3900,acompressor=threshold=-19dB:ratio=3.4:attack=8:release=120,volume=1.48,aecho=0.38:0.16:18:0.05")
        summary.append({"name": case["name"], "wav": str(wav), "raw_m4a": str(raw) if raw else None, "cockpit_ai": str(cockpit) if cockpit else None, "jaeger_comms": str(comms) if comms else None})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

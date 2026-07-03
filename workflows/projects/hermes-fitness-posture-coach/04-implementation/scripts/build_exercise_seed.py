#!/usr/bin/env python3
"""Build a self-use exercise seed index from hasaneyldrm/exercises-dataset.

Boundary: metadata/instructions only. The upstream README says media is not included;
image/gif fields are expected to be null and must not be invented.
"""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/exercises.json"
OUT = ROOT / "data/derived/exercise_seed_index.json"
REPORT = ROOT / "data/derived/exercise_seed_report.md"

LOW_RISK_STARTERS = {
    "squat": ["squat", "bodyweight squat"],
    "push_up": ["push-up", "push up"],
    "plank": ["plank"],
    "lunge": ["lunge"],
}

def main() -> None:
    records = json.loads(RAW.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise SystemExit("raw dataset must be a JSON array")
    categories = Counter()
    body_parts = Counter()
    equipment = Counter()
    targets = Counter()
    languages = Counter()
    media_non_null = Counter()
    normalized = []
    starter_ids = defaultdict(list)

    for rec in records:
        categories[rec.get("category") or ""] += 1
        body_parts[rec.get("body_part") or ""] += 1
        equipment[rec.get("equipment") or ""] += 1
        targets[rec.get("target") or ""] += 1
        for lang, text in (rec.get("instructions") or {}).items():
            if text:
                languages[lang] += 1
        for media_field in ["image", "gif_url", "gifUrl", "thumbnail"]:
            if rec.get(media_field):
                media_non_null[media_field] += 1
        name=(rec.get("name") or "").lower()
        for starter, needles in LOW_RISK_STARTERS.items():
            if any(n in name for n in needles):
                starter_ids[starter].append(rec.get("id"))
        normalized.append({
            "id": rec.get("id"),
            "name": rec.get("name"),
            "category": rec.get("category"),
            "body_part": rec.get("body_part"),
            "equipment": rec.get("equipment"),
            "target": rec.get("target"),
            "secondary_muscles": rec.get("secondary_muscles") or rec.get("secondaryMuscles") or [],
            "media_id": rec.get("media_id"),
            "has_media_asset": bool(rec.get("image") or rec.get("gif_url") or rec.get("gifUrl")),
            "instruction_languages": sorted([k for k,v in (rec.get("instructions") or {}).items() if v]),
            "zh_instruction": (rec.get("instructions") or {}).get("zh"),
            "en_instruction": (rec.get("instructions") or {}).get("en"),
        })
    index = {
        "source": "https://github.com/hasaneyldrm/exercises-dataset",
        "boundary": "self-use metadata seed only; no bundled exercise images/GIFs; not commercial-license-cleared",
        "total_exercises": len(records),
        "category_counts": dict(categories.most_common()),
        "body_part_counts": dict(body_parts.most_common()),
        "equipment_counts": dict(equipment.most_common()),
        "target_counts_top30": dict(targets.most_common(30)),
        "instruction_language_coverage": dict(languages.most_common()),
        "non_null_media_fields": dict(media_non_null),
        "low_risk_starter_candidate_ids": {k:v[:20] for k,v in starter_ids.items()},
        "records": normalized,
    }
    OUT.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    report = [
        "# Exercise seed build report",
        "",
        f"Total exercises: **{len(records)}**",
        f"Media fields non-null: `{dict(media_non_null)}` (expected empty for this repo)",
        "",
        "## Top categories",
        *[f"- {k}: {v}" for k,v in categories.most_common(12)],
        "",
        "## Top equipment",
        *[f"- {k}: {v}" for k,v in equipment.most_common(12)],
        "",
        "## Low-risk starter candidate counts",
        *[f"- {k}: {len(v)} candidates; first ids: {', '.join(v[:8])}" for k,v in starter_ids.items()],
        "",
        "## Product boundary",
        "- This seed supports action catalog / filtering / Chinese instruction cards / phase checklist drafting.",
        "- It does not provide pose keypoints, rep segmentation, form-scoring rules, or media licensing.",
    ]
    REPORT.write_text("\n".join(report)+"\n", encoding="utf-8")
    print(json.dumps({"ok": True, "records": len(records), "out": str(OUT), "report": str(REPORT), "media_non_null": dict(media_non_null)}, ensure_ascii=False))

if __name__ == "__main__":
    main()

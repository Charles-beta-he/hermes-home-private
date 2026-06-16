#!/usr/bin/env python3
"""OCR and summarize China-local app screenshots.

Intended input: user-provided screenshots from Dianping/Meituan/XHS/Douyin/Amap.
This script does not access platforms directly; it extracts visible text from images.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pytesseract
from PIL import Image, ImageOps, ImageFilter


def preprocess(img: Image.Image) -> Image.Image:
    # Conservative preprocessing: enlarge and increase contrast for mobile app screenshots.
    img = img.convert("RGB")
    scale = 2 if max(img.size) < 2500 else 1
    if scale != 1:
        img = img.resize((img.width * scale, img.height * scale))
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray)
    return gray.filter(ImageFilter.SHARPEN)


def extract_fields(text: str) -> Dict[str, Any]:
    clean = re.sub(r"[ \t]+", " ", text)
    lines = [ln.strip() for ln in clean.splitlines() if ln.strip()]
    joined = "\n".join(lines)
    fields: Dict[str, Any] = {"lines": lines[:120]}

    ratings: List[str] = []
    for pat in [r"(\d\.\d)\s*分", r"评分\s*([0-5]\.\d)", r"([0-5]\.\d)\s*(?:星|/5)"]:
        ratings += re.findall(pat, joined)
    if ratings:
        fields["ratings"] = sorted(set(ratings), reverse=True)

    prices: List[str] = []
    for pat in [r"人均\s*[¥￥]?(\d+)", r"[¥￥]\s*(\d+(?:\.\d+)?)", r"(\d+)\s*元"]:
        prices += re.findall(pat, joined)
    if prices:
        fields["prices_or_per_capita_candidates"] = prices[:30]

    dishes = []
    dish_keywords = ["推荐菜", "烧麦", "稍麦", "羊杂", "羊肉", "焙子", "奶茶", "羊排", "手把肉", "酸奶", "炸羊尾"]
    for ln in lines:
        if any(k in ln for k in dish_keywords):
            dishes.append(ln)
    if dishes:
        fields["dish_signal_lines"] = dishes[:30]

    negative = []
    neg_keywords = ["差评", "难吃", "踩雷", "避雷", "排队", "服务差", "贵", "坑", "不好吃", "等位", "卫生"]
    for ln in lines:
        if any(k in ln for k in neg_keywords):
            negative.append(ln)
    if negative:
        fields["risk_signal_lines"] = negative[:30]

    return fields


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+", help="Screenshot image paths")
    ap.add_argument("--lang", default="chi_sim+eng")
    ap.add_argument("--psm", default="6")
    args = ap.parse_args()
    results = []
    for image in args.images:
        path = Path(image).expanduser()
        img = Image.open(path)
        pre = preprocess(img)
        text = pytesseract.image_to_string(pre, lang=args.lang, config=f"--psm {args.psm}")
        results.append({
            "image": str(path),
            "ocr_lang": args.lang,
            "raw_text": text,
            "extracted": extract_fields(text),
        })
    print(json.dumps({"schema": "china_local_screenshot_ocr_v1", "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

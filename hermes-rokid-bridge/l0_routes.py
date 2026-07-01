"""Adapter-neutral L0 route metadata for the Access Brain.

The registry describes read-only route ownership and matching order without
importing FastAPI, Rokid request models, filesystem access, or model providers.
Device adapters can use the route IDs to dispatch to their local cache/context
handlers.
"""
from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from access_brain import ACCESS_LAYER_QUERY_PATTERNS


CAPABILITY_QUERY_PATTERNS = (
    "你能做什么",
    "你会什么",
    "有什么能力",
    "能力列表",
    "怎么用你",
    "使用说明",
    "你能干什么",
    "你是干什么的",
    "你是什么",
    "介绍一下你自己",
)
DAILY_BRIEF_PATTERNS = (
    "日报",
    "今日简报",
    "今天简报",
    "今日重点",
    "今天重点",
)
BRAIN_STATS_PATTERNS = (
    "本地大脑",
    "本地电脑",
    "大脑状态",
    "脑状态",
    "任务统计",
    "待办统计",
    "任务池",
    "任务池状态",
    "任务池进度",
    "任务进度",
    "现在有什么任务",
    "今天有什么任务",
    "最近有什么任务",
    "最近任务",
    "今日任务",
    "大脑统计",
    "多脑架构",
    "多脑状态",
    "本地电脑状态",
)
MANUFACTURING_STATUS_PATTERNS = (
    "制造脑状态",
    "制造脑进度",
    "制造脑的进度",
    "制造状态",
    "打印机状态",
    "打印状态",
    "打印进度",
    "打印到哪里",
    "打印到哪",
    "还要多久",
    "剩余多久",
    "拓竹状态",
    "Bambu 状态",
    "Bambu状态",
    "X2D 状态",
    "X2D状态",
    "料盘状态",
    "AMS 状态",
    "AMS状态",
    "温度状态",
)
ROKID_DEVELOPER_RESOURCE_PATTERNS = (
    "Rokid开发资源",
    "Rokid 开发资源",
    "开发资源入口",
    "开发者资源",
    "开发者入口",
    "Rokid文档",
    "Rokid 文档",
    "SDK文档",
    "YodaOS-Sprite",
    "Sprite文档",
    "开放平台入口",
    "眼镜端怎么开发",
    "眼镜端怎么完善",
    "根据文档眼镜端",
    "Glasses开发",
    "Rokid Glasses开发",
)


FUZZY_FILLER_CHARS = " 的了呢吗嘛啊呀吧个一下请帮我查查问问看看看"
FUZZY_HOMOPHONE_TRANSLATION = str.maketrans({
    "毒": "度",
    "读": "度",
    "渡": "度",
    "肚": "度",
    "睹": "度",
    "都": "度",
    "堵": "度",
    "净": "进",
    "近": "进",
    "装": "状",
    "太": "态",
})
FUZZY_MIN_RATIO = 0.78


def _normalize_for_l0_intent(text: str) -> str:
    lowered = text.strip().lower().translate(FUZZY_HOMOPHONE_TRANSLATION)
    return "".join(ch for ch in lowered if ch not in FUZZY_FILLER_CHARS and not ch.isspace())


def _best_substring_ratio(text: str, pattern: str) -> float:
    if not text or not pattern:
        return 0.0
    if pattern in text:
        return 1.0
    # Compare against windows near the pattern length so one ASR-corrupted word
    # (进毒/净度/进读) does not require an ever-growing keyword list.
    best = SequenceMatcher(None, text, pattern).ratio()
    min_len = max(1, len(pattern) - 2)
    max_len = min(len(text), len(pattern) + 2)
    for size in range(min_len, max_len + 1):
        for start in range(0, len(text) - size + 1):
            ratio = SequenceMatcher(None, text[start:start + size], pattern).ratio()
            if ratio > best:
                best = ratio
    return best


def _looks_like_route_intent(text: str, intent_terms: tuple[str, ...]) -> bool:
    normalized = _normalize_for_l0_intent(text)
    return bool(normalized and any(_normalize_for_l0_intent(term) in normalized for term in intent_terms))


@dataclass(frozen=True)
class L0Route:
    route_id: str
    patterns: tuple[str, ...]
    is_read_only: bool = True
    side_effect_scope: str = "none"
    description: str = ""
    intent_terms: tuple[str, ...] = ()
    fuzzy: bool = False

    def matches(self, user_text: str) -> bool:
        text = user_text.strip()
        if not text:
            return False
        if any(pattern in text for pattern in self.patterns):
            return True
        if not self.fuzzy or not _looks_like_route_intent(text, self.intent_terms):
            return False
        normalized_text = _normalize_for_l0_intent(text)
        for pattern in self.patterns:
            normalized_pattern = _normalize_for_l0_intent(pattern)
            if len(normalized_pattern) >= 3 and _best_substring_ratio(normalized_text, normalized_pattern) >= FUZZY_MIN_RATIO:
                return True
        return False


L0_TEXT_ROUTE_REGISTRY: tuple[L0Route, ...] = (
    L0Route("access_layer", ACCESS_LAYER_QUERY_PATTERNS, description="Access Brain taxonomy and layer naming"),
    L0Route("capability", CAPABILITY_QUERY_PATTERNS, description="Voice-friendly capability menu"),
    L0Route(
        "manufacturing_status",
        MANUFACTURING_STATUS_PATTERNS,
        description="Read-only manufacturing cache summary",
        intent_terms=("制造脑", "打印", "打印机", "拓竹", "bambu", "x2d", "ams", "料盘", "温度"),
        fuzzy=True,
    ),
    L0Route("daily_brief", DAILY_BRIEF_PATTERNS, description="Read-only daily brief cache summary"),
    L0Route(
        "rokid_developer_resources",
        ROKID_DEVELOPER_RESOURCE_PATTERNS,
        description="Read-only Rokid developer resource entrypoints",
        intent_terms=("rokid", "开发", "文档", "资源", "sdk", "yodaos", "sprite", "开放平台"),
        fuzzy=True,
    ),
    L0Route(
        "local_brain_stats",
        BRAIN_STATS_PATTERNS,
        description="Read-only local brain stats cache summary",
        intent_terms=("本地大脑", "本地电脑", "任务池", "任务", "待办", "多脑", "大脑"),
        fuzzy=True,
    ),
)
L0_ROUTE_REGISTRY = L0_TEXT_ROUTE_REGISTRY


def route_ids(routes: Iterable[L0Route]) -> list[str]:
    return [route.route_id for route in routes]


def match_text_route(user_text: str, routes: Iterable[L0Route] = L0_TEXT_ROUTE_REGISTRY) -> L0Route | None:
    for route in routes:
        if route.matches(user_text):
            return route
    return None

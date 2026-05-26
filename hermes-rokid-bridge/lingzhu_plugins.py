"""Declarative Lingzhu platform plugin registry for Rokid glasses entry.

This module does not call Rokid/Lingzhu APIs. It gives the Hermes SSE bridge a
stable, testable contract for recognizing capabilities that should be handled by
Lingzhu native plugins when the platform can execute them, while keeping Hermes
fail-closed when no plugin execution receipt is present.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Literal

RiskTier = Literal["low", "medium", "high", "critical"]
Capability = Literal[
    "device_info",
    "weather",
    "location",
    "photo",
    "navigation",
    "exit_agent",
    "payment",
    "calculator",
]


UNSAFE_PLUGIN_COMPLETION_CLAIMS: tuple[str, ...] = (
    "已拍照",
    "拍照成功",
    "照片已拍",
    "已导航",
    "导航已开始",
    "开始导航",
    "已退出",
    "退出成功",
    "已支付",
    "支付成功",
    "付款成功",
    "已付款",
    "已打开计算器",
)


@dataclass(frozen=True)
class LingzhuPlugin:
    plugin_id: str
    display_name: str
    capability: Capability
    native_intents: tuple[str, ...]
    risk_tier: RiskTier
    confirmation_required: bool
    fallback_message: str

    def matches(self, user_text: str) -> bool:
        text = str(user_text or "").strip()
        return bool(text and any(intent in text for intent in self.native_intents))


LINGZHU_PLUGIN_REGISTRY: tuple[LingzhuPlugin, ...] = (
    LingzhuPlugin(
        plugin_id="glasses_info.device_status",
        display_name="乐奇AI眼镜信息获取：设备状态",
        capability="device_info",
        native_intents=("眼镜电量", "电量", "电池", "眼镜状态", "设备状态", "网络状态"),
        risk_tier="low",
        confirmation_required=False,
        fallback_message="眼镜状态应优先由灵珠信息获取插件读取；本次没有插件回执时，我只能播报请求上下文里已有的信息，不会猜测。",
    ),
    LingzhuPlugin(
        plugin_id="glasses_info.location",
        display_name="乐奇AI眼镜信息获取：位置",
        capability="location",
        native_intents=("我的位置", "当前位置", "现在位置", "本地位置", "获取位置", "获取本地位置", "我在哪里", "我在哪", "定位一下", "经纬度"),
        risk_tier="low",
        confirmation_required=False,
        fallback_message="位置应优先由灵珠信息获取插件读取；没有插件回执时，我只能使用本次请求上下文，不会猜位置。",
    ),
    LingzhuPlugin(
        plugin_id="glasses_info.weather",
        display_name="乐奇AI眼镜信息获取：天气",
        capability="weather",
        native_intents=("天气", "当前天气", "现在天气", "今天天气"),
        risk_tier="low",
        confirmation_required=False,
        fallback_message="天气应优先由灵珠信息获取插件读取；没有插件回执时，我不会编造实时天气。",
    ),
    LingzhuPlugin(
        plugin_id="glasses_control.photo",
        display_name="乐奇AI眼镜控制插件：拍照",
        capability="photo",
        native_intents=("拍照", "拍一张", "照一张", "帮我拍", "用眼镜拍"),
        risk_tier="high",
        confirmation_required=True,
        fallback_message="拍照需要灵珠眼镜控制插件和你的确认。当前 Hermes 没有收到插件执行回执，不能声称已经拍照。请在灵珠端确认拍照，或说“后台分析图片”处理已发送图片。",
    ),
    LingzhuPlugin(
        plugin_id="glasses_control.navigation",
        display_name="乐奇AI眼镜控制插件：导航",
        capability="navigation",
        native_intents=("导航到", "开始导航", "带我去", "路线到", "去哪里怎么走"),
        risk_tier="high",
        confirmation_required=True,
        fallback_message="导航会影响现实行动，需要灵珠眼镜控制插件和目的地确认。当前没有插件执行回执，不能声称动作完成。请确认目的地后由灵珠插件执行。",
    ),
    LingzhuPlugin(
        plugin_id="glasses_control.exit",
        display_name="乐奇AI眼镜控制插件：退出",
        capability="exit_agent",
        native_intents=("退出当前智能体", "退出智能体", "关闭当前智能体", "结束对话", "退出"),
        risk_tier="high",
        confirmation_required=True,
        fallback_message="退出智能体需要灵珠控制插件执行。当前没有插件回执，我不能声称已经退出；你可以在眼镜端确认退出。",
    ),
    LingzhuPlugin(
        plugin_id="alipay.ai_pay",
        display_name="支付宝AI付",
        capability="payment",
        native_intents=("支付宝付款", "支付宝支付", "付款", "支付", "买单", "付钱"),
        risk_tier="critical",
        confirmation_required=True,
        fallback_message="支付是高风险动作，必须核对金额、商户和二次确认，并由支付宝AI付插件返回回执。当前 Hermes 没有支付回执，不能确认支付完成。",
    ),
    LingzhuPlugin(
        plugin_id="calculator.basic",
        display_name="计算器",
        capability="calculator",
        native_intents=("计算器", "算一下", "帮我算", "算下", "算算", "计算", "等于多少"),
        risk_tier="low",
        confirmation_required=False,
        fallback_message="计算可以由灵珠计算器插件或 Hermes 本地计算处理；没有插件回执时，我可以给出普通文本计算建议，但不会伪造插件结果。",
    ),
)


def match_lingzhu_plugin(user_text: str, registry: Iterable[LingzhuPlugin] = LINGZHU_PLUGIN_REGISTRY) -> LingzhuPlugin | None:
    """Return the first Lingzhu native plugin matching the utterance."""
    for plugin in registry:
        if plugin.matches(user_text):
            return plugin
    return None


def extract_lingzhu_plugin_context(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize possible Lingzhu plugin receipt locations from request metadata.

    The current public SSE examples do not document native-plugin receipts for
    third-party agents. Keep this parser deliberately tolerant but read-only:
    it only extracts receipt-like metadata that the platform already supplied;
    it never creates or executes a plugin action.
    """
    if not isinstance(metadata, Mapping):
        return {}
    context = metadata.get("context") if isinstance(metadata.get("context"), Mapping) else {}
    candidates = (
        metadata.get("lingzhu_plugin_receipts"),
        metadata.get("pluginReceipts"),
        metadata.get("plugin_receipts"),
        context.get("lingzhu_plugin_receipts") if isinstance(context, Mapping) else None,
        context.get("pluginReceipts") if isinstance(context, Mapping) else None,
        context.get("plugin_receipts") if isinstance(context, Mapping) else None,
    )
    for receipts in candidates:
        if isinstance(receipts, Mapping):
            return {"lingzhu_plugin_receipts": receipts}
    return {}


def _receipt_for(plugin: LingzhuPlugin, context: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    receipts = (context or {}).get("lingzhu_plugin_receipts")
    if not isinstance(receipts, Mapping):
        return None
    receipt = receipts.get(plugin.plugin_id) or receipts.get(plugin.capability) or receipts.get(plugin.display_name)
    return receipt if isinstance(receipt, Mapping) else None


def can_execute_plugin(plugin: LingzhuPlugin | None, context: Mapping[str, Any] | None = None) -> bool:
    """Fail closed unless the platform provides an explicit execution receipt.

    The SSE bridge itself does not execute native plugins. A plugin is considered
    executed only when a caller supplies a receipt for that exact plugin_id with a
    successful status and an id/token/evidence field.
    """
    if plugin is None:
        return False
    receipt = _receipt_for(plugin, context)
    if not receipt:
        return False
    status = str(receipt.get("status") or receipt.get("result") or "").lower()
    has_evidence = bool(receipt.get("receipt_id") or receipt.get("id") or receipt.get("evidence") or receipt.get("token"))
    return status in {"ok", "success", "executed", "done"} and has_evidence


def build_plugin_receipted_answer(plugin: LingzhuPlugin, context: Mapping[str, Any] | None = None) -> str:
    """Voice-safe answer when Lingzhu supplied an execution receipt.

    Use receipt-grounded wording instead of unsafe completion phrases like
    "已拍照" or "付款成功". The receipt proves the platform reported success;
    Hermes still does not claim it personally performed the real-world action.
    """
    receipt = _receipt_for(plugin, context) or {}
    receipt_id = receipt.get("receipt_id") or receipt.get("id") or receipt.get("evidence") or "已收到"
    return f"收到灵珠平台插件回执：{plugin.display_name}，回执编号：{receipt_id}。我会按这个平台回执继续后续处理。"


def build_plugin_unavailable_answer(plugin: LingzhuPlugin | None, user_text: str = "") -> str:
    """Voice-safe fail-closed answer when a Lingzhu capability is recognized but not receipted."""
    if plugin is None:
        return "这个请求没有匹配到可用的灵珠平台插件；我会按 Hermes 普通能力处理。"
    confirm = "需要先确认。" if plugin.confirmation_required else "这是只读/低风险能力。"
    base = plugin.fallback_message
    if "不能声称" not in base:
        base += " 当前没有插件回执，不能声称已经执行完成。"
    elif "不能声称已经执行" not in base:
        base += " 当前没有插件回执，不能声称已经执行完成。"
    return f"识别到灵珠平台插件：{plugin.display_name}。{confirm}{base}"

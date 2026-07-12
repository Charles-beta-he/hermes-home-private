import json
import sys
import time
import urllib.request
from pathlib import Path

import websocket

BASE = "http://127.0.0.1:4188"
URL = BASE + "/contract/calculator?tradeId=1035922175497863168"
PORT = 9228

pages = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
ws = websocket.create_connection(
    next(page["webSocketDebuggerUrl"] for page in pages if page.get("type") == "page"),
    timeout=30,
)
request_id = 0


def call(method, params=None):
    global request_id
    request_id += 1
    current = request_id
    ws.send(json.dumps({"id": current, "method": method, "params": params or {}}))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == current:
            if "error" in message:
                raise RuntimeError(message["error"])
            return message.get("result", {})


def evaluate(expression):
    result = call(
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True, "awaitPromise": True},
    )["result"]
    if result.get("subtype") == "error":
        raise RuntimeError(result.get("description"))
    return result.get("value")


def click_text(text):
    return evaluate(
        """(() => {
          const text = %s;
          const node = Array.from(document.querySelectorAll('button')).find(
            (item) => item.textContent?.trim() === text
          );
          if (!node) return false;
          node.click();
          return true;
        })()""" % json.dumps(text, ensure_ascii=False)
    )


def set_input(label, value):
    return evaluate(
        """(() => {
          const labelText = %s;
          const value = %s;
          const label = Array.from(document.querySelectorAll('label')).find(
            (item) => item.querySelector('span')?.textContent?.trim() === labelText
          );
          const input = label?.querySelector('input');
          if (!input) return false;
          const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
          setter.call(input, value);
          input.dispatchEvent(new Event('input', { bubbles: true }));
          return true;
        })()""" % (json.dumps(label, ensure_ascii=False), json.dumps(value))
    )


def result_rows():
    return evaluate(
        """(() => Array.from(document.querySelectorAll('section[aria-live="polite"] > div')).map(
          (row) => ({
            label: row.querySelector('span')?.textContent?.trim() || '',
            value: row.querySelector('strong')?.textContent?.trim() || '',
          })
        ))()"""
    )


def wait_until(expression: str, timeout: float = 10.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if evaluate(expression):
            return True
        time.sleep(0.2)
    return False


call("Page.enable")
call("Network.enable")
call(
    "Emulation.setDeviceMetricsOverride",
    {"width": 390, "height": 640, "deviceScaleFactor": 2, "mobile": True},
)
call("Network.setCacheDisabled", {"cacheDisabled": True})
call("Page.navigate", {"url": URL})
time.sleep(4)

initial = evaluate(
    """(() => ({
      url: location.href,
      title: document.querySelector('header h1')?.textContent?.trim() || '',
      tabs: Array.from(document.querySelectorAll('[role="tab"]')).map((tab) => tab.textContent?.trim()),
      selectedContract: document.querySelector('select')?.selectedOptions[0]?.textContent?.trim() || '',
      headerTop: document.querySelector('header')?.getBoundingClientRect().top,
      viewport: { width: innerWidth, height: innerHeight },
      noHorizontalOverflow: document.documentElement.scrollWidth === innerWidth,
      error: document.querySelector('[role="alert"]')?.textContent?.trim() || '',
    }))()"""
)
evaluate("window.scrollTo(0, 320); true")
time.sleep(0.3)
header_after_scroll = evaluate(
    """(() => ({
      scrollY: window.scrollY,
      top: document.querySelector('header')?.getBoundingClientRect().top,
      bottom: document.querySelector('header')?.getBoundingClientRect().bottom,
    }))()"""
)
evaluate("window.scrollTo(0, 0); true")
assert click_text("计算")
time.sleep(0.2)
invalid_input_error = evaluate("document.querySelector('[role=\"alert\"]')?.textContent?.trim() || ''")

assert click_text("平仓价格")
time.sleep(0.2)
assert set_input("杠杆倍数（1–125）", "10")
assert set_input("开仓价格", "100")
assert set_input("预期收益", "100")
assert set_input("开仓数量", "2")
assert click_text("计算")
time.sleep(0.2)
target_rows = result_rows()
target_error = evaluate("document.querySelector('[role=\"alert\"]')?.textContent?.trim() || ''")

assert click_text("收益计算")
time.sleep(0.2)
assert set_input("开仓价格", "100")
assert set_input("平仓价格", "110")
assert set_input("开仓数量", "2")
assert click_text("计算")
time.sleep(0.2)
profit_rows = result_rows()
profit_error = evaluate("document.querySelector('[role=\"alert\"]')?.textContent?.trim() || ''")

assert set_input("杠杆倍数（1–125）", "126")
assert click_text("计算")
time.sleep(0.2)
leverage_clamp = {
    "value": evaluate(
        "Array.from(document.querySelectorAll('label')).find((item) => item.querySelector('span')?.textContent?.trim() === '杠杆倍数（1–125）')?.querySelector('input')?.value || ''"
    ),
    "rows": result_rows(),
    "error": evaluate("document.querySelector('[role=\"alert\"]')?.textContent?.trim() || ''"),
}
assert set_input("杠杆倍数（1–125）", "10")

assert click_text("强平价格")
time.sleep(2)
assert set_input("开仓价格", "100")
assert set_input("开仓数量", "10")
assert set_input("增加保证金", "20")
assert click_text("计算")
time.sleep(0.2)
isolated_rows = result_rows()
isolated_error = evaluate("document.querySelector('[role=\"alert\"]')?.textContent?.trim() || ''")

assert click_text("全仓")
assert wait_until(
    "Array.from(document.querySelectorAll('button')).some((node) => node.textContent?.trim() === '计算')"
)
assert set_input("可用保证金", "20")
assert click_text("计算")
time.sleep(0.2)
cross_rows = result_rows()
cross_error = evaluate("document.querySelector('[role=\"alert\"]')?.textContent?.trim() || ''")

trade_url = BASE + "/contract?tradeName=SOLUSDT%20%E6%B0%B8%E7%BB%AD&symbol=sol_usdt_sustainable&tradeId=1035922175497863168"
call("Page.navigate", {"url": trade_url})
time.sleep(4)
entry_before_click = evaluate(
    """(() => {
      const button = document.querySelector('button[aria-label="打开合约计算器"]');
      return {
        exists: Boolean(button),
        currentTrade: document.querySelector('button[aria-label="选择合约交易对"] span')?.textContent?.trim() || '',
      };
    })()"""
)
evaluate("document.querySelector('button[aria-label=\"打开合约计算器\"]')?.click(); true")
time.sleep(1)
entry_after_click_url = evaluate("location.href")

result = {
    "initial": initial,
    "headerAfterScroll": header_after_scroll,
    "invalidInputError": invalid_input_error,
    "target": {"rows": target_rows, "error": target_error},
    "profit": {"rows": profit_rows, "error": profit_error},
    "leverageClamp": leverage_clamp,
    "isolatedLiquidation": {"rows": isolated_rows, "error": isolated_error},
    "crossLiquidation": {"rows": cross_rows, "error": cross_error},
    "entry": {
        "beforeClick": entry_before_click,
        "afterClickUrl": entry_after_click_url,
    },
}

passed = (
    initial["url"].startswith(URL)
    and initial["title"] == "合约计算器"
    and initial["tabs"] == ["收益计算", "平仓价格", "强平价格"]
    and initial["selectedContract"] == "SOLUSDT 永续"
    and initial["headerTop"] == 0
    and initial["viewport"] == {"width": 390, "height": 640}
    and initial["noHorizontalOverflow"]
    and header_after_scroll["scrollY"] > 0
    and header_after_scroll["top"] == 0
    and invalid_input_error == "请填写有效且大于零的计算参数"
    and not target_error
    and target_rows == [{"label": "目标平仓价格", "value": "150.00 USDT"}]
    and not profit_error
    and [row["label"] for row in profit_rows]
    == ["保证金", "收益", "收益率", "Maker手续费", "Taker手续费"]
    and leverage_clamp["value"] == "125"
    and not leverage_clamp["error"]
    and next(row["value"] for row in leverage_clamp["rows"] if row["label"] == "保证金")
    == "1.60 USDT"
    and next(row["value"] for row in leverage_clamp["rows"] if row["label"] == "收益率")
    == "1250.00%"
    and not isolated_error
    and len(isolated_rows) == 1
    and isolated_rows[0]["label"] == "强平价格"
    and not cross_error
    and len(cross_rows) == 1
    and cross_rows[0]["label"] == "强平价格"
    and entry_before_click["exists"]
    and entry_before_click["currentTrade"] == "SOLUSDT 永续"
    and entry_after_click_url
    == BASE + "/contract/calculator?tradeId=1035922175497863168"
)
result["passed"] = passed
output_path = Path(__file__).with_name("contract-calculator-runtime-390x640.json")
output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
ws.close()
sys.exit(0 if passed else 1)

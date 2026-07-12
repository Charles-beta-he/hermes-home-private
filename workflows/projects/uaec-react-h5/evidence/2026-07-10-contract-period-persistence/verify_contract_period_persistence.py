import json
import sys
import time
import urllib.request

import websocket

PAGE_URL = (
    "http://127.0.0.1:4183/contract/contract-interface"
    "?tradeName=SOLUSDT%20%E6%B0%B8%E7%BB%AD"
    "&symbol=sol_usdt_sustainable"
    "&tradeId=1035922175497863168"
)
STORAGE_KEY = "uaec.contract.kline.period"


def page_ws_url():
    pages = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
    return next(page["webSocketDebuggerUrl"] for page in pages if page.get("type") == "page")


class CDP:
    def __init__(self):
        self.ws = websocket.create_connection(page_ws_url(), timeout=20)
        self.request_id = 0

    def call(self, method, params=None):
        self.request_id += 1
        request_id = self.request_id
        self.ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    def eval(self, expression):
        return self.call(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
        ).get("result", {}).get("value")


cdp = CDP()
cdp.call("Page.enable")
cdp.call("Network.enable")
cdp.call("Network.setCacheDisabled", {"cacheDisabled": True})
cdp.call(
    "Storage.clearDataForOrigin",
    {
        "origin": "http://127.0.0.1:4183",
        "storageTypes": "cache_storage,service_workers",
    },
)
cdp.call("Page.navigate", {"url": f"{PAGE_URL}&cacheBust={int(time.time())}"})
time.sleep(3)
cdp.eval(f"localStorage.removeItem({json.dumps(STORAGE_KEY)})")
cdp.call("Page.reload", {"ignoreCache": True})
time.sleep(5)

before = cdp.eval(
    f"""
    (() => {{
      const selected = [...document.querySelectorAll('button[aria-pressed="true"]')]
        .find((node) => node.textContent.trim().includes('分'));
      return {{ selected: selected?.textContent.trim() || '', stored: localStorage.getItem({json.dumps(STORAGE_KEY)}) }};
    }})()
    """
)

selected = cdp.eval(
    f"""
    (async () => {{
      const button = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '30分');
      button?.click();
      await new Promise((resolve) => setTimeout(resolve, 300));
      return {{
        found: Boolean(button),
        pressed: button?.getAttribute('aria-pressed') || '',
        stored: localStorage.getItem({json.dumps(STORAGE_KEY)})
      }};
    }})()
    """
)

cdp.call("Page.reload", {"ignoreCache": True})
time.sleep(5)
after = cdp.eval(
    f"""
    (() => {{
      const button = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '30分');
      const selectedButtons = [...document.querySelectorAll('button[aria-pressed="true"]')]
        .map((node) => node.textContent.trim())
        .filter(Boolean);
      return {{
        pressed: button?.getAttribute('aria-pressed') || '',
        selectedButtons,
        stored: localStorage.getItem({json.dumps(STORAGE_KEY)})
      }};
    }})()
    """
)

cdp.eval(f"localStorage.setItem({json.dumps(STORAGE_KEY)}, 'unsupported-period')")
cdp.call("Page.reload", {"ignoreCache": True})
time.sleep(5)
invalid = cdp.eval(
    f"""
    (() => {{
      const selected = [...document.querySelectorAll('button[aria-pressed="true"]')]
        .find((node) => node.textContent.trim().includes('分'));
      return {{
        selected: selected?.textContent.trim() || '',
        stored: localStorage.getItem({json.dumps(STORAGE_KEY)})
      }};
    }})()
    """
)

depth = cdp.eval(
    f"""
    (async () => {{
      localStorage.setItem({json.dumps(STORAGE_KEY)}, 'min30');
      const button = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '深度图');
      button?.click();
      await new Promise((resolve) => setTimeout(resolve, 300));
      return {{
        found: Boolean(button),
        stored: localStorage.getItem({json.dumps(STORAGE_KEY)})
      }};
    }})()
    """
)

result = {
    "before": before,
    "selected": selected,
    "afterReload": after,
    "invalidFallback": invalid,
    "depthSelection": depth,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
cdp.ws.close()
passed = (
    selected.get("found")
    and selected.get("pressed") == "true"
    and selected.get("stored") == "min30"
    and after.get("pressed") == "true"
    and after.get("stored") == "min30"
    and invalid.get("selected") == "15分"
    and invalid.get("stored") == "unsupported-period"
    and depth.get("found")
    and depth.get("stored") == "min30"
)
sys.exit(0 if passed else 1)

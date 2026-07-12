import base64
import json
import pathlib
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
PERIOD_KEY = "uaec.contract.kline.period"
VIEW_KEY = "uaec.contract.kline.view"
SCREENSHOT = pathlib.Path(__file__).with_name("contract-depth-restored-390x844.png")


def page_ws_url():
    pages = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
    return next(
        page["webSocketDebuggerUrl"]
        for page in pages
        if page.get("type") == "page" and page.get("url", "").startswith("http")
    )


class CDP:
    def __init__(self):
        self.ws = websocket.create_connection(page_ws_url(), timeout=30)
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
    "Emulation.setDeviceMetricsOverride",
    {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True},
)
cdp.call(
    "Storage.clearDataForOrigin",
    {"origin": "http://127.0.0.1:4183", "storageTypes": "cache_storage,service_workers"},
)
cdp.call("Page.navigate", {"url": f"{PAGE_URL}&depthPersistence={int(time.time())}"})
time.sleep(3)
cdp.eval(
    f"localStorage.setItem({json.dumps(PERIOD_KEY)}, 'min30');"
    f"localStorage.removeItem({json.dumps(VIEW_KEY)});"
)
cdp.call("Page.reload", {"ignoreCache": True})
time.sleep(4)

selected_depth = cdp.eval(
    f"""
    (async () => {{
      const button = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '深度图');
      button?.click();
      await new Promise((resolve) => setTimeout(resolve, 300));
      return {{
        found: Boolean(button),
        pressed: button?.getAttribute('aria-pressed') || '',
        storedPeriod: localStorage.getItem({json.dumps(PERIOD_KEY)}),
        storedView: localStorage.getItem({json.dumps(VIEW_KEY)})
      }};
    }})()
    """
)

cdp.call("Page.reload", {"ignoreCache": True})
time.sleep(4)
after_depth_reload = cdp.eval(
    f"""
    (() => {{
      const depth = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '深度图');
      depth?.scrollIntoView({{ behavior: 'instant', block: 'nearest', inline: 'end' }});
      return {{
        pressed: depth?.getAttribute('aria-pressed') || '',
        storedPeriod: localStorage.getItem({json.dumps(PERIOD_KEY)}),
        storedView: localStorage.getItem({json.dumps(VIEW_KEY)})
      }};
    }})()
    """
)
time.sleep(0.3)
SCREENSHOT.write_bytes(
    base64.b64decode(
        cdp.call(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": False},
        )["data"]
    )
)

selected_period = cdp.eval(
    f"""
    (async () => {{
      const button = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '30分');
      button?.click();
      await new Promise((resolve) => setTimeout(resolve, 300));
      return {{
        found: Boolean(button),
        pressed: button?.getAttribute('aria-pressed') || '',
        storedPeriod: localStorage.getItem({json.dumps(PERIOD_KEY)}),
        storedView: localStorage.getItem({json.dumps(VIEW_KEY)})
      }};
    }})()
    """
)

cdp.call("Page.reload", {"ignoreCache": True})
time.sleep(4)
after_period_reload = cdp.eval(
    f"""
    (() => {{
      const period = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '30分');
      return {{
        pressed: period?.getAttribute('aria-pressed') || '',
        storedPeriod: localStorage.getItem({json.dumps(PERIOD_KEY)}),
        storedView: localStorage.getItem({json.dumps(VIEW_KEY)})
      }};
    }})()
    """
)

result = {
    "selectedDepth": selected_depth,
    "afterDepthReload": after_depth_reload,
    "selectedPeriod": selected_period,
    "afterPeriodReload": after_period_reload,
    "screenshot": str(SCREENSHOT),
}
print(json.dumps(result, ensure_ascii=False, indent=2))
cdp.ws.close()

passed = (
    selected_depth.get("found")
    and selected_depth.get("pressed") == "true"
    and selected_depth.get("storedPeriod") == "min30"
    and selected_depth.get("storedView") == "depth"
    and after_depth_reload.get("pressed") == "true"
    and after_depth_reload.get("storedPeriod") == "min30"
    and after_depth_reload.get("storedView") == "depth"
    and selected_period.get("found")
    and selected_period.get("pressed") == "true"
    and selected_period.get("storedPeriod") == "min30"
    and selected_period.get("storedView") is None
    and after_period_reload.get("pressed") == "true"
    and after_period_reload.get("storedPeriod") == "min30"
    and after_period_reload.get("storedView") is None
)
sys.exit(0 if passed else 1)

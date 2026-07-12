import base64
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

import websocket

BASE_URL = "http://127.0.0.1:4183/contract"
SCREENSHOT = pathlib.Path(__file__).with_name("contract-sell-entry-intent-390x844.png")
PAIR_PARAMS = {
    "tradeName": "SOLUSDT 永续",
    "symbol": "sol_usdt_sustainable",
    "tradeId": "1035922175497863168",
}


def page_ws_url():
    pages = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
    return next(page["webSocketDebuggerUrl"] for page in pages if page.get("type") == "page")


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


def navigate_case(cdp, side, buyselltype):
    params = {**PAIR_PARAMS, "side": side, "buyselltype": buyselltype}
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    cdp.call("Page.navigate", {"url": url})
    time.sleep(5)
    return cdp.eval(
        """
        (() => {
          const buy = document.querySelector('button[aria-label^="合约开多下单"]');
          const sell = document.querySelector('button[aria-label^="合约开空下单"]');
          const heading = document.body.innerText;
          return {
            url: location.href,
            pairVisible: heading.includes('SOLUSDT'),
            buyIntent: buy?.dataset.entryIntent || '',
            sellIntent: sell?.dataset.entryIntent || '',
            buyLabel: buy?.getAttribute('aria-label') || '',
            sellLabel: sell?.getAttribute('aria-label') || ''
          };
        })()
        """
    )


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

buy = navigate_case(cdp, "buy", "BUY")
sell = navigate_case(cdp, "sell", "SELL")
cdp.eval(
    "document.querySelector('button[data-entry-intent=\"active\"]')?.scrollIntoView({block: 'center'}); true"
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
cdp.ws.close()
result = {"buy": buy, "sell": sell, "screenshot": str(SCREENSHOT)}
print(json.dumps(result, ensure_ascii=False, indent=2))

passed = (
    buy.get("pairVisible")
    and buy.get("buyIntent") == "active"
    and buy.get("sellIntent") == ""
    and "当前入口" in buy.get("buyLabel", "")
    and sell.get("pairVisible")
    and sell.get("sellIntent") == "active"
    and sell.get("buyIntent") == ""
    and "当前入口" in sell.get("sellLabel", "")
)
sys.exit(0 if passed else 1)

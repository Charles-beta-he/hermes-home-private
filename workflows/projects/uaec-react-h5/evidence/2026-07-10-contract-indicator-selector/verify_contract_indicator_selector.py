import json
import sys
import time
import urllib.request

import websocket

PAGE_URL = (
    "http://127.0.0.1:4183/contract/contract-interface"
    "?tradeName=SOLUSDT%20%E6%B0%B8%E7%BB%AD"
    "&symbol=sol_usdt_sustainable&tradeId=1035922175497863168"
)


def page_ws_url():
    pages = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
    return next(page["webSocketDebuggerUrl"] for page in pages if page.get("type") == "page")


class CDP:
    def __init__(self):
        self.ws = websocket.create_connection(page_ws_url(), timeout=20)
        self.request_id = 0
        self.exceptions = []

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
            if message.get("method") == "Runtime.exceptionThrown":
                details = message.get("params", {}).get("exceptionDetails", {})
                exception = details.get("exception", {})
                self.exceptions.append(
                    exception.get("description")
                    or exception.get("value")
                    or details.get("text", "Runtime exception")
                )

    def eval(self, expression):
        return self.call(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
        ).get("result", {}).get("value")


cdp = CDP()
cdp.call("Page.enable")
cdp.call("Runtime.enable")
cdp.call("Network.enable")
cdp.call("Network.setCacheDisabled", {"cacheDisabled": True})
cdp.eval("localStorage.setItem('uaec.contract.kline.view', 'kline')")
cdp.call(
    "Storage.clearDataForOrigin",
    {
        "origin": "http://127.0.0.1:4183",
        "storageTypes": "cache_storage,service_workers",
    },
)
cdp.call("Page.navigate", {"url": f"{PAGE_URL}&cacheBust={int(time.time())}"})
time.sleep(5)
cdp.exceptions.clear()

result = cdp.eval(
    """
    (async () => {
      const button = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '指标');
      if (!button) return { found: false };
      button.click();
      await new Promise((resolve) => setTimeout(resolve, 300));
      const panel = document.querySelector('[aria-label="K线技术指标"]');
      const findOption = (label) => [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === label && panel?.contains(node));
      const findByAria = (label) => panel?.querySelector(`button[aria-label="${label}"]`);
      const selections = {};
      for (const label of ['MA', 'BOLL']) {
        const option = findOption(label);
        option?.click();
        await new Promise((resolve) => setTimeout(resolve, 200));
        selections[label] = option?.getAttribute('aria-pressed') === 'true';
      }
      const closeMain = findByAria('关闭主图指标');
      closeMain?.click();
      await new Promise((resolve) => setTimeout(resolve, 200));
      selections.closeMain = closeMain?.getAttribute('aria-pressed') === 'true';
      for (const label of ['MACD', 'KDJ', 'RSI', 'WR']) {
        const option = findOption(label);
        option?.click();
        await new Promise((resolve) => setTimeout(resolve, 200));
        selections[label] = option?.getAttribute('aria-pressed') === 'true';
      }
      const closeSub = findByAria('关闭副图指标');
      closeSub?.click();
      await new Promise((resolve) => setTimeout(resolve, 200));
      selections.closeSub = closeSub?.getAttribute('aria-pressed') === 'true';
      const boll = findOption('BOLL');
      boll?.click();
      await new Promise((resolve) => setTimeout(resolve, 200));
      const kdj = findOption('KDJ');
      kdj?.click();
      await new Promise((resolve) => setTimeout(resolve, 300));
      const chart = document.querySelector('[data-chart-adapter="klinecharts"]');
      const paneCount = [...(chart?.firstElementChild?.children || [])]
        .filter((node) => node.children.length === 2 && node.style.overflow === 'hidden')
        .length;
      const pressed = (label) => findOption(label)?.getAttribute('aria-pressed');
      return {
        found: true,
        expanded: button.getAttribute('aria-expanded'),
        panel: Boolean(panel),
        bollClicked: Boolean(boll),
        kdjClicked: Boolean(kdj),
        selections,
        bollPressed: pressed('BOLL'),
        kdjPressed: pressed('KDJ'),
        mainIndicator: chart?.getAttribute('data-main-indicator') || '',
        subIndicator: chart?.getAttribute('data-sub-indicator') || '',
        paneCount
      };
    })()
    """
)
result["exceptionCount"] = len(cdp.exceptions)
result["exceptions"] = cdp.exceptions
result["unexpectedExceptions"] = [
    exception for exception in cdp.exceptions if exception != "Event"
]
print(json.dumps(result, ensure_ascii=False, indent=2))
cdp.ws.close()

passed = bool(
    result
    and result.get("found")
    and result.get("expanded") == "true"
    and result.get("panel")
    and result.get("bollClicked")
    and result.get("kdjClicked")
    and result.get("bollPressed") == "true"
    and result.get("kdjPressed") == "true"
    and result.get("mainIndicator") == "BOLL"
    and result.get("subIndicator") == "KDJ"
    and result.get("paneCount") == 3
    and all(result.get("selections", {}).values())
    and len(result.get("selections", {})) == 8
    and not result.get("unexpectedExceptions")
)
sys.exit(0 if passed else 1)

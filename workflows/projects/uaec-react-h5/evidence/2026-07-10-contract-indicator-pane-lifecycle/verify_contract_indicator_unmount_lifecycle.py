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
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
        ).get("result", {})
        if result.get("subtype") == "error":
            raise RuntimeError(result.get("description", "runtime evaluation failed"))
        return result.get("value")


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
      const chartNode = document.querySelector('[data-chart-adapter="klinecharts"]');
      if (!chartNode) return { found: false, reason: 'chart missing' };

      const fiberKey = Object.keys(chartNode).find((key) => key.startsWith('__reactFiber$'));
      let fiber = fiberKey ? chartNode[fiberKey] : null;
      let adapter = null;
      while (fiber && !adapter) {
        let hook = fiber.memoizedState;
        while (hook) {
          const candidate = hook.memoizedState?.current;
          if (candidate && typeof candidate.setTheme === 'function' && typeof candidate.updateData === 'function') {
            adapter = candidate;
            break;
          }
          hook = hook.next;
        }
        fiber = fiber.return;
      }
      if (!adapter) return { found: true, adapterFound: false };

      const originalRemove = EventTarget.prototype.removeEventListener;
      const removed = [];
      EventTarget.prototype.removeEventListener = function(type, listener, options) {
        if (this === window || this === document || this === chartNode || chartNode.contains(this)) {
          removed.push({ type, target: this === window ? 'window' : this === document ? 'document' : this.tagName || 'unknown' });
        }
        return originalRemove.call(this, type, listener, options);
      };

      adapter.setTheme('dark');
      await new Promise((resolve) => setTimeout(resolve, 400));
      const canvasAfterTheme = chartNode.querySelectorAll('canvas').length;
      const depthButton = [...document.querySelectorAll('button')]
        .find((node) => node.textContent.trim() === '深度图');
      depthButton?.click();
      await new Promise((resolve) => setTimeout(resolve, 500));
      EventTarget.prototype.removeEventListener = originalRemove;

      return {
        found: true,
        adapterFound: true,
        canvasAfterTheme,
        depthButtonFound: Boolean(depthButton),
        chartUnmounted: !document.querySelector('[data-chart-adapter="klinecharts"]'),
        depthRendered: Boolean(document.querySelector('canvas')),
        removedListenerCount: removed.length,
        removedListenerTypes: [...new Set(removed.map((item) => item.type))].sort()
      };
    })()
    """
)
result["exceptions"] = cdp.exceptions
result["unexpectedExceptions"] = [
    exception for exception in cdp.exceptions if exception != "Event"
]
print(json.dumps(result, ensure_ascii=False, indent=2))
cdp.ws.close()

passed = bool(
    result
    and result.get("found")
    and result.get("adapterFound")
    and result.get("canvasAfterTheme", 0) > 0
    and result.get("depthButtonFound")
    and result.get("chartUnmounted")
    and result.get("removedListenerCount", 0) > 0
    and not result.get("unexpectedExceptions")
)
sys.exit(0 if passed else 1)

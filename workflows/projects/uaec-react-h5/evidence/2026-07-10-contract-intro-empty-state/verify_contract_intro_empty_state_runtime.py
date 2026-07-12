import json
import sys
import time
import urllib.parse
import urllib.request

import websocket

URL = "http://127.0.0.1:4183/contract/contract-interface?" + urllib.parse.urlencode({
    "tradeName": "SOLUSDT 永续",
    "symbol": "sol_usdt_sustainable",
    "tradeId": "1035922175497863168",
})
pages = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
ws = websocket.create_connection(next(p["webSocketDebuggerUrl"] for p in pages if p.get("type") == "page"), timeout=30)
request_id = 0


def call(method, params=None):
    global request_id
    request_id += 1
    current = request_id
    ws.send(json.dumps({"id": current, "method": method, "params": params or {}}))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == current:
            return message.get("result", {})


def evaluate(expression):
    return call("Runtime.evaluate", {"expression": expression, "returnByValue": True})["result"].get("value")


call("Page.enable")
call("Network.enable")
call("Network.setCacheDisabled", {"cacheDisabled": True})
call("Network.setBlockedURLs", {"urls": ["*cms/TheCoinInformation*"]})
call("Page.navigate", {"url": URL})
time.sleep(5)
evaluate("Array.from(document.querySelectorAll('button')).find((button) => button.textContent?.trim() === '简介')?.click(); true")
time.sleep(2)
result = evaluate("""(() => {
  const status = document.querySelector('[role="status"]');
  const selected = Array.from(document.querySelectorAll('button')).find((button) => button.textContent?.trim() === '简介');
  return {
    fallbackText: status?.textContent?.trim() || '',
    fallbackVisible: Boolean(status && status.getBoundingClientRect().height > 0),
    introSelected: Boolean(selected?.className.includes('text-yellow-500')),
    bodyContainsUndefined: document.body.innerText.includes('undefined'),
  };
})()""")
ws.close()
print(json.dumps(result, ensure_ascii=False, indent=2))
passed = result["fallbackText"] == "暂无简介" and result["fallbackVisible"] and result["introSelected"] and not result["bodyContainsUndefined"]
sys.exit(0 if passed else 1)

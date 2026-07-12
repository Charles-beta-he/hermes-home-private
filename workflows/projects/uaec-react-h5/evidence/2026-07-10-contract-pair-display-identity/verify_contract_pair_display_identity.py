import json
import sys
import time
import urllib.parse
import urllib.request

import websocket

URL = "http://127.0.0.1:4183/contract/contract-interface?" + urllib.parse.urlencode(
    {"tradeName": "BTC/USDT", "symbol": "btc_usdt_sustainable", "tradeId": "1"}
)
pages = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
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
            return message.get("result", {})


call("Page.enable")
call("Network.enable")
call("Network.setCacheDisabled", {"cacheDisabled": True})
call("Storage.clearDataForOrigin", {"origin": "http://127.0.0.1:4183", "storageTypes": "cache_storage,service_workers"})
call("Page.navigate", {"url": URL})
time.sleep(5)
result = call(
    "Runtime.evaluate",
    {
        "expression": "(() => ({body: document.body.innerText, title: document.querySelector('button[aria-label^=\"选择合约交易对\"]')?.innerText || ''}))()",
        "returnByValue": True,
    },
)["result"]["value"]
ws.close()
title = result["title"].splitlines()[0] if result["title"] else ""
print(json.dumps({"title": title, "displayedPair": "BTC/USDT" in result["body"], "normalizedLeak": "btcusdt" in result["body"]}, ensure_ascii=False, indent=2))
sys.exit(0 if title == "BTC/USDT" and "BTC/USDT" in result["body"] and "btcusdt" not in result["body"] else 1)

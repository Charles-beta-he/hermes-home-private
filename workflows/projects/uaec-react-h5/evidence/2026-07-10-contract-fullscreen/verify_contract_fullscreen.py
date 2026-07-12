import json
import sys
import time
import urllib.request

import websocket

CDP_PORT = 9225
BASE_URL = "http://127.0.0.1:4183"
DETAIL_URL = (
    BASE_URL
    + "/contract/contract-interface?tradeName=SOLUSDT%20%E6%B0%B8%E7%BB%AD"
    + "&symbol=sol_usdt_sustainable&tradeId=1035922175497863168"
)

pages = json.load(urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list"))
page = next(page for page in pages if page.get("type") == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=20)
command_id = 0
requests = []


def command(method, params=None):
    global command_id
    command_id += 1
    request_id = command_id
    ws.send(json.dumps({"id": request_id, "method": method, "params": params or {}}))
    while True:
        response = json.loads(ws.recv())
        if response.get("method") == "Network.requestWillBeSent":
            requests.append(response["params"]["request"]["url"])
        if response.get("id") == request_id:
            return response


def evaluate(expression):
    response = command(
        "Runtime.evaluate", {"expression": expression, "returnByValue": True}
    )
    return response["result"]["result"].get("value")


command("Network.enable")
command("Network.clearBrowserCache")
command("Network.setCacheDisabled", {"cacheDisabled": True})
command(
    "Runtime.evaluate",
    {
        "expression": "Promise.all([navigator.serviceWorker?.getRegistrations().then(rs=>Promise.all(rs.map(r=>r.unregister()))),caches?.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k))))])",
        "awaitPromise": True,
    },
)
command(
    "Emulation.setDeviceMetricsOverride",
    {"width": 844, "height": 390, "deviceScaleFactor": 1, "mobile": True},
)
command("Page.navigate", {"url": DETAIL_URL})
time.sleep(5)

initial = evaluate(
    "({"
    "openButton:!!document.querySelector('button[aria-label=\\\"全屏K线\\\"]'),"
    "fullscreenRegion:!!document.querySelector('[role=region][aria-label=\\\"全屏K线图\\\"]'),"
    "title:document.querySelector('button[aria-label=\\\"选择合约交易对\\\"]')?.innerText.trim()"
    "})"
)

if not initial.get("openButton"):
    print(json.dumps({"phase": "RED", "reason": "fullscreen trigger missing", "initial": initial}, ensure_ascii=False, indent=2))
    ws.close()
    sys.exit(1)

evaluate("document.querySelector('button[aria-label=\\\"全屏K线\\\"]')?.click()")
time.sleep(2)
opened = evaluate(
    "({"
    "region:!!document.querySelector('[role=region][aria-label=\\\"全屏K线图\\\"]'),"
    "closeButton:!!document.querySelector('button[aria-label=\\\"退出全屏K线\\\"]'),"
    "title:document.querySelector('[role=region][aria-label=\\\"全屏K线图\\\"]')?.innerText.includes('SOLUSDT 永续'),"
    "periods:[...document.querySelectorAll('[role=region][aria-label=\\\"全屏K线图\\\"] button')].map(b=>b.innerText.trim()).filter(Boolean),"
    "bodyOverflow:getComputedStyle(document.body).overflow"
    "})"
)
evaluate("document.querySelector('button[aria-label=\\\"退出全屏K线\\\"]')?.click()")
time.sleep(2)
closed = evaluate(
    "({"
    "region:!!document.querySelector('[role=region][aria-label=\\\"全屏K线图\\\"]'),"
    "openButton:!!document.querySelector('button[aria-label=\\\"全屏K线\\\"]'),"
    "bodyOverflow:getComputedStyle(document.body).overflow,"
    "title:document.querySelector('button[aria-label=\\\"选择合约交易对\\\"]')?.innerText.trim()"
    "})"
)
forbidden_count = sum(
    "/collection" in url or "/saveEntrust" in url for url in requests
)
result = {
    "phase": "GREEN",
    "initial": initial,
    "opened": opened,
    "closed": closed,
    "forbiddenRequestCount": forbidden_count,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
ws.close()

passed = (
    opened.get("region")
    and opened.get("closeButton")
    and opened.get("title")
    and opened.get("bodyOverflow") == "hidden"
    and not closed.get("region")
    and closed.get("openButton")
    and closed.get("title", "").startswith("SOLUSDT 永续")
    and forbidden_count == 0
)
sys.exit(0 if passed else 1)

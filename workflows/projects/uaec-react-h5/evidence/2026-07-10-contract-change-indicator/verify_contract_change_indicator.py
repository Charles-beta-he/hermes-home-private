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
page = next(
    page
    for page in json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
    if page.get("type") == "page"
)
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=20)
command_id = 0


def command(method, params=None):
    global command_id
    command_id += 1
    current_id = command_id
    ws.send(json.dumps({"id": current_id, "method": method, "params": params or {}}))
    while True:
        response = json.loads(ws.recv())
        if response.get("id") == current_id:
            return response


def evaluate(expression):
    response = command(
        "Runtime.evaluate", {"expression": expression, "returnByValue": True}
    )
    return response["result"]["result"].get("value")


command("Network.clearBrowserCache")
command("Network.setCacheDisabled", {"cacheDisabled": True})
command(
    "Runtime.evaluate",
    {
        "expression": "Promise.all([navigator.serviceWorker?.getRegistrations().then(rs=>Promise.all(rs.map(r=>r.unregister()))),caches?.keys().then(ks=>Promise.all(ks.map(k=>caches.delete(k))))])",
        "awaitPromise": True,
    },
)
command("Page.navigate", {"url": PAGE_URL})
time.sleep(5)
state = evaluate(
    "(() => {"
    "const rate=document.querySelector('[aria-label^=\"24小时涨跌幅\"]');"
    "const indicator=rate?.querySelector('[data-direction]');"
    "return {"
    "found:!!rate,"
    "text:rate?.innerText.trim() || '',"
    "change:rate?.getAttribute('data-change') || '',"
    "direction:indicator?.getAttribute('data-direction') || '',"
    "indicatorAriaHidden:indicator?.getAttribute('aria-hidden') || ''"
    "};"
    "})()"
)
print(json.dumps(state, ensure_ascii=False, indent=2))
ws.close()
try:
    change = float(state.get("change", ""))
except ValueError:
    change = None
expected_direction = "up" if change is not None and change > 0 else "down" if change is not None and change < 0 else "flat"
expected_text = None if change is None else f"{'+' if change > 0 else ''}{state['change']}%"
passed = (
    state.get("found") is True
    and state.get("text", "").startswith(expected_text or "__missing__")
    and state.get("direction") == expected_direction
    and state.get("indicatorAriaHidden") == "true"
)
sys.exit(0 if passed else 1)

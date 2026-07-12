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
command(
    "Emulation.setDeviceMetricsOverride",
    {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True},
)
command("Page.navigate", {"url": PAGE_URL})
time.sleep(5)
labels = ["3分", "30分", "周线"]
results = []
for label in labels:
    clicked = evaluate(
        "(() => {"
        f"const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==={json.dumps(label, ensure_ascii=False)});"
        "if(!b)return false;b.click();return true"
        "})()"
    )
    time.sleep(2)
    state = evaluate(
        "(() => {"
        f"const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==={json.dumps(label, ensure_ascii=False)});"
        "return {present:!!b,pressed:b?.getAttribute('aria-pressed')||'',selected:b?.className.includes('bg-yellow-500')||false};"
        "})()"
    )
    results.append({"label": label, "clicked": clicked, **state})
print(json.dumps(results, ensure_ascii=False, indent=2))
ws.close()
passed = all(
    item["present"] and item["clicked"] and item["pressed"] == "true" and item["selected"]
    for item in results
)
sys.exit(0 if passed else 1)

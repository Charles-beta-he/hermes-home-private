import json
import sys
import time
import urllib.parse
import urllib.request

import websocket

BASE = "http://127.0.0.1:4183/contract/contract-interface?" + urllib.parse.urlencode(
    {"tradeName": "SOLUSDT 永续", "symbol": "sol_usdt_sustainable", "tradeId": "1035922175497863168"}
)
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
    return call("Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True})["result"].get("value")


call("Page.enable")
call("Network.enable")
call("Network.setCacheDisabled", {"cacheDisabled": True})
call("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True})
call("Storage.clearDataForOrigin", {"origin": "http://127.0.0.1:4183", "storageTypes": "cache_storage,service_workers,local_storage"})
call("Page.navigate", {"url": BASE})
time.sleep(5)
evaluate("document.querySelector('button[aria-label=\"全屏K线\"]')?.setAttribute('data-test-trigger','true'); document.querySelectorAll('button').forEach(b => b.textContent?.trim() === '深度图' && b.click()); const trigger=document.querySelector('button[aria-label=\"全屏K线\"]'); trigger?.focus(); trigger?.click(); true")
time.sleep(0.5)
opened = evaluate("(() => { const dialog=document.querySelector('[aria-label=\"全屏K线图\"]'); const heights=dialog ? Array.from(dialog.querySelectorAll('div')).map(node => node.getBoundingClientRect().height).filter(height => height < 844) : []; return { role: dialog?.getAttribute('role') || '', modal: dialog?.getAttribute('aria-modal') || '', height: Math.max(0, ...heights), active: document.activeElement?.getAttribute('aria-label') || '' }; })()")
call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape"})
call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape"})
time.sleep(0.5)
escape = evaluate("({ open: Boolean(document.querySelector('[aria-label=\"全屏K线图\"]')), focus: document.activeElement?.getAttribute('aria-label') || '' })")
evaluate("document.querySelector('button[aria-label=\"全屏K线\"]')?.click(); true")
time.sleep(0.4)
evaluate("history.back(); true")
time.sleep(0.7)
back = evaluate("({ open: Boolean(document.querySelector('[aria-label=\"全屏K线图\"]')), path: location.pathname, pair: new URLSearchParams(location.search).get('symbol') })")
ws.close()
result = {"opened": opened, "escape": escape, "back": back}
print(json.dumps(result, ensure_ascii=False, indent=2))
passed = opened["role"] == "dialog" and opened["modal"] == "true" and opened["height"] > 700 and opened["active"] == "退出全屏K线" and not escape["open"] and escape["focus"] == "全屏K线" and not back["open"] and back["path"].endswith("contract-interface") and back["pair"] == "sol_usdt_sustainable"
sys.exit(0 if passed else 1)

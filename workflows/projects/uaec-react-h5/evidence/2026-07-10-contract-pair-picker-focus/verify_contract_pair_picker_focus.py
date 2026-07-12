import json
import sys
import time
import urllib.parse
import urllib.request

import websocket

URL = "http://127.0.0.1:4183/contract/contract-interface?" + urllib.parse.urlencode({"tradeName": "SOLUSDT 永续", "symbol": "sol_usdt_sustainable", "tradeId": "1035922175497863168"})
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
call("Page.addScriptToEvaluateOnNewDocument", {"source": """
  window.__drawerListenerCounts = { adds: 0, removes: 0 };
  const originalAdd = window.addEventListener.bind(window);
  const originalRemove = window.removeEventListener.bind(window);
  window.addEventListener = function(type, listener, options) {
    if (type === 'keydown') window.__drawerListenerCounts.adds += 1;
    return originalAdd(type, listener, options);
  };
  window.removeEventListener = function(type, listener, options) {
    if (type === 'keydown') window.__drawerListenerCounts.removes += 1;
    return originalRemove(type, listener, options);
  };
"""})
call("Page.navigate", {"url": URL})
time.sleep(5)
evaluate("const trigger=document.querySelector('button[aria-label^=\"选择合约交易对\"]'); trigger?.focus(); trigger?.click(); true")
time.sleep(0.4)
opened = evaluate("({ dialog: Boolean(document.querySelector('[role=dialog][aria-label=\"选择合约交易对\"]')), active: document.activeElement?.getAttribute('aria-label') || '', activeTag: document.activeElement?.tagName || '', activeHtml: document.activeElement?.outerHTML?.slice(0, 240) || '', inputExists: Boolean(document.querySelector('input[aria-label=\"搜索合约交易对\"]')), rootInert: document.getElementById('root')?.hasAttribute('inert') || false })")
opened["listenerCounts"] = evaluate("({...window.__drawerListenerCounts})")
call("Input.insertText", {"text": "SOL"})
time.sleep(0.2)
opened["searchValue"] = evaluate("document.querySelector('input[aria-label=\"搜索合约交易对\"]')?.value || ''")
after_search_listener_counts = evaluate("({...window.__drawerListenerCounts})")
call("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape"})
call("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Escape", "code": "Escape"})
time.sleep(0.4)
closed = evaluate("({ dialog: Boolean(document.querySelector('[role=dialog][aria-label=\"选择合约交易对\"]')), active: document.activeElement?.getAttribute('aria-label') || '', rootInert: document.getElementById('root')?.hasAttribute('inert') || false })")
ws.close()
result = {"opened": opened, "afterSearchListenerCounts": after_search_listener_counts, "closed": closed}
print(json.dumps(result, ensure_ascii=False, indent=2))
listener_stable_during_search = after_search_listener_counts == opened["listenerCounts"]
passed = opened["dialog"] and opened["active"] == "搜索合约交易对" and opened["searchValue"] == "SOL" and opened["rootInert"] and listener_stable_during_search and not closed["dialog"] and closed["active"].startswith("选择合约交易对") and not closed["rootInert"]
sys.exit(0 if passed else 1)

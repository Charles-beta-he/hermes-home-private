import json
import pathlib
import sys
import time
import urllib.request

import websocket

PAGE_URL = (
    "http://127.0.0.1:4183/contract/contract-interface"
    "?tradeName=SOLUSDT%20%E6%B0%B8%E7%BB%AD"
    "&symbol=sol_usdt_sustainable"
    "&tradeId=1035922175497863168"
)
DOWNLOAD_DIR = pathlib.Path(
    "/Users/charles/.hermes/workflows/projects/uaec-react-h5/evidence/"
    "2026-07-10-contract-kline-share/downloads"
)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
for old_file in DOWNLOAD_DIR.glob("contract-kline-*.png"):
    old_file.unlink()

pages = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json/list"))
page = next(item for item in pages if item.get("type") == "page")
ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=20)
request_id = 0


def call(method, params=None):
    global request_id
    request_id += 1
    current_id = request_id
    ws.send(json.dumps({"id": current_id, "method": method, "params": params or {}}))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == current_id:
            if "error" in message:
                raise RuntimeError(message["error"])
            return message.get("result", {})


call("Page.enable")
call("Network.enable")
call("Network.setCacheDisabled", {"cacheDisabled": True})
call(
    "Storage.clearDataForOrigin",
    {
        "origin": "http://127.0.0.1:4183",
        "storageTypes": "cache_storage,service_workers",
    },
)
call(
    "Page.addScriptToEvaluateOnNewDocument",
    {
        "source": "Object.defineProperty(navigator, 'share', { value: undefined, configurable: true });"
    },
)
call("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DOWNLOAD_DIR), "eventsEnabled": True})
call("Page.navigate", {"url": f"{PAGE_URL}&cacheBust={int(time.time())}"})
time.sleep(5)

result = call(
    "Runtime.evaluate",
    {
        "expression": """
        (async () => {
          const errors = [];
          const originalError = console.error;
          console.error = (...args) => {
            errors.push(args.map((value) => value instanceof Error ? `${value.name}: ${value.message}` : String(value)));
            originalError(...args);
          };
          const button = document.querySelector('button[aria-label="分享K线截图"]');
          if (!button) return { found: false, errors };
          button.click();
          await new Promise((resolve) => setTimeout(resolve, 4000));
          console.error = originalError;
          return {
            found: true,
            disabledAfter: button.disabled,
            labelAfter: button.getAttribute('aria-label'),
            errors
          };
        })()
        """,
        "awaitPromise": True,
        "returnByValue": True,
    },
).get("result", {}).get("value", {})

time.sleep(2)
files = [
    {"name": file.name, "size": file.stat().st_size}
    for file in DOWNLOAD_DIR.glob("contract-kline-*.png")
]
result["downloads"] = files


def run_unsupported_file_share_case(can_share_source):
    case_result = call(
        "Runtime.evaluate",
        {
            "expression": f"""
            (async () => {{
              let shareCalls = 0;
              let downloadClicks = 0;
              const originalClick = HTMLAnchorElement.prototype.click;
              HTMLAnchorElement.prototype.click = function () {{ downloadClicks += 1; }};
              Object.defineProperty(navigator, 'share', {{
                value: () => {{ shareCalls += 1; return Promise.resolve(); }},
                configurable: true
              }});
              Object.defineProperty(navigator, 'canShare', {{
                value: {can_share_source},
                configurable: true
              }});
              const button = document.querySelector('button[aria-label="分享K线截图"]');
              button?.click();
              await new Promise((resolve) => setTimeout(resolve, 4000));
              HTMLAnchorElement.prototype.click = originalClick;
              return {{ found: Boolean(button), shareCalls, downloadClicks, disabledAfter: button?.disabled }};
            }})()
            """,
            "awaitPromise": True,
            "returnByValue": True,
        },
    ).get("result", {}).get("value", {})
    return case_result


result["shareWithoutCanShare"] = run_unsupported_file_share_case("undefined")
result["shareWithCanShareFalse"] = run_unsupported_file_share_case("() => false")

abort_result = call(
    "Runtime.evaluate",
    {
        "expression": """
        (async () => {
          Object.defineProperty(navigator, 'share', {
            value: () => Promise.reject(new DOMException('cancelled', 'AbortError')),
            configurable: true
          });
          Object.defineProperty(navigator, 'canShare', {
            value: () => true,
            configurable: true
          });
          const button = document.querySelector('button[aria-label="分享K线截图"]');
          button?.click();
          await new Promise((resolve) => setTimeout(resolve, 4000));
          return {
            found: Boolean(button),
            disabledAfter: button?.disabled,
            labelAfter: button?.getAttribute('aria-label'),
            failureShown: document.body.innerText.includes('K线截图生成失败')
          };
        })()
        """,
        "awaitPromise": True,
        "returnByValue": True,
    },
).get("result", {}).get("value", {})
result["abortPath"] = abort_result
print(json.dumps(result, ensure_ascii=False, indent=2))
ws.close()

passed = (
    result.get("found")
    and len(files) == 1
    and files[0]["size"] > 10000
    and result["shareWithoutCanShare"].get("shareCalls") == 0
    and result["shareWithoutCanShare"].get("downloadClicks") == 1
    and result["shareWithCanShareFalse"].get("shareCalls") == 0
    and result["shareWithCanShareFalse"].get("downloadClicks") == 1
    and abort_result.get("found")
    and abort_result.get("disabledAfter") is False
    and abort_result.get("labelAfter") == "分享K线截图"
    and abort_result.get("failureShown") is False
)
sys.exit(0 if passed else 1)

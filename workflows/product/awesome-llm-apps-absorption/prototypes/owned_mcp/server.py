#!/usr/bin/env python3
from __future__ import annotations
import json, sys

TOOLS=[{"name":"read_fixture","description":"Read one deterministic checked-in fixture","inputSchema":{"type":"object","properties":{"fixture_id":{"type":"string"}},"required":["fixture_id"],"additionalProperties":False}}]
RESOURCES=[{"uri":"fixture://capability-contract","name":"Capability contract fixture","mimeType":"application/json"}]
FIXTURES={"capability-contract":{"authority":"read_only","status":"fixture","external":False}}

def response(request):
    request_id=request.get("id")
    method=request.get("method")
    if method=="initialize": result={"protocolVersion":"2025-03-26","serverInfo":{"name":"owned-readonly-fixture","version":"1.0"},"capabilities":{"tools":{},"resources":{}}}
    elif method=="tools/list": result={"tools":TOOLS}
    elif method=="resources/list": result={"resources":RESOURCES}
    elif method=="tools/call":
        params=request.get("params",{}); name=params.get("name"); args=params.get("arguments",{})
        if name!="read_fixture": return {"jsonrpc":"2.0","id":request_id,"error":{"code":-32601,"message":"tool not found"}}
        fixture_id=args.get("fixture_id")
        if fixture_id not in FIXTURES: return {"jsonrpc":"2.0","id":request_id,"error":{"code":-32602,"message":"fixture not found"}}
        result={"content":[{"type":"text","text":json.dumps(FIXTURES[fixture_id],sort_keys=True)}],"structuredContent":FIXTURES[fixture_id],"isError":False}
    else: return {"jsonrpc":"2.0","id":request_id,"error":{"code":-32601,"message":"method not found"}}
    return {"jsonrpc":"2.0","id":request_id,"result":result}

def main():
    for line in sys.stdin:
        try: request=json.loads(line); out=response(request)
        except Exception as exc: out={"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":type(exc).__name__}}
        print(json.dumps(out,separators=(",",":")),flush=True)

if __name__=="__main__": main()

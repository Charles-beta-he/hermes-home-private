from __future__ import annotations
import hashlib, json, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class DiscoveredTool:
    capability_id:str; server_id:str; name:str; description:str; input_schema:dict[str,Any]; side_effect_class:str; schema_digest:str

class OwnedStdioAdapter:
    def __init__(self,server_id:str,server_path:Path,timeout:float=2.0,max_description:int=500):
        if not server_id.strip(): raise ValueError("server_id required")
        self.server_id=server_id; self.server_path=server_path; self.timeout=timeout; self.max_description=max_description; self._next_id=0
    def _request(self,method:str,params:dict[str,Any]|None=None)->dict[str,Any]:
        self._next_id+=1; request={"jsonrpc":"2.0","id":self._next_id,"method":method}
        if params is not None: request["params"]=params
        proc=subprocess.run([sys.executable,str(self.server_path)],input=json.dumps(request)+"\n",text=True,capture_output=True,timeout=self.timeout,check=False)
        if proc.returncode: raise RuntimeError("server failed")
        line=proc.stdout.splitlines()[0] if proc.stdout.splitlines() else ""
        reply=json.loads(line)
        if reply.get("id")!=self._next_id: raise RuntimeError("response id mismatch")
        if "error" in reply: raise RuntimeError(reply["error"].get("message","MCP error"))
        return reply["result"]
    def initialize(self)->dict[str,Any]: return self._request("initialize")
    def discover(self)->list[DiscoveredTool]:
        tools=self._request("tools/list").get("tools",[]); out=[]
        for raw in tools:
            name=raw.get("name",""); description=raw.get("description",""); schema=raw.get("inputSchema")
            if not name or not isinstance(schema,dict): raise ValueError("malformed tool schema")
            if len(description)>self.max_description: raise ValueError("oversized description")
            effect="read_only" if name.startswith(("read_","list_","get_")) else "unknown"
            digest=hashlib.sha256(json.dumps(schema,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            out.append(DiscoveredTool(f"{self.server_id}:{name}",self.server_id,name,description,schema,effect,digest))
        return out
    def list_resources(self)->list[dict[str,Any]]: return self._request("resources/list").get("resources",[])
    def call(self,capability_id:str,arguments:dict[str,Any],allowed_capabilities:set[str])->dict[str,Any]:
        tools={t.capability_id:t for t in self.discover()}
        if capability_id not in tools: raise KeyError(capability_id)
        tool=tools[capability_id]
        if tool.side_effect_class!="read_only" or capability_id not in allowed_capabilities: raise PermissionError("capability not authorized")
        result=self._request("tools/call",{"name":tool.name,"arguments":arguments})
        return {"server_id":self.server_id,"capability_id":capability_id,"schema_digest":tool.schema_digest,"result":result}

#!/usr/bin/env python3
import importlib.util,json,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];s=importlib.util.spec_from_file_location("v",ROOT/"scripts/verify_pack.py");v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
def clone(p):
 for rel in v.REQ:
  q=p/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/rel).read_bytes())
def current():assert v.validate(ROOT)==[],v.validate(ROOT)
def mutate(rel,fn,needle):
 with tempfile.TemporaryDirectory() as td:
  p=Path(td);clone(p);q=p/rel;d=json.loads(q.read_text());fn(d);q.write_text(json.dumps(d));assert any(needle in x for x in v.validate(p)),v.validate(p)
def claim_hash():mutate("evidence/source-evidence.json",lambda d:d["claims"][0]["evidence"][0].update(quote_sha256="0"*64),"claim_hash_mismatch")
def authority():mutate("evidence/source-evidence.json",lambda d:d["authority"].update(runtime_mutation=True),"authority_not_closed")
def gate():mutate("graph/raven-everos-capability-graph.json",lambda d:d["gates"][0].update(outcomes={"pass":"continue"}),"gate_outcomes_missing")
def promotion():mutate("proposals/experience-ratchet-created.json",lambda d:d["promotion"].update(performed=True),"unexpected_promotion")
if __name__=="__main__":
 for f in [current,claim_hash,authority,gate,promotion]:f();print("PASS",f.__name__)
 print("VERIFY_PACK_TESTS_OK")

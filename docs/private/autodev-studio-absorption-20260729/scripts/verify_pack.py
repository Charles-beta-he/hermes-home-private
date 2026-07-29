#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
REQ=["PLAN.md","evidence/source-evidence.json","evidence/timestamped-source-packet-20260729.md","graph/raven-everos-capability-graph.json","proposals/experience-ratchet-created.json","reports/final.md"]
OUT={"pass","warn","fail","blocked"}; AUTH={"runtime_mutation","core_mutation","taskpool_write","scheduler_write","external_dispatch","publish_deploy_push","credential_entry"}
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def qhash(src,rel,a,b): return hashlib.sha256("".join((src/rel).read_text(encoding="utf-8").splitlines(keepends=True)[a-1:b]).encode()).hexdigest()
def validate(root):
 e=[]
 for rel in REQ:
  if not (root/rel).is_file(): e.append("missing:"+rel)
 if e:return e
 ev=load(root/"evidence/source-evidence.json"); src=Path(ev["source"]["local_checkout"])
 if not (src/".git").is_dir(): e.append("source_checkout_missing")
 else:
  def git(*a): return subprocess.run(["git","-C",str(src),*a],text=True,capture_output=True).stdout.strip()
  if git("rev-parse","HEAD")!=ev["source"]["commit"]:e.append("source_commit_drift")
  if git("rev-parse","HEAD^{tree}")!=ev["source"]["tree"]:e.append("source_tree_drift")
  if git("status","--porcelain"):e.append("source_worktree_dirty")
 for c in ev.get("claims",[]):
  for r in c.get("evidence",[]):
   a,b=r["line_range"]
   try: actual=qhash(src,r["file"],a,b)
   except Exception as x:e.append(f"claim_read_error:{c.get('id')}:{x}");continue
   if actual!=r.get("quote_sha256"):e.append("claim_hash_mismatch:"+str(c.get("id")))
 for k in AUTH:
  if ev.get("authority",{}).get(k) is not False:e.append("authority_not_closed:"+k)
 g=load(root/"graph/raven-everos-capability-graph.json")
 if not g.get("capability_nodes"):e.append("graph_nodes_missing")
 if not g.get("agent_wrappers"):e.append("graph_wrappers_missing")
 for gate in g.get("gates",[]):
  if not OUT.issubset(set((gate.get("outcomes") or {}).keys())):e.append("gate_outcomes_missing:"+str(gate.get("id")))
 if (g.get("authority_boundary") or {}).get("closed") is not True:e.append("authority_boundary_open")
 p=load(root/"proposals/experience-ratchet-created.json")
 if p.get("promotion",{}).get("performed") is not False:e.append("unexpected_promotion")
 if any(x.get("status")!="proposal_only" for x in p.get("created",[])):e.append("proposal_status_not_proposal_only")
 return e
def main(a):
 root=Path(a[1] if len(a)>1 else ".").resolve();e=validate(root);print(json.dumps({"ok":not e,"root":str(root),"errors":e},sort_keys=True));return bool(e)
if __name__=="__main__":raise SystemExit(main(sys.argv))

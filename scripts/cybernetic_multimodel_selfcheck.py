#!/usr/bin/env python3
"""Local-first verifier for cybernetic multi-model intervention landing.

Checks first-order/second-order cybernetics × multi-model thinking artifacts in
~/Documents/brain. No network, no LLM calls, no destructive actions.
"""
from __future__ import annotations

import argparse, json, os, re, subprocess, sys
from pathlib import Path

VAULT = Path(os.environ.get("HERMES_BRAIN_VAULT", str(Path.home()/"Documents/brain"))).expanduser()
PROJECT = VAULT/"20-projects"/"cybernetic-multimodel-intervention"
FILES = {
  "project": PROJECT/"Project - Cybernetic Multi-model Intervention.md",
  "p10": PROJECT/"P10 - Long-term Strategy.md",
  "p9": PROJECT/"P9 - Implementation Backlog.md",
  "playbook": VAULT/"08-实践方案"/"06-一阶二阶控制论多模型介入Playbook.md",
  "review": VAULT/"60-reviews"/"2026-05-06-cybernetic-multimodel-intervention-review.md",
  "task": VAULT/"30-tasks"/"2026-05-06-cybernetic-multimodel-intervention-log.md",
  "evolution": VAULT/"05-进化日志"/"2026-05-06-控制论多模型介入落地.md",
  "atom_first": VAULT/"10-atoms"/"first-order-cybernetic-multimodel-intervention.md",
  "atom_second": VAULT/"10-atoms"/"second-order-cybernetic-self-observation.md",
  "theory_fo_so": VAULT/"01-控制论基础"/"06-一阶与二阶控制论.md",
  "theory_second": VAULT/"03-系统理论"/"SecondOrder-二阶控制论.md",
}
PATTERNS = {
  "p10": ["first-order cybernetics", "second-order cybernetics", "observer", "P10 stop gate", "model agreement is not evidence"],
  "p9": ["P0", "P1", "P2", "Acceptance checks", "brainctl sync", "structural audit"],
  "playbook": ["First-order gate", "Second-order gate", "issue ledger", "not_certified", "tool evidence"],
  "review": ["not_certified", "issue_ledger", "DeepSeek", "timeout", "dissent"],
  "task": ["expires_at", "proof ledger", "sync", "reindex", "search"],
  "atom_first": ["first-order cybernetics", "object task", "tool evidence", "multi-model"],
  "atom_second": ["second-order cybernetics", "observer", "self-audit", "audit rules"],
  "theory_fo_so": ["cybernetic multi-model intervention", "first-order cybernetics", "second-order cybernetics"],
  "theory_second": ["multi-model self-observation", "second-order cybernetics", "audit rules"],
}
SECRET_RE = re.compile(r"(?i)((?:sk-(?:proj|live|test)-[A-Za-z0-9_\-]{20,})|ghp_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9\-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----)")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

def text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def run(cmd):
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=60)
    return {"cmd": cmd, "exit_code": p.returncode, "stdout": p.stdout[:3000], "stderr": p.stderr[:1200]}

def structural():
    ignored={".obsidian",".git",".trash",".DS_Store"}
    md=[p for p in VAULT.rglob("*.md") if not any(part.startswith(".") or part in ignored for part in p.relative_to(VAULT).parts)]
    dirs=[p for p in VAULT.rglob("*") if p.is_dir() and not any(part.startswith(".") or part in ignored for part in p.relative_to(VAULT).parts)]
    empty=[]
    for d in dirs:
        children=[c for c in d.iterdir() if not c.name.startswith(".") and c.name not in ignored]
        if not children: empty.append(str(d.relative_to(VAULT)))
    top_no=[]; hollow=[]
    for d in [p for p in VAULT.iterdir() if p.is_dir() and not p.name.startswith(".") and p.name not in ignored]:
        direct=list(d.glob("*.md"))
        if not any(f.name.startswith("00-") and ("索引" in f.name or "index" in f.name.lower()) for f in direct): top_no.append(d.name)
        if any(True for _ in d.rglob("*.md")) and not direct: hollow.append(d.name)
    basenames={p.stem for p in md}; rels={str(p.relative_to(VAULT).with_suffix("")) for p in md}
    broken=[]
    for p in md:
        for m in WIKILINK_RE.finditer(text(p)):
            target=m.group(1).split("|",1)[0].split("#",1)[0].strip()
            if not target or target in basenames or target in rels or Path(target).name in basenames: continue
            broken.append({"file":str(p.relative_to(VAULT)),"target":target})
    secrets=[str(p.relative_to(VAULT)) for p in md if SECRET_RE.search(text(p))]
    return {"empty_dirs":sorted(empty),"top_level_no_index":sorted(top_no),"parent_no_direct_md_top":sorted(hollow),"broken_wikilinks_count":len(broken),"broken_wikilinks_sample":broken[:20],"secret_pattern_hits":len(secrets),"secret_pattern_files":secrets[:20]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); ap.add_argument("--skip-brainctl", action="store_true"); args=ap.parse_args()
    checks=[]; ok=True
    for name,p in FILES.items():
        exists=p.exists(); checks.append({"name":f"file:{name}","ok":exists,"path":str(p)}); ok &= exists
        if exists and name in PATTERNS:
            tx=text(p)
            for pat in PATTERNS[name]:
                hit=pat in tx; checks.append({"name":f"pattern:{name}:{pat}","ok":hit,"path":str(p)}); ok &= hit
    st=structural() if VAULT.exists() else {"error":"vault_missing"}
    for key in ["empty_dirs","top_level_no_index","parent_no_direct_md_top"]:
        good=st.get(key)==[]; checks.append({"name":f"structure:{key}","ok":good,"value":st.get(key)}); ok &= good
    for key in ["broken_wikilinks_count","secret_pattern_hits"]:
        good=st.get(key)==0; checks.append({"name":f"structure:{key}","ok":good,"value":st.get(key)}); ok &= good
    brainctl={}
    if not args.skip_brainctl:
        script=str(Path.home()/".hermes/scripts/brainctl.py")
        brainctl["search_combined"] = run([sys.executable, script, "--json", "search", "cybernetic multi-model intervention first-order second-order observer", "--limit", "8"])
        good=brainctl["search_combined"]["exit_code"]==0 and "cybernetic" in brainctl["search_combined"].get("stdout","")
        checks.append({"name":"brainctl:search_combined","ok":good,"exit_code":brainctl["search_combined"]["exit_code"]}); ok &= good
        brainctl["search_chinese"] = run([sys.executable, script, "--json", "search", "一阶控制论 二阶控制论 多模型介入 观察者", "--limit", "8"])
        good=brainctl["search_chinese"]["exit_code"]==0 and "多模型介入" in brainctl["search_chinese"].get("stdout","")
        checks.append({"name":"brainctl:search_chinese","ok":good,"exit_code":brainctl["search_chinese"]["exit_code"]}); ok &= good
    report={"status":"PASS" if ok else "FAIL", "vault":str(VAULT), "checks":checks, "structure":st, "brainctl":brainctl}
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else report["status"])
    return 0 if ok else 1
if __name__ == "__main__": raise SystemExit(main())

from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Claim:
    id: str
    text: str
    evidence_refs: tuple[str, ...]
    status: str = "verified_static"
    cannot_prove: tuple[str, ...] = ()


class CitationGate:
    ALLOWED_STATUS = {"verified_static", "runtime_verified", "assumption", "blocked"}

    def __init__(self, source_root: Path):
        self.source_root = source_root.resolve()

    def validate(self, claims: list[Claim]) -> dict[str, Any]:
        issues=[]; seen=set()
        for claim in claims:
            if not claim.id or claim.id in seen: issues.append(f"duplicate_or_empty_id:{claim.id}")
            seen.add(claim.id)
            if claim.status not in self.ALLOWED_STATUS: issues.append(f"invalid_status:{claim.id}")
            if claim.status in {"verified_static", "runtime_verified"} and not claim.evidence_refs:
                issues.append(f"missing_evidence:{claim.id}")
            for ref in claim.evidence_refs:
                candidate=(self.source_root/ref).resolve()
                try: candidate.relative_to(self.source_root)
                except ValueError:
                    issues.append(f"outside_source_root:{claim.id}:{ref}"); continue
                if not candidate.is_file(): issues.append(f"missing_source:{claim.id}:{ref}")
            if claim.status == "verified_static" and not claim.cannot_prove:
                issues.append(f"missing_static_boundary:{claim.id}")
        return {"status":"PASS" if not issues else "FAIL","issues":issues,"claim_count":len(claims)}


def render_report(title: str, claims: list[Claim], verdict: dict[str, Any]) -> str:
    lines=[f"# {title}","",f"Citation gate: **{verdict['status']}**","","## Claims",""]
    for claim in claims:
        lines += [f"### {claim.id}","",claim.text,"",f"Status: `{claim.status}`",""]
        if claim.evidence_refs:
            lines.append("Evidence:"); lines += [f"- `{ref}`" for ref in claim.evidence_refs]; lines.append("")
        if claim.cannot_prove:
            lines.append("Cannot prove:"); lines += [f"- {x}" for x in claim.cannot_prove]; lines.append("")
    if verdict["issues"]:
        lines += ["## Gate issues",""]+[f"- {x}" for x in verdict["issues"]]
    return "\n".join(lines).rstrip()+"\n"


def write_packet(out_dir: Path, title: str, claims: list[Claim], verdict: dict[str, Any], report: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir/"claims.json").write_text(json.dumps([asdict(c) for c in claims],ensure_ascii=False,indent=2)+"\n")
    (out_dir/"verdict.json").write_text(json.dumps(verdict,ensure_ascii=False,indent=2)+"\n")
    (out_dir/"report.md").write_text(report)

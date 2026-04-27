#!/usr/bin/env python3
"""
code-intel.py — Hermes 原生代码智能引擎 (GitNexus 方法论, Python 标准库)
轻量级替代: 不装 npm, 不用 tree-sitter, 专为 Hermes 自维护定制

功能:
  1. import-graph    → 脚本间 Python import 依赖图
  2. call-graph      → 脚本间 subprocess/直接调用关系
  3. blast-radius    → 修改某文件的影响范围
  4. skill-deps      → Skills 交叉引用图
  5. dead-code       → 疑似未使用的脚本
  6. summary         → 全部分析一目了然

用法:
  python3 code-intel.py import-graph
  python3 code-intel.py blast-radius --file route_store.py
  python3 code-intel.py dead-code
  python3 code-intel.py summary
"""

import argparse, ast, os, re, sys
from collections import defaultdict
from pathlib import Path

HERMES = Path.home() / ".hermes"
SCRIPTS = HERMES / "scripts"
SKILLS = HERMES / "skills"
HOOKS = HERMES / "agent-hooks"


def _py_files(dir_path):
    return sorted(dir_path.glob("*.py")) if dir_path.exists() else []


def _sh_files(dir_path):
    return sorted(dir_path.glob("*.sh")) if dir_path.exists() else []


def import_graph():
    """Python import 依赖: 脚本A import 了脚本B的什么?"""
    py_files = _py_files(SCRIPTS)
    graph = defaultdict(list)
    reverse = defaultdict(list)

    for f in py_files:
        try:
            tree = ast.parse(f.read_text())
        except:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    graph[f.name].append(("import", name))
                    reverse[name].append(f.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    name = node.module.split(".")[0]
                    graph[f.name].append(("from", name))
                    reverse[name].append(f.name)

    # 去重
    for k in graph:
        graph[k] = list(set(graph[k]))
    for k in reverse:
        reverse[k] = list(set(reverse[k]))

    return graph, reverse


def call_graph():
    """subprocess / bash 调用关系"""
    py_files = _py_files(SCRIPTS)
    sh_files = _sh_files(SCRIPTS)
    graph = defaultdict(list)
    reverse = defaultdict(list)

    for f in py_files + sh_files:
        try:
            content = f.read_text()
        except:
            continue
        # 查找 subprocess.run(["python3", "...script.py" ...]) 或 bash script.sh
        for match in re.finditer(r"""["']([^"']+\.(?:py|sh))["']""", content):
            called = match.group(1)
            if "/" not in called:
                graph[f.name].append(called)
                reverse[called].append(f.name)

    for k in graph:
        graph[k] = list(set(graph[k]))
    for k in reverse:
        reverse[k] = list(set(reverse[k]))

    return graph, reverse


def blast_radius(file_name: str):
    """修改 file_name 会影响哪些脚本?"""
    imp, _ = import_graph()
    call, _ = call_graph()

    affected = set()
    base = file_name.replace(".py", "").replace(".sh", "")

    # 被 import 的
    for script, imports in imp.items():
        for _, name in imports:
            if name == base:
                affected.add(script)

    # 被 subprocess 调用的
    for script, calls in call.items():
        for c in calls:
            if base in c:
                affected.add(script)

    # 递归: 受影响脚本又被谁依赖?
    depth2 = set()
    for a in list(affected):
        a_base = a.replace(".py", "").replace(".sh", "")
        for script, imports in imp.items():
            for _, name in imports:
                if name == a_base and script not in affected:
                    depth2.add(script)
        for script, calls in call.items():
            for c in calls:
                if a_base in c and script not in affected:
                    depth2.add(script)

    return {
        "file": file_name,
        "directly_affected": sorted(affected),
        "indirectly_affected": sorted(depth2),
        "total_blast": len(affected) + len(depth2),
    }


def skill_deps():
    """Skills 交叉引用"""
    skill_refs = defaultdict(set)
    skill_refd_by = defaultdict(set)

    for skmd in SKILLS.rglob("SKILL.md"):
        skill_name = skmd.parent.name
        try:
            content = skmd.read_text()
        except:
            continue
        for other in SKILLS.rglob("SKILL.md"):
            other_name = other.parent.name
            if other_name != skill_name and other_name in content:
                skill_refs[skill_name].add(other_name)
                skill_refd_by[other_name].add(skill_name)

    return skill_refs, skill_refd_by


def dead_code():
    """疑似未使用的脚本"""
    py_files = _py_files(SCRIPTS)
    sh_files = _sh_files(SCRIPTS)
    all_scripts = [f.name for f in py_files + sh_files]

    # 被 import 或被 subprocess 调用的
    _, rev_imp = import_graph()
    _, rev_call = call_graph()

    referenced = set()
    for refs in [rev_imp, rev_call]:
        for name, callers in refs.items():
            for script in all_scripts:
                if name in script or script in name:
                    referenced.add(script)

    # CLI entry points: 有 if __name__ == "__main__" 或 argparse subparsers 的脚本
    # 这些是用户直接调用的, 不算 dead code
    for f in _py_files(SCRIPTS):
        try:
            content = f.read_text()
            if 'if __name__ == "__main__"' in content or "if __name__ == '__main__'" in content:
                referenced.add(f.name)
        except:
            pass
    for f in _sh_files(SCRIPTS):
        try:
            content = f.read_text()
            # shell scripts that use $1 or parse args are likely CLI tools
            if re.search(r'\$\{?1\}?|argparse|subparsers|--help', content):
                referenced.add(f.name)
        except:
            pass

    # 被 cron 引用的
    cron_file = HERMES / "cron" / "jobs.json"
    if cron_file.exists():
        import json
        cron_content = json.loads(cron_file.read_text())
        cron_str = json.dumps(cron_content)
        for script in all_scripts:
            if script in cron_str:
                referenced.add(script)

    # 被 config.yaml 引用的
    config_file = HERMES / "config.yaml"
    if config_file.exists():
        config_str = config_file.read_text()
        for script in all_scripts:
            if script in config_str:
                referenced.add(script)

    unreferenced = [s for s in all_scripts if s not in referenced and s != "code-intel.py"]
    return sorted(unreferenced)


def summary():
    """一站式代码健康摘要"""
    imp, rev = import_graph()
    call, _ = call_graph()
    srefs, _ = skill_deps()
    dead = dead_code()

    print("Hermes Code Intelligence — Summary")
    print("=" * 60)
    print(f"  Scripts (.py):  {len(_py_files(SCRIPTS))}")
    print(f"  Scripts (.sh):  {len(_sh_files(SCRIPTS))}")
    print(f"  Skills:         {len(list(SKILLS.rglob('SKILL.md')))}")
    print()

    # Top import dependencies
    top_imported = sorted(rev.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    print("  Most imported scripts:")
    for name, callers in top_imported:
        print(f"    {name:30s} ← {len(callers):2d} scripts")

    # Top subprocess-called
    top_called = sorted(call.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    print()
    print("  Most subprocess-called scripts:")
    for name, callers in top_called:
        print(f"    {name:30s} ← {len(callers):2d} scripts")

    # Top skill references
    top_skills = sorted(srefs.items(), key=lambda x: len(x[1]), reverse=True)[:5]
    print()
    print("  Most cross-referenced skills:")
    for name, refs in top_skills:
        print(f"    {name:30s} → {len(refs):2d} skills")

    print()
    print(f"  Potentially dead code: {len(dead)} scripts")
    if dead:
        for d in dead:
            print(f"    - {d}")

    # Blast radius for critical files
    critical = ["route_store.py", "model-router.py", "record-trace.sh", "pricing.py"]
    print()
    print("  Blast radius (critical files):")
    for c in critical:
        br = blast_radius(c)
        print(f"    {c:30s} → {br['total_blast']:2d} affected "
              f"(direct={len(br['directly_affected'])} indirect={len(br['indirectly_affected'])})")


def cli():
    parser = argparse.ArgumentParser(description="Code Intel — Hermes 原生代码智能引擎")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("import-graph", help="Python import 依赖图")
    sub.add_parser("call-graph", help="subprocess 调用图")

    br = sub.add_parser("blast-radius", help="修改某文件的影响范围")
    br.add_argument("--file", required=True)

    sub.add_parser("skill-deps", help="Skills 交叉引用")
    sub.add_parser("dead-code", help="疑似未使用的脚本")
    sub.add_parser("summary", help="一站式代码健康摘要")

    args = parser.parse_args()

    if args.cmd == "import-graph":
        imp, rev = import_graph()
        print("Import dependencies:")
        for script, imports in sorted(imp.items()):
            names = [n for _, n in imports]
            print(f"  {script:35s} → {', '.join(sorted(set(names))[:5])}")

    elif args.cmd == "call-graph":
        call, rev = call_graph()
        print("Subprocess call graph:")
        for script, calls in sorted(call.items()):
            if calls:
                print(f"  {script:35s} → {', '.join(sorted(set(calls))[:5])}")

    elif args.cmd == "blast-radius":
        result = blast_radius(args.file)
        print(f"Blast radius: {args.file}")
        print(f"  Directly affected ({len(result['directly_affected'])}):")
        for f in result["directly_affected"]:
            print(f"    - {f}")
        if result["indirectly_affected"]:
            print(f"  Indirectly affected ({len(result['indirectly_affected'])}):")
            for f in result["indirectly_affected"]:
                print(f"    - {f}")
        print(f"  Total blast: {result['total_blast']} files")

    elif args.cmd == "skill-deps":
        refs, refd = skill_deps()
        print("Skill cross-references (top 20):")
        for skill, refs_set in sorted(refs.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
            print(f"  {skill:30s} → {', '.join(sorted(refs_set)[:5])}")

    elif args.cmd == "dead-code":
        dead = dead_code()
        print(f"Potentially dead code ({len(dead)}):")
        for d in dead:
            print(f"  - {d}")

    elif args.cmd == "summary":
        summary()

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()

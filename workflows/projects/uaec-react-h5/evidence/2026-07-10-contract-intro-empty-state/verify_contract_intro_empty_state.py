from pathlib import Path
import sys

source = Path(
    "/Users/charles/Desktop/folder/work/uaec-react-h5/src/pages/ContractPage/ContractInterface/ContractInterface.tsx"
).read_text()

checks = {
    "loading_state_preserved": "加载中..." in source,
    "empty_intro_checked": "coinInfoHtml.trim()" in source,
    "nonblank_fallback": "暂无简介" in source,
    "fallback_is_status": 'role="status"' in source,
    "html_render_preserved": "dangerouslySetInnerHTML={{ __html: coinInfoHtml }}" in source,
}

for name, passed in checks.items():
    print(f"{name}={'PASS' if passed else 'FAIL'}")

sys.exit(0 if all(checks.values()) else 1)

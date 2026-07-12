from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT = Path.home() / ".hermes" / "scripts" / "gitnexus_fusion_selfcheck.py"
spec = spec_from_file_location("gitnexus_fusion_selfcheck", SCRIPT)
assert spec and spec.loader
module = module_from_spec(spec)
spec.loader.exec_module(module)


def test_contract_bridge_search_uses_fts_or_for_independently_indexed_terms():
    query = module.BRAIN_SEARCH_TERMS[2]

    assert query == '"Contract Bridge" OR contract_id OR shape_check'

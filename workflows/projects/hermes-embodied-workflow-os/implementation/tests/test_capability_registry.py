import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.contracts import ContractError
from hewos_core.registry import CapabilityRegistry


def valid_manifest(**overrides):
    manifest = {
        "capability_id": "cap.web.image_upload",
        "actor_id": "actor.human.operator",
        "adapter_id": "adapter.web.mock",
        "capability_type": "observe.image.single",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "risk_class": "none",
        "required_gates": [],
        "dry_run_supported": True,
        "readback_required": False,
        "audit_required": False,
        "idempotency_policy": "not_required",
    }
    manifest.update(overrides)
    return manifest


class CapabilityRegistryTest(unittest.TestCase):
    def test_rejects_manifest_missing_risk_class(self):
        registry = CapabilityRegistry()
        manifest = valid_manifest()
        manifest.pop("risk_class")

        with self.assertRaisesRegex(ContractError, "risk_class"):
            registry.register(manifest)

    def test_rejects_physical_capability_without_readback_audit_and_gates(self):
        registry = CapabilityRegistry()
        manifest = valid_manifest(
            capability_id="cap.robot.grip",
            adapter_id="adapter.robot.mock",
            capability_type="act.robot.grip",
            risk_class="physical_action",
            required_gates=[],
            readback_required=False,
            audit_required=False,
            idempotency_policy="not_required",
        )

        with self.assertRaisesRegex(ContractError, "readback_required"):
            registry.register(manifest)

    def test_registers_observation_capability_and_queries_by_type(self):
        registry = CapabilityRegistry()
        manifest = valid_manifest()

        registered = registry.register(manifest)

        self.assertEqual(registered["capability_id"], "cap.web.image_upload")
        self.assertEqual(
            [item["capability_id"] for item in registry.find_by_type("observe.image.single")],
            ["cap.web.image_upload"],
        )


if __name__ == "__main__":
    unittest.main()

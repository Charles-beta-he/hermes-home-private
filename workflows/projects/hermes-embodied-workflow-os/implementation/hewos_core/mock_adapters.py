def _manifest(capability_id, adapter_id, capability_type, risk_class="none", **overrides):
    manifest = {
        "capability_id": capability_id,
        "actor_id": overrides.pop("actor_id", f"actor.{adapter_id}"),
        "adapter_id": adapter_id,
        "capability_type": capability_type,
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "risk_class": risk_class,
        "required_gates": [],
        "dry_run_supported": True,
        "readback_required": False,
        "audit_required": False,
        "idempotency_policy": "not_required",
    }
    manifest.update(overrides)
    return manifest


def mock_adapter_manifests():
    return [
        _manifest("cap.cli.text", "adapter.cli.mock", "observe.text"),
        _manifest("cap.web.image_upload", "adapter.web.mock", "observe.image.single"),
        _manifest("cap.glasses.first_person_image", "adapter.glasses.mock", "observe.image.single"),
        _manifest("cap.embedded.fixed_camera", "adapter.embedded.mock", "observe.fixed_camera"),
        _manifest(
            "cap.robot.grip",
            "adapter.robot.mock",
            "act.robot.grip",
            risk_class="physical_action",
            required_gates=["SafetyGate", "ExternalControlGate"],
            readback_required=True,
            audit_required=True,
            idempotency_policy="required_per_intent",
        ),
    ]

HIGH_RISK_ACTIONS = {"physical_action", "destructive", "payment_or_credential"}


def _find_adapter(available_capabilities, wanted):
    for adapter_id, capabilities in available_capabilities.items():
        if wanted in capabilities:
            return adapter_id
    return None


def recommend_entry(required_observation=None, required_action=None, risk_level="none", available_capabilities=None):
    available_capabilities = available_capabilities or {}
    if risk_level in HIGH_RISK_ACTIONS:
        confirmer = _find_adapter(available_capabilities, "confirm.onsite_human")
        if not confirmer:
            return {
                "status": "blocked_human_gate",
                "primary": None,
                "reason": "High-risk action requires onsite human confirmation before execution.",
            }
    if required_observation == "first_person_visual":
        primary = _find_adapter(available_capabilities, "observe.first_person_view")
        if primary:
            return {"status": "recommended", "primary": primary, "reason": "Need first-person visual evidence."}
    if required_action == "edit.taskgraph":
        primary = _find_adapter(available_capabilities, "edit.taskgraph")
        if primary:
            return {"status": "recommended", "primary": primary, "reason": "TaskGraph editing needs workbench-class surface."}
    if required_action:
        primary = _find_adapter(available_capabilities, required_action)
        if primary:
            return {"status": "recommended", "primary": primary, "reason": "Adapter has the required action capability."}
    return {"status": "blocked_no_capability", "primary": None, "reason": "No available adapter has the required capability."}

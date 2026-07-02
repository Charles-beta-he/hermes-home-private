from .contracts import validate_capability_manifest


class CapabilityRegistry:
    def __init__(self):
        self._items = {}

    def register(self, manifest):
        validated = validate_capability_manifest(manifest)
        self._items[validated["capability_id"]] = validated
        return dict(validated)

    def find_by_type(self, capability_type):
        return [
            dict(item)
            for item in self._items.values()
            if item["capability_type"] == capability_type
        ]

import pathlib
import sys

source = pathlib.Path(
    "/Users/charles/Desktop/folder/work/uaec-react-h5/src/pages/ContractPage/ContractInterface/ContractInterface.tsx"
).read_text()

checks = {
    "tracks active symbol": "activeCollectionSymbolRef" in source,
    "tracks login state": "activeCollectionLoginRef" in source,
    "tracks request generation": "collectionRequestGenerationRef" in source,
    "invalidates generation on context change": "collectionRequestGenerationRef.current += 1;" in source,
    "status request captures generation": "checkCollectionStatus(symbol, requestGeneration)" in source,
    "status response checks generation": "requestGeneration === collectionRequestGenerationRef.current" in source,
    "status response checks login": "activeCollectionLoginRef.current" in source,
    "toggle request captures generation": "toggleCollection(symbol, !isCollected, requestGeneration)" in source,
    "mutation response checks generation": "requestGeneration !== collectionRequestGenerationRef.current" in source,
    "anonymous click remains local navigation": 'navigate("/login");' in source,
}
for name, passed in checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

# Deterministic acceptance model for the intended generation guard.
def accepted(request, current):
    return (
        current["logged_in"]
        and request["symbol"] == current["symbol"]
        and request["generation"] == current["generation"]
    )

model_checks = {
    "direct A to B late A rejected": not accepted(
        {"symbol": "A", "generation": 1},
        {"symbol": "B", "generation": 2, "logged_in": True},
    ),
    "logout same-symbol late response rejected": not accepted(
        {"symbol": "A", "generation": 1},
        {"symbol": "A", "generation": 2, "logged_in": False},
    ),
    "A-B-A old A response rejected": not accepted(
        {"symbol": "A", "generation": 1},
        {"symbol": "A", "generation": 3, "logged_in": True},
    ),
    "latest A response accepted": accepted(
        {"symbol": "A", "generation": 3},
        {"symbol": "A", "generation": 3, "logged_in": True},
    ),
}
for name, passed in model_checks.items():
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

sys.exit(0 if all(checks.values()) and all(model_checks.values()) else 1)

import subprocess

def check():
    try:
        r = subprocess.run(["hermes", "auth", "status", "openai-codex"],
                           capture_output=True, text=True, timeout=15)
        logged_out = "logged out" in r.stdout.lower() or "logged out" in r.stderr.lower()
        return {"ok": not logged_out, "detail": r.stdout.strip()[:200], "metrics": {}}
    except Exception as e:
        return {"ok": False, "detail": str(e), "metrics": {}}

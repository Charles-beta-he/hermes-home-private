# Telemetry Freshness Pitfall

The `external_control_gate.py execute` command enforces `current_telemetry.timestamp <= 5 seconds ago`.
This is a server-side check and cannot be bypassed.

## The trap

If you:
1. Generate action packet in one python invocation (timestamp set to T0)
2. Wait a few seconds (user confirmation, terminal switch, etc.)
3. Call `external_control_gate.py execute` in a separate invocation (now T0 + N seconds where N > 5)

The gate will fail: `"telemetry too old for real-action gate: age_seconds=N.NNNN"`

## The fix

Generate the action packet AND call the gate in the SAME script invocation, OR set the
timestamp to `datetime.now(timezone.utc).isoformat()` at the exact moment you call the gate
(not when you wrote the packet file).

```python
# WRONG: timestamp set at file-write time, gate called seconds later
action["current_telemetry"]["timestamp"] = datetime.now(timezone.utc).isoformat()
Path("action.json").write_text(json.dumps(action))
# ... user thinks for 8 seconds ...
os.system("python3 external_control_gate.py execute action.json ...")  # FAILS: age=8s

# RIGHT: timestamp set at gate-call time
action["current_telemetry"]["timestamp"] = datetime.now(timezone.utc).isoformat()
Path("action.json").write_text(json.dumps(action))
subprocess.run(["python3", "external_control_gate.py", "execute", "action.json", ...])  # age < 1s
```

Best: put both in one python invocation so there's no shell-level delay.

# Node control-plane patterns for long-video workers

Use this when extending local long-video extraction from one controller machine to LAN worker nodes.

## Core lesson

Do not equate "SSH login works" with "node is connected", and do not equate "SSH login fails" with "node is unusable". A node may already expose task-relevant services over HTTP:

- Hermes Edge Worker: `/health`, `/info`, `/command`, `/execute`
- MLX/OpenAI-compatible LLM server: `/health`, `/v1/models`, `/v1/chat/completions`
- Vision node: `/health`
- Ollama: `/api/tags`, `/api/embeddings`

Probe service endpoints first, then choose the control path.

## Discovery order

1. Identify candidate IPs from local subnet, ARP/neighbors, SSH config, Tailscale/ZeroTier if present.
2. Probe task-relevant ports before asking for SSH:
   - `8080` for local MLX/OpenAI-compatible LLM servers
   - `9000` for vision-node style services
   - `9001`/`9002` for Hermes Edge Worker services
   - `11434` for Ollama
   - `22` for SSH as a fallback/control channel, not the only channel
3. For each open port, call safe read-only endpoints:
   - `/health`
   - `/info`
   - `/v1/models`
   - `/api/tags`
4. Only try mutating or shell endpoints after confirming auth method and scope.
5. Write a `nodes.json` with role-specific URLs, not just host/IP.

## Role classification

A single machine can be multiple node types:

```json
{
  "name": "node-192-168-31-130-edge",
  "host": "192.168.31.130",
  "roles": ["edge-worker", "video-worker", "mlx-llm", "vision-node"],
  "edge_url": "http://192.168.31.130:9002",
  "mlx_url": "http://192.168.31.130:8080",
  "vision_url": "http://192.168.31.130:9000"
}
```

## Auth boundary interpretation

If `/health` works but `/command` or `/execute` returns `401`, the node is connected but command control is not authorized. The next step is token/scope synchronization for the Edge Worker, not generic SSH setup.

Report this distinction explicitly:

- service reachable: yes/no
- role usable without shell: yes/no
- shell/command execution authorized: yes/no
- exact blocked boundary: token mismatch, command allowlist, SSH key, service not listening, etc.

Never print or persist plaintext tokens. Use `[REDACTED]` for any token material in reports.

## Minimal user-cooperation pattern

When the user wants the shortest path, do not ask them to manually copy tokens, inspect plist files, or run several commands. Prefer a temporary one-line helper:

1. On the controller, create a private random-slug script under `/tmp` and serve it with `python3 -m http.server --bind CONTROLLER_IP PORT`.
2. The user runs exactly one command on the node:
   ```bash
   curl -fsSL http://CONTROLLER_IP:PORT/RANDOM.sh | bash
   ```
3. The helper should:
   - create/backup `~/.hermes/.env`
   - write or replace `HERMES_EDGE_WORKER_ACCESS` without printing it
   - patch or rewrite `~/.hermes/edge-worker/start.sh` if it passes `--token` explicitly
   - stop launchctl/old `edge_worker.py` processes if needed
   - restart Edge Worker on `0.0.0.0:9002`
   - print `DONE ... health=...` or print logs/ps/curl errors on failure
4. After the user reports completion, verify from the controller using both read-only and command endpoints.
5. Stop the temporary HTTP server and remove the private script after verification.

Important startup pitfall: updating `.env` alone may not affect a worker launched with a hardcoded `--token` argument in `start.sh` or a launch agent. If `/health` remains public but `/command` still returns `401`, patch the startup token path. If the port becomes connection-refused, the restart failed; generate a diagnostic helper that rewrites `start.sh`, launches it, and prints `worker.log` rather than asking the user to inspect manually.

## Command allowlist and reload pattern

If `/info` shows a valid token but `security.allowed_commands: []`, command auth is working but shell execution is still blocked by the allowlist. In that state:

1. Use already-authorized `read_file`, `write_file`, and `list_dir` to inspect and update the worker config; do not ask for SSH unless no API write path exists.
2. Add only the command prefixes needed for the class of work, for example `python3`, `ffmpeg`, `ffprobe`, `ollama`, `uvx`, `mkdir`, `cp`, `mv`, `rm`, `find`, `ps`, `pkill`, and `curl` for video workers.
3. Expand `allowed_paths` only to required sandboxes such as the node home directory and `/tmp`.
4. Remember that many Edge Worker implementations load `allowed_commands` at process start. After writing config, restart the worker before expecting `run_command` to work.
5. If `run_command` is not yet allowed, the worker usually cannot restart itself. Use the one-line helper or another external control channel for that one restart, then resume full automation.

When testing `run_command`, avoid multi-command shell strings like `hostname; whoami; ...` unless the first token exactly matches an allowlist rule. Some allowlist implementations compare `shlex.split(command)[0]`, so a semicolon-adjacent first token such as `hostname;` may be rejected. For compound probes, write a small script under an allowed path (for example `/tmp/video_worker_probe.py`) with `write_file`, then run `python3 /tmp/video_worker_probe.py`.

## Remote Ollama startup pattern

Starting `ollama serve` on a node with a plain background shell command may bind only to localhost depending on the inherited environment. For LAN embedding, start it with `OLLAMA_HOST=0.0.0.0:11434` in the process environment, then verify from both sides:

- node local: `curl -fsS http://127.0.0.1:11434/api/tags`
- controller: `python3 -m video_essence.cli ollama-health --ollama-host http://NODE:11434 --model nomic-embed-text`

A robust remote start is to write and run a tiny Python script that `Popen`s `ollama serve` with `env["OLLAMA_HOST"] = "0.0.0.0:11434"`, redirects logs to `/tmp/ollama-serve.log`, and detaches with `start_new_session=True`.

## Long-video application

- Remote MLX/LLM endpoint can be used for final reduce or assisted synthesis without SSH.
- Remote Ollama endpoint can be used for embeddings/semantic QA without SSH.
- Remote Edge Worker command control is needed for running `ffmpeg`, ASR, OCR, or moving artifacts on the node.
- Vision nodes can add visual analysis if they have a suitable API, even when not available as shell workers.

## Pitfall from session

A node at `192.168.31.130` was initially misclassified as needing SSH authorization because SSH login failed. Further port probing showed:

- `:8080` MLX LLM service healthy
- `:9000` vision-node healthy
- `:9002` Hermes Edge Worker `/health` healthy
- Edge Worker `/command` and `/execute` returned `401`
- `:11434` Ollama unavailable

Correct interpretation: it was already a connected service node, but Edge Worker command authorization/token scope was not synchronized.

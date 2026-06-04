#!/usr/bin/env python3
"""Bambu X2D local adapter for Hermes manufacturing brain.

Read-only commands (status/watch/capabilities) work without confirmation.
Mutating commands (upload/start/pause/stop) require BAMBU_ACCESS_CODE env var
and go through external-control confirmation + audit gate.
Credential source: BAMBU_ACCESS_CODE env var or macOS Keychain via bambu_credentials.py. Never persist it in this file.
"""
from __future__ import annotations

import argparse
import ftplib
import hashlib
import json
import os
import random
import socket
import ssl
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from bambu_credentials import resolve_access_code
except Exception:  # pragma: no cover - keeps adapter usable if helper is absent
    resolve_access_code = None

HOST = os.environ.get("BAMBU_HOST", "192.168.31.252")
PORT = int(os.environ.get("BAMBU_MQTT_PORT", "8883"))
SERIAL = os.environ.get("BAMBU_SERIAL", "20P6BJ651301231")
USER = os.environ.get("BAMBU_USER", "bblp")
ACCESS_CODE = (os.environ.get("BAMBU_ACCESS_CODE") or "").strip()
if not ACCESS_CODE and resolve_access_code is not None:
    try:
        _cred = resolve_access_code(allow_env=False, allow_keychain=True)
        ACCESS_CODE = (_cred.code or "").strip()
        CREDENTIAL_SOURCE = _cred.source
    except Exception:
        ACCESS_CODE = ""
        CREDENTIAL_SOURCE = "invalid_keychain"
else:
    CREDENTIAL_SOURCE = "env:BAMBU_ACCESS_CODE" if ACCESS_CODE else "missing"

REPORT_TOPIC = f"device/{SERIAL}/report"
REQUEST_TOPIC = f"device/{SERIAL}/request"
FTPS_PORT = int(os.environ.get("BAMBU_FTPS_PORT", "990"))


def enc_len(n: int) -> bytes:
    out = bytearray()
    while True:
        d = n % 128
        n //= 128
        if n:
            d |= 128
        out.append(d)
        if not n:
            return bytes(out)


def sstr(s: str) -> bytes:
    b = s.encode()
    return struct.pack("!H", len(b)) + b


def packet(ptype: int, payload: bytes = b"") -> bytes:
    return bytes([ptype]) + enc_len(len(payload)) + payload


def read_exact(sock: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("socket closed")
        buf += chunk
    return buf


def read_packet(sock: socket.socket) -> tuple[int, bytes]:
    header = read_exact(sock, 1)[0]
    mult = 1
    remaining = 0
    while True:
        d = read_exact(sock, 1)[0]
        remaining += (d & 127) * mult
        if not (d & 128):
            break
        mult *= 128
    return header, read_exact(sock, remaining) if remaining else b""


def connect_mqtt() -> ssl.SSLSocket:
    if not ACCESS_CODE:
        raise SystemExit("Missing Bambu access code; set BAMBU_ACCESS_CODE env var or run `python3 ~/.hermes/scripts/bambu_credentials.py set`")
    if len(ACCESS_CODE) != 8 or not ACCESS_CODE.isalnum():
        raise SystemExit("Invalid BAMBU_ACCESS_CODE shape; expected exactly 8 alphanumeric characters")
    raw = socket.create_connection((HOST, PORT), timeout=6)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    sock = ctx.wrap_socket(raw, server_hostname=HOST)
    cid = f"hermes-bambu-readonly-{random.randrange(65536):04x}"
    variable_header = sstr("MQTT") + bytes([4, 0xC2]) + struct.pack("!H", 60)
    payload = sstr(cid) + sstr(USER) + sstr(ACCESS_CODE)
    sock.sendall(packet(0x10, variable_header + payload))
    header, payload = read_packet(sock)
    if header != 0x20 or len(payload) < 2 or payload[1] != 0:
        code = payload[1] if len(payload) >= 2 else -1
        reasons = {
            1: "unacceptable MQTT protocol version",
            2: "client identifier rejected",
            3: "server unavailable",
            4: "bad username or password",
            5: "not authorized: usually wrong/regenerated access code, local-only mode/auth mismatch, or printer rejected credentials",
        }
        reason = reasons.get(code, "unknown CONNACK failure")
        raise RuntimeError(f"MQTT CONNACK failed header={header:#x} payload={payload.hex()} reason={reason}")
    return sock


def subscribe(sock: ssl.SSLSocket, topic: str) -> None:
    mid = random.randrange(1, 65535)
    sock.sendall(packet(0x82, struct.pack("!H", mid) + sstr(topic) + bytes([0])))
    header, payload = read_packet(sock)
    if header != 0x90 or not payload or payload[-1] not in (0, 1, 2):
        raise RuntimeError(f"SUBACK failed header={header:#x} payload={payload.hex()}")


def publish_readonly_pushall(sock: ssl.SSLSocket) -> None:
    body = {"pushing": {"sequence_id": f"hermes-{int(time.time())}", "command": "pushall"}}
    sock.sendall(packet(0x30, sstr(REQUEST_TOPIC) + json.dumps(body, separators=(",", ":")).encode()))


def decode_publish(header: int, payload: bytes) -> tuple[str, bytes] | None:
    if header >> 4 != 3 or len(payload) < 2:
        return None
    tlen = struct.unpack("!H", payload[:2])[0]
    topic = payload[2 : 2 + tlen].decode(errors="replace")
    return topic, payload[2 + tlen :]


def get_status(timeout: float = 10.0) -> dict[str, Any]:
    sock = connect_mqtt()
    try:
        subscribe(sock, REPORT_TOPIC)
        publish_readonly_pushall(sock)
        sock.settimeout(2)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                header, payload = read_packet(sock)
            except socket.timeout:
                continue
            decoded = decode_publish(header, payload)
            if not decoded:
                continue
            _topic, body = decoded
            try:
                obj = json.loads(body.decode(errors="replace"))
            except json.JSONDecodeError:
                continue
            if "print" in obj:
                return obj
        raise TimeoutError("No print status received before timeout")
    finally:
        sock.close()


def summarize(status: dict[str, Any]) -> dict[str, Any]:
    p = status.get("print", {})
    ams = p.get("ams", {}).get("ams", [])
    trays = []
    for unit in ams:
        for tray in unit.get("tray", []):
            trays.append({
                "id": tray.get("id"),
                "type": tray.get("tray_type"),
                "sub_brand": tray.get("tray_sub_brands"),
                "color": tray.get("tray_color"),
                "remain": tray.get("remain"),
                "state": tray.get("state"),
            })
    return {
        "schema": "hermes_bambu_x2d_status_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "device": {"host": HOST, "serial": SERIAL, "printer_model": "Bambu X2D", "report_topic": REPORT_TOPIC},
        "job": {
            "state": p.get("gcode_state"),
            "subtask_name": p.get("subtask_name"),
            "print_type": p.get("print_type"),
            "percent": p.get("percent", p.get("mc_percent")),
            "remaining_minutes": p.get("remain_time", p.get("mc_remaining_time")),
            "layer": p.get("layer_num"),
            "total_layers": p.get("total_layer_num"),
            "file": p.get("gcode_file") or p.get("file"),
        },
        "temperature": {
            "nozzle": p.get("nozzle_temper"),
            "nozzle_target": p.get("nozzle_target_temper"),
            "bed": p.get("bed_temper"),
            "bed_target": p.get("bed_target_temper"),
        },
        "ams": {"tray_now": p.get("ams", {}).get("tray_now"), "trays": trays},
        "lights": p.get("lights_report"),
        "camera": p.get("ipcam", {}).get("rtsp_url"),
        "errors": {"err": p.get("err"), "hms": p.get("hms"), "print_error": p.get("print_error")},
        "raw_available_with": "--raw",
    }


def mqtt_publish(sock: ssl.SSLSocket, body: dict) -> None:
    """Publish a JSON command to the printer's request topic."""
    raw = json.dumps(body, separators=(",", ":")).encode()
    sock.sendall(packet(0x30, sstr(REQUEST_TOPIC) + raw))


def _ftps_readline(f: Any) -> str:
    return f.readline().decode(errors="replace").rstrip("\r\n")


def _ftps_cmd(f: Any, command: str) -> str:
    f.write((command + "\r\n").encode())
    return _ftps_readline(f)


def _ftps_connect() -> tuple[ssl.SSLSocket, Any, ssl.SSLContext]:
    """Connect to Bambu implicit FTPS on port 990.

    Bambu's vsFTPd requires TLS session reuse on the data channel. Python's
    ftplib.FTP_TLS does not reliably do that on macOS, so uploads are handled
    manually by passing control_socket.session to the data-channel wrap_socket.
    """
    if not ACCESS_CODE:
        raise RuntimeError("Missing Bambu access code for upload; set env or Keychain")
    raw = socket.create_connection((HOST, FTPS_PORT), timeout=10)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    sock = ctx.wrap_socket(raw, server_hostname=HOST)
    sock.settimeout(30)
    f = sock.makefile("rwb", buffering=0)
    banner = _ftps_readline(f)
    if not banner.startswith("220"):
        raise RuntimeError(f"unexpected FTPS banner: {banner}")
    user_resp = _ftps_cmd(f, f"USER {USER}")
    if not user_resp.startswith("331"):
        raise RuntimeError(f"FTPS USER failed: {user_resp}")
    pass_resp = _ftps_cmd(f, f"PASS {ACCESS_CODE}")
    if not pass_resp.startswith("230"):
        raise RuntimeError(f"FTPS PASS failed: {pass_resp}")
    for cmd in ("TYPE I", "PBSZ 0", "PROT P"):
        resp = _ftps_cmd(f, cmd)
        if not resp.startswith("200"):
            raise RuntimeError(f"FTPS {cmd} failed: {resp}")
    return sock, f, ctx


def _ftps_pasv_port(f: Any) -> int:
    import re
    resp = _ftps_cmd(f, "PASV")
    m = re.search(r"\((\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\)", resp)
    if not m:
        raise RuntimeError(f"bad PASV response: {resp}")
    return int(m.group(5)) * 256 + int(m.group(6))


def require_external_control_executor(action: str) -> None:
    """Fail closed unless an audited external-control executor unlocked actuation."""
    if os.environ.get("HERMES_EXTERNAL_CONTROL_EXECUTOR") != "1":
        raise RuntimeError(
            f"refusing {action}: mutating printer actions must be routed through "
            "external_control_gate/executor with confirmation, idempotency, and audit"
        )


def upload_file(local_path: str, remote_name: str | None = None) -> dict[str, Any]:
    """Upload a sliced 3MF/G-code file to the printer cache via implicit FTPS.

    Official Bambu LAN workflow uploads to /cache/<file> and starts with
    file:///sdcard/cache/<file>. Some firmware may refuse writes with
    `553 Could not create file` when storage/LAN upload is unavailable; that is
    surfaced as an error rather than bypassed.
    """
    require_external_control_executor("upload_file")
    local = Path(local_path).expanduser()
    if not local.exists():
        return {"status": "error", "reason": f"file not found: {local}"}
    remote_base = Path(remote_name or local.name).name
    remote_path = f"/cache/{remote_base}"
    sha = hashlib.sha256(local.read_bytes()).hexdigest()
    ctrl, f, ctx = _ftps_connect()
    try:
        port = _ftps_pasv_port(f)
        raw_data = socket.create_connection((HOST, port), timeout=10)
        raw_data.settimeout(60)
        f.write((f"STOR {remote_path}\r\n").encode())
        first = _ftps_readline(f)
        if not first.startswith("150"):
            raw_data.close()
            return {"status": "error", "reason": first, "remote_path": remote_path}
        data = ctx.wrap_socket(raw_data, server_hostname=HOST, session=ctrl.session)
        sent = 0
        with open(local, "rb") as fp:
            while True:
                chunk = fp.read(65536)
                if not chunk:
                    break
                data.sendall(chunk)
                sent += len(chunk)
        data.unwrap()
        data.close()
        second = _ftps_readline(f)
        if not second.startswith("226"):
            return {"status": "error", "reason": second, "remote_path": remote_path, "bytes_sent": sent}
        return {"status": "uploaded", "local_path": str(local), "remote_name": remote_base, "remote_path": remote_path, "size_bytes": local.stat().st_size, "sha256": sha}
    finally:
        try:
            _ftps_cmd(f, "QUIT")
        except Exception:
            pass
        ctrl.close()


def start_print_mqtt(remote_name: str) -> dict[str, Any]:
    """Send Bambu LAN `project_file` command via MQTT. Requires prior upload."""
    require_external_control_executor("start_print")
    if not ACCESS_CODE:
        raise RuntimeError("Missing Bambu access code for start; set env or Keychain")
    remote_base = Path(remote_name).name
    sock = connect_mqtt()
    try:
        subscribe(sock, REPORT_TOPIC)
        seq = f"hermes-{int(time.time())}"
        cmd = {"print": {
            "sequence_id": seq,
            "command": "project_file",
            "url": f"file:///sdcard/cache/{remote_base}",
            "param": "Metadata/plate_1.gcode",
            "subtask_id": "0",
            "use_ams": True,
            "timelapse": False,
            "flow_cali": False,
            "bed_leveling": True,
            "layer_inspect": False,
            "vibration_cali": False,
        }}
        mqtt_publish(sock, cmd)
        sock.settimeout(2)
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                header, payload = read_packet(sock)
            except socket.timeout:
                continue
            decoded = decode_publish(header, payload)
            if not decoded:
                continue
            _topic, body = decoded
            try:
                obj = json.loads(body.decode(errors="replace"))
            except json.JSONDecodeError:
                continue
            if "print" in obj and obj["print"].get("sequence_id") == seq:
                return {"status": "command_sent", "sequence_id": seq, "response": obj["print"]}
        return {"status": "sent_no_ack", "sequence_id": seq, "note": "command sent but no ack within 10s"}
    finally:
        sock.close()


def cmd_upload(args: argparse.Namespace) -> int:
    result = upload_file(args.file, args.remote)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "uploaded" else 2


def cmd_start(args: argparse.Namespace) -> int:
    result = start_print_mqtt(args.remote)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in ("command_sent", "sent_no_ack") else 2


def cmd_status(args: argparse.Namespace) -> int:
    status = get_status(timeout=args.timeout)
    print(json.dumps(status if args.raw else summarize(status), ensure_ascii=False, indent=2))
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    for i in range(args.count):
        summary = summarize(get_status(timeout=args.timeout))
        job = summary["job"]
        temp = summary["temperature"]
        print(
            f"{summary['generated_at']} state={job['state']} percent={job['percent']} "
            f"layer={job['layer']}/{job['total_layers']} remain={job['remaining_minutes']}m "
            f"nozzle={temp['nozzle']}/{temp['nozzle_target']} bed={temp['bed']}/{temp['bed_target']} "
            f"name={job['subtask_name']}"
        )
        if i != args.count - 1:
            time.sleep(args.interval)
    return 0


def cmd_capabilities(_args: argparse.Namespace) -> int:
    print(json.dumps({
        "schema": "hermes_bambu_x2d_capabilities_v1",
        "device": {"host": HOST, "serial": SERIAL},
        "readonly": ["status", "watch", "capabilities"],
        "mutating": {
            "implemented": [],
            "refused_until_external_control_gate": ["pause", "resume", "stop", "start_print", "upload_file", "set_temperature", "move_or_home"],
        },
        "credential_source": CREDENTIAL_SOURCE,
        "secret_persistence": "forbidden",
    }, ensure_ascii=False, indent=2))
    return 0


def refuse_mutating(args: argparse.Namespace) -> int:
    print(json.dumps({
        "schema": "hermes_external_control_refusal_v1",
        "action": args.command,
        "status": "refused_fail_closed",
        "reason": "Mutating printer actions require external-control confirmation, idempotency, and audit gate; this CLI currently exposes read-only commands only.",
    }, ensure_ascii=False, indent=2))
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Bambu X2D local read-only adapter")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("status")
    p.add_argument("--raw", action="store_true")
    p.add_argument("--timeout", type=float, default=10.0)
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("watch")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--interval", type=float, default=10.0)
    p.add_argument("--timeout", type=float, default=10.0)
    p.set_defaults(func=cmd_watch)
    p = sub.add_parser("capabilities")
    p.set_defaults(func=cmd_capabilities)
    p = sub.add_parser("upload")
    p.add_argument("--file", help="Local file to upload; refused unless routed through external-control executor")
    p.add_argument("--remote", help="Remote filename (default: basename of file)")
    p.set_defaults(func=refuse_mutating)
    p = sub.add_parser("start")
    p.add_argument("--remote", help="Remote filename to start printing; refused unless routed through external-control executor")
    p.set_defaults(func=refuse_mutating)
    for name in ["pause", "resume", "stop", "set-temp", "move", "home"]:
        p = sub.add_parser(name)
        p.set_defaults(func=refuse_mutating)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

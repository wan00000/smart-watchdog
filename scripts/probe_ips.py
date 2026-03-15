#!/usr/bin/env python3

from __future__ import annotations

import ipaddress
import json
import os
import socket
from datetime import datetime
from typing import Any, Iterable


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def append_log(message: str) -> None:
    log_file = os.getenv("PROBE_LOG_FILE", "").strip()
    if not log_file:
        return
    directory = os.path.dirname(log_file)
    if directory:
        os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def parse_ports(raw: str) -> list[int]:
    ports: list[int] = []
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        try:
            port = int(item)
        except ValueError:
            append_log(f"Ignoring invalid port value '{item}'")
            continue
        if 1 <= port <= 65535:
            ports.append(port)
        else:
            append_log(f"Ignoring out-of-range port value '{item}'")
    return ports


def load_targets(path: str, limit: int) -> list[tuple[str, int]]:
    if not path:
        raise ValueError("PROBE_INPUT_FILE is empty")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Probe input file not found: {path}")

    targets: list[tuple[str, int]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                append_log(f"Skipping malformed line: {line}")
                continue
            ip_text = parts[0]
            try:
                count = int(parts[1])
            except ValueError:
                append_log(f"Skipping line with invalid count: {line}")
                continue
            targets.append((ip_text, count))
            if len(targets) >= limit:
                break
    return targets


def reverse_dns(ip_text: str) -> dict[str, Any]:
    try:
        host, aliases, addresses = socket.gethostbyaddr(ip_text)
        return {
            "ok": True,
            "hostname": host,
            "aliases": aliases,
            "addresses": addresses,
        }
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def tcp_probe(ip_text: str, port: int, timeout: int) -> dict[str, Any]:
    try:
        with socket.create_connection((ip_text, port), timeout=timeout):
            return {"ok": True, "port": port}
    except OSError as exc:
        return {"ok": False, "port": port, "error": str(exc)}


def iter_results(targets: Iterable[tuple[str, int]]) -> list[dict[str, Any]]:
    include_private = _env_bool("PROBE_INCLUDE_PRIVATE", False)
    do_reverse_dns = _env_bool("PROBE_REVERSE_DNS", True)
    do_connect = _env_bool("PROBE_CONNECT_ENABLED", True)
    timeout = _env_int("PROBE_TIMEOUT", 2)
    ports = parse_ports(os.getenv("PROBE_PORTS", "80,443"))

    results: list[dict[str, Any]] = []
    for ip_text, hit_count in targets:
        result: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "ip": ip_text,
            "hit_count": hit_count,
        }

        try:
            ip_obj = ipaddress.ip_address(ip_text)
        except ValueError:
            result.update({"status": "invalid_ip", "error": "Invalid IP address"})
            results.append(result)
            append_log(f"INVALID ip={ip_text} hits={hit_count}")
            continue

        result["ip_version"] = ip_obj.version
        result["is_private"] = ip_obj.is_private
        result["is_loopback"] = ip_obj.is_loopback
        result["is_reserved"] = ip_obj.is_reserved
        result["is_multicast"] = ip_obj.is_multicast
        result["is_global"] = ip_obj.is_global

        if not include_private and not ip_obj.is_global:
            result.update({
                "status": "skipped_non_global",
                "reason": "PROBE_INCLUDE_PRIVATE=0 and IP is not globally routable",
            })
            results.append(result)
            append_log(f"SKIP ip={ip_text} hits={hit_count} reason=non_global")
            continue

        result["status"] = "probed"

        if do_reverse_dns:
            result["reverse_dns"] = reverse_dns(ip_text)

        if do_connect:
            result["tcp_connect"] = [tcp_probe(ip_text, port, timeout) for port in ports]

        results.append(result)
        append_log(f"PROBED ip={ip_text} hits={hit_count}")

    return results


def write_report(results: Iterable[dict[str, Any]]) -> None:
    report_file = os.getenv("PROBE_REPORT_FILE", "").strip()
    if not report_file:
        raise ValueError("PROBE_REPORT_FILE is empty")
    directory = os.path.dirname(report_file)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as handle:
        for item in results:
            handle.write(json.dumps(item, sort_keys=True) + "\n")


def main() -> int:
    input_file = os.getenv("PROBE_INPUT_FILE", "").strip()
    top_n = _env_int("PROBE_TOP_N", 5)
    if top_n <= 0:
        append_log("No probe run because PROBE_TOP_N <= 0")
        return 0

    targets = load_targets(input_file, top_n)
    if not targets:
        append_log(f"No probe targets found in {input_file}")
        write_report([])
        return 0

    results = iter_results(targets)
    write_report(results)
    append_log(f"Completed probe run for {len(results)} target(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

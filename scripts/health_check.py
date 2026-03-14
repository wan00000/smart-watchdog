#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime

import requests


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def append_log(message: str) -> None:
    log_file = os.getenv("HEALTH_LOG_FILE", "").strip()
    if not log_file:
        return
    directory = os.path.dirname(log_file)
    if directory:
        os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def read_pause_time() -> int:
    raw = sys.stdin.readline().strip()
    if raw == "":
        return 1
    try:
        return int(raw)
    except ValueError:
        append_log(f"Invalid pause_time '{raw}', defaulting to 1")
        return 1


def maybe_alert(url: str, max_failures: int, last_error: str) -> None:
    if os.getenv("EMAIL_ALERTS_ENABLED", "0") != "1":
        return
    script_dir = os.path.dirname(os.path.abspath(__file__))
    alert_script = os.path.join(script_dir, "alert.py")
    message = (
        f"The endpoint {url} failed more than {max_failures} times in succession. "
        f"Last error: {last_error}"
    )
    subprocess.run(
        [sys.executable, alert_script, "ALERT - Watchdog health check failed", message],
        check=False,
        env=os.environ.copy(),
    )


def main() -> int:
    url = os.getenv("HEALTH_URL", "http://example.com").strip()
    timeout = _env_int("HEALTH_TIMEOUT", 5)
    max_failures = _env_int("HEALTH_MAX_FAILURES", 3)
    pause_time = read_pause_time()

    failures = 0
    last_error = "unknown"

    while True:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                append_log(f"SUCCESS status=200 url={url}")
                print("healthy")
                return 0

            failures += 1
            last_error = f"HTTP {response.status_code}"
            append_log(
                f"FAIL status={response.status_code} url={url} failures={failures}/{max_failures + 1}"
            )
        except requests.RequestException as exc:
            failures += 1
            last_error = str(exc)
            append_log(f"EXCEPTION url={url} error={exc} failures={failures}/{max_failures + 1}")

        if failures > max_failures:
            append_log(f"TERMINAL_FAILURE url={url} last_error={last_error}")
            maybe_alert(url, max_failures, last_error)
            print("error")
            return 1

        time.sleep(pause_time)


if __name__ == "__main__":
    raise SystemExit(main())

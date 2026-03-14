#!/usr/bin/env python3
from __future__ import annotations

import glob
import os
import time
from pathlib import Path
from typing import Iterable

from flask import Flask, Response, render_template_string
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Gauge, generate_latest

APP = Flask(__name__)
REPORT_DIR = Path(os.getenv("REPORT_DIR", Path(__file__).resolve().parents[1] / "reports"))
DASHBOARD_FILE = Path(os.getenv("DASHBOARD_FILE", REPORT_DIR / "dashboard.txt"))
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[1]))
METRICS_ROUTE = os.getenv("METRICS_ROUTE", "/metrics")

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart Infra Watchdog</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    
    :root {
      --bg-primary: #0a0f1a;
      --bg-secondary: #111827;
      --bg-card: #1a2332;
      --border: #2d3a4f;
      --text-primary: #f1f5f9;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      --accent: #22d3bb;
      --accent-dim: rgba(34, 211, 187, 0.15);
      --success: #22c55e;
      --warning: #eab308;
      --danger: #ef4444;
      --radius: 12px;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: var(--bg-primary);
      color: var(--text-primary);
      line-height: 1.6;
      min-height: 100vh;
    }
    
    .container {
      max-width: 1280px;
      margin: 0 auto;
      padding: 1.5rem;
    }
    
    @media (min-width: 768px) {
      .container { padding: 2rem; }
    }
    
    /* Header */
    header {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-bottom: 2rem;
      padding-bottom: 1.5rem;
      border-bottom: 1px solid var(--border);
    }
    
    @media (min-width: 640px) {
      header {
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
      }
    }
    
    .logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    
    .logo-icon {
      width: 40px;
      height: 40px;
      background: var(--accent-dim);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .logo-icon svg {
      width: 24px;
      height: 24px;
      color: var(--accent);
    }
    
    h1 {
      font-size: 1.5rem;
      font-weight: 600;
      letter-spacing: -0.025em;
    }
    
    .metrics-link {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 1rem;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text-secondary);
      text-decoration: none;
      font-size: 0.875rem;
      transition: all 0.2s;
    }
    
    .metrics-link:hover {
      background: var(--bg-secondary);
      border-color: var(--accent);
      color: var(--accent);
    }
    
    /* Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1rem;
      margin-bottom: 2rem;
    }
    
    @media (min-width: 640px) {
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
    }
    
    @media (min-width: 1024px) {
      .stats-grid { grid-template-columns: repeat(4, 1fr); }
    }
    
    .stat-card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem;
      transition: all 0.2s;
    }
    
    .stat-card:hover {
      border-color: var(--accent);
      transform: translateY(-2px);
    }
    
    .stat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 0.75rem;
    }
    
    .stat-label {
      font-size: 0.875rem;
      color: var(--text-secondary);
      font-weight: 500;
    }
    
    .stat-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .stat-icon svg {
      width: 18px;
      height: 18px;
    }
    
    .stat-icon.health { background: rgba(34, 197, 94, 0.15); color: var(--success); }
    .stat-icon.suspicious { background: rgba(234, 179, 8, 0.15); color: var(--warning); }
    .stat-icon.blocked { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
    .stat-icon.cleanup { background: var(--accent-dim); color: var(--accent); }
    
    .stat-value {
      font-size: 1.75rem;
      font-weight: 700;
      letter-spacing: -0.025em;
      margin-bottom: 0.25rem;
    }
    
    .stat-description {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    
    /* Section Titles */
    .section-title {
      font-size: 1.125rem;
      font-weight: 600;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    
    .section-title::before {
      content: '';
      width: 4px;
      height: 1.25rem;
      background: var(--accent);
      border-radius: 2px;
    }
    
    /* Table */
    .table-wrapper {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
      margin-bottom: 2rem;
    }
    
    .table-scroll {
      overflow-x: auto;
    }
    
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 400px;
    }
    
    th {
      background: var(--bg-secondary);
      padding: 0.875rem 1rem;
      text-align: left;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-secondary);
      border-bottom: 1px solid var(--border);
    }
    
    td {
      padding: 0.875rem 1rem;
      border-bottom: 1px solid var(--border);
      font-size: 0.875rem;
    }
    
    tr:last-child td { border-bottom: none; }
    
    tr:hover td { background: rgba(34, 211, 187, 0.05); }
    
    .ip-cell {
      font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
      color: var(--accent);
    }
    
    .hits-cell {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    
    .hits-bar {
      flex: 1;
      max-width: 120px;
      height: 6px;
      background: var(--bg-secondary);
      border-radius: 3px;
      overflow: hidden;
    }
    
    .hits-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--accent), #3b82f6);
      border-radius: 3px;
    }
    
    .hits-value {
      min-width: 48px;
      text-align: right;
      font-weight: 600;
    }
    
    .empty-state {
      text-align: center;
      padding: 2rem;
      color: var(--text-muted);
    }
    
    /* Terminal / Pre block */
    .terminal {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      overflow: hidden;
    }
    
    .terminal-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
    }
    
    .terminal-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
    
    .terminal-dot.red { background: #ef4444; }
    .terminal-dot.yellow { background: #eab308; }
    .terminal-dot.green { background: #22c55e; }
    
    .terminal-title {
      flex: 1;
      text-align: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    
    pre {
      padding: 1rem;
      margin: 0;
      font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
      font-size: 0.8125rem;
      line-height: 1.7;
      color: var(--text-secondary);
      overflow-x: auto;
      white-space: pre-wrap;
      word-wrap: break-word;
      max-height: 400px;
      overflow-y: auto;
    }
    
    /* Footer */
    footer {
      margin-top: 2rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--border);
      text-align: center;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo">
        <div class="logo-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
          </svg>
        </div>
        <h1>Smart Infra Watchdog</h1>
      </div>
      <a href="{{ metrics_route }}" class="metrics-link">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
        {{ metrics_route }}
      </a>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">Health Status</span>
          <div class="stat-icon health">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
        </div>
        <div class="stat-value" style="font-size: 1rem; word-break: break-word;">{{ health_status }}</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">Suspicious IPs</span>
          <div class="stat-icon suspicious">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
        </div>
        <div class="stat-value">{{ suspicious_count }}</div>
        <div class="stat-description">Detected in latest scan</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">Blocked IPs</span>
          <div class="stat-icon blocked">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
        </div>
        <div class="stat-value">{{ blocked_count }}</div>
        <div class="stat-description">Currently blocked</div>
      </div>
      
      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">Cleanup</span>
          <div class="stat-icon cleanup">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
        </div>
        <div class="stat-value">{{ cleanup_count }}</div>
        <div class="stat-description">Removed in last run</div>
      </div>
    </div>

    <h2 class="section-title">Top IPs by Request Count</h2>
    <div class="table-wrapper">
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>IP Address</th>
              <th>Hits</th>
            </tr>
          </thead>
          <tbody>
            {% for ip, hits in top_ips %}
            <tr>
              <td class="ip-cell">{{ ip }}</td>
              <td>
                <div class="hits-cell">
                  <div class="hits-bar">
                    <div class="hits-fill" style="width: {{ (hits / (top_ips[0][1] if top_ips else 1)) * 100 }}%;"></div>
                  </div>
                  <span class="hits-value">{{ hits }}</span>
                </div>
              </td>
            </tr>
            {% endfor %}
            {% if not top_ips %}
            <tr>
              <td colspan="2" class="empty-state">No report data available yet</td>
            </tr>
            {% endif %}
          </tbody>
        </table>
      </div>
    </div>

    <h2 class="section-title">Latest Dashboard Output</h2>
    <div class="terminal">
      <div class="terminal-header">
        <div class="terminal-dot red"></div>
        <div class="terminal-dot yellow"></div>
        <div class="terminal-dot green"></div>
        <span class="terminal-title">dashboard.txt</span>
      </div>
      <pre>{{ dashboard_text }}</pre>
    </div>
    
    <footer>
      Smart Infra Watchdog &middot; Infrastructure Monitoring
    </footer>
  </div>
</body>
</html>
"""


def latest_file(pattern: str) -> Path | None:
    matches = sorted(glob.glob(str(REPORT_DIR / pattern)), key=os.path.getmtime, reverse=True)
    return Path(matches[0]) if matches else None


def read_lines(path: Path | None) -> list[str]:
    if not path or not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def parse_ip_count_lines(lines: Iterable[str]) -> list[tuple[str, int]]:
    output: list[tuple[str, int]] = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            ip = parts[0]
            try:
                output.append((ip, int(parts[1])))
            except ValueError:
                continue
    return output


def latest_health_status() -> str:
    path = latest_file("health_*.log")
    lines = read_lines(path)
    if not lines:
        return "No health log yet"
    return lines[-1]


def cleanup_count() -> int:
    path = latest_file("cleanup_*.log")
    return len([line for line in read_lines(path) if line.startswith("/")])


def suspicious_count() -> int:
    path = latest_file("suspicious_ips_*.txt")
    return len(parse_ip_count_lines(read_lines(path)))


def blocked_count() -> int:
    path = latest_file("blocked_ips_*.txt")
    return len(parse_ip_count_lines(read_lines(path)))


def top_ips() -> list[tuple[str, int]]:
    path = latest_file("top_ips_*.txt")
    return parse_ip_count_lines(read_lines(path))


def dashboard_text() -> str:
    if not DASHBOARD_FILE.exists():
        return "No dashboard generated yet."
    return DASHBOARD_FILE.read_text(encoding="utf-8")


def build_metrics() -> bytes:
    registry = CollectorRegistry()
    gauge_health = Gauge("watchdog_health_up", "Health status from latest health log, 1 means healthy", registry=registry)
    gauge_cleanup = Gauge("watchdog_cleanup_removed_last_run", "Items removed by the most recent cleanup run", registry=registry)
    gauge_suspicious = Gauge("watchdog_suspicious_ip_count", "Suspicious IPs found in the latest report", registry=registry)
    gauge_blocked = Gauge("watchdog_blocked_ip_count", "Blocked IPs recorded in the latest block report", registry=registry)
    gauge_report_age = Gauge("watchdog_report_age_seconds", "Age in seconds of the latest report file", ["report_type"], registry=registry)
    gauge_top_ip_hits = Gauge("watchdog_top_ip_hits", "Hit counts for IPs in the latest top-IP report", ["ip"], registry=registry)

    health = latest_health_status().lower()
    gauge_health.set(1 if "success status=200" in health or health.endswith("healthy") else 0)
    gauge_cleanup.set(cleanup_count())
    gauge_suspicious.set(suspicious_count())
    gauge_blocked.set(blocked_count())

    for report_type, pattern in {
        "top_ips": "top_ips_*.txt",
        "suspicious": "suspicious_ips_*.txt",
        "blocked": "blocked_ips_*.txt",
        "cleanup": "cleanup_*.log",
        "health": "health_*.log",
    }.items():
        path = latest_file(pattern)
        age = time.time() - path.stat().st_mtime if path and path.exists() else -1
        gauge_report_age.labels(report_type=report_type).set(age)

    for ip, hits in top_ips():
        gauge_top_ip_hits.labels(ip=ip).set(hits)

    return generate_latest(registry)


@APP.route("/")
def index() -> str:
    return render_template_string(
        HTML_TEMPLATE,
        metrics_route=METRICS_ROUTE,
        health_status=latest_health_status(),
        suspicious_count=suspicious_count(),
        blocked_count=blocked_count(),
        cleanup_count=cleanup_count(),
        top_ips=top_ips(),
        dashboard_text=dashboard_text(),
    )


@APP.route(METRICS_ROUTE)
def metrics() -> Response:
    return Response(build_metrics(), mimetype=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    APP.run(host=os.getenv("FLASK_HOST", "127.0.0.1"), port=int(os.getenv("FLASK_PORT", "5000")), debug=False)

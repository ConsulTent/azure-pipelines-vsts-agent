#!/usr/bin/env python3
"""Rewrite the variants status table in README.md (in the current directory).

Runs after every workflow run: status updates for all distros; a distro's
build tag advances only when its own build leg succeeded, so failures keep
the last successful tag. Tag immutability on Docker Hub guarantees the
kept tag still resolves to that older build.

Always invoked from the repo root in CI; tests run it from a directory
containing a fixture README.md.
"""
import argparse
import datetime
import ipaddress
import json
import os
import re
import socket
import sys
import urllib.parse
import urllib.request
from pathlib import Path

GH_REPO = "ConsulTent/azure-pipelines-vsts-agent"
DH_REPO = "consultent/azure-pipelines-vsts-agent"
ALLOWED_HOST = "api.github.com"
DISTROS = ["22.04", "24.04", "26.04"]
START, END = "<!-- variants:start -->", "<!-- variants:end -->"


def fetch_conclusions(run_id):
    """Per-distro job conclusion from the run's jobs API ('needs' is aggregate-only)."""
    if not run_id.isdigit():
        sys.exit(f"run id must be numeric, got: {run_id!r}")
    url = urllib.parse.urlsplit(f"https://{ALLOWED_HOST}/repos/{GH_REPO}/actions/runs/{run_id}/jobs")
    if url.scheme != "https" or url.hostname != ALLOWED_HOST:
        sys.exit("unexpected request target")
    for info in socket.getaddrinfo(url.hostname, 443):
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            sys.exit(f"{ALLOWED_HOST} resolves to non-public address {ip}")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url.geturl(), headers=headers)
    with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as resp:
        jobs = json.load(resp)["jobs"]
    return {
        m.group(1): (j["conclusion"] or "unknown")
        for j in jobs
        if (m := re.search(r"\((\d+\.\d+)\)", j["name"]))
    }


def current_builds(readme):
    """tag + date per distro from the existing table - what failed legs keep."""
    found = {}
    for line in readme.splitlines():
        m = re.match(r"\| Ubuntu (\d+\.\d+).*\| `(\d+\.\d+-\d+-\d+)` \((\d{4}-\d{2}-\d{2})\) \|", line)
        if m:
            found[m.group(1)] = (m.group(2), m.group(3))
    return found


def build_table(status, builds, run_number, run_id, today):
    lines = [
        "| Distro | Status | Rolling tag | Current build | Size |",
        "| --- | --- | --- | --- | --- |",
    ]
    for d in DISTROS:
        conclusion = status.get(d, "unknown")
        if conclusion == "success":
            tag, day = f"{d}-{run_number}-{run_id}", today
            word, color = "passing", "brightgreen"
        else:
            tag, day = builds.get(d, ("—", ""))
            word, color = conclusion, "red"
        rolling = "`ubuntu-" + d + "`"
        if d == "26.04":
            rolling += " (`latest`)"
        lines.append(
            f"| Ubuntu {d} | ![status](https://img.shields.io/badge/{d}-{word}-{color})"
            f" | {rolling} | `{tag}`{f' ({day})' if day else ''}"
            f" | ![size](https://img.shields.io/docker/image-size/{DH_REPO}/ubuntu-{d}) |"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="GitHub run id (skipped when --status-map is given)")
    ap.add_argument("--number", default="0", help="run number (build-tag component)")
    ap.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).strftime("%F"))
    ap.add_argument("--status-map", help="override conclusions, e.g. '22.04=failing,24.04=success'")
    args = ap.parse_args()

    if args.status_map:
        status = dict(p.split("=") for p in args.status_map.split(","))
    else:
        if not args.run:
            ap.error("--run is required without --status-map")
        status = fetch_conclusions(args.run)

    source = Path("README.md")
    readme = source.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        sys.exit("markers not found in README.md")
    table = build_table(status, current_builds(readme), args.number, args.run or "0", args.date)
    updated = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        START + "\n" + table + "\n" + END,
        readme,
        flags=re.S,
    )
    source.write_text(updated, encoding="utf-8", newline="\n")
    print("statuses:", status)


if __name__ == "__main__":
    main()

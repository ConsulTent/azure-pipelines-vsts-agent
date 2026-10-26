#!/usr/bin/env python3
"""Rewrite the variants status and software-versions tables in README.md (cwd).

Runs after every workflow run: status updates for all variants; a variant's
build tag advances only when its own build leg succeeded, so failures keep
the last successful tag. Tool versions are probed from the PUBLISHED rolling
tags, which a failed run never re-pointed - so both tables always describe
the last successful builds. When the 26.04 leg succeeded and the versions
parse, the monthly version tag <year>-<month>-<az>-<pwsh> is printed as a
"version_tag:" line for the workflow to capture (the docker re-tag/push
happens in the workflow, not here).
"""
import argparse
import datetime
import ipaddress
import json
import os
import re
import socket
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

GH_REPO = "ConsulTent/azure-pipelines-vsts-agent"
DH_REPO = "consultent/azure-pipelines-vsts-agent"
ALLOWED_HOST = "api.github.com"
VERSION_RE = re.compile(r"^[0-9][0-9A-Za-z.+-]*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ROLLING_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
# (variant id, rolling tag, display name)
VARIANTS = [
    ("22.04", "ubuntu-22.04", "Ubuntu 22.04"),
    ("24.04", "ubuntu-24.04", "Ubuntu 24.04"),
    ("26.04", "ubuntu-26.04", "Ubuntu 26.04"),  # the `latest` variant
    ("dhi-debian13", "dhi-debian13", "Debian 13 (DHI hardened)"),
]
LATEST_VARIANT = "26.04"
ROLLING_ANNOTATIONS = {"26.04": " (`latest`)", "dhi-debian13": " (`dhi-latest`)"}
VSTART, VEND = "<!-- variants:start -->", "<!-- variants:end -->"
SSTART, SEND = "<!-- versions:start -->", "<!-- versions:end -->"
README = "README.md"
PROBE_SH = "az version 2>/dev/null | jq -r '.\"azure-cli\"' | tr -d '\\r'; pwsh --version 2>/dev/null | awk '{print $2}' | tr -d '\\r'"


def fetch_conclusions(run_id):
    """Per-variant job conclusion from the run's jobs API ('needs' is aggregate-only)."""
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
    known = {v[0] for v in VARIANTS}
    # job display name: "build-push (22.04, ubuntu:22.04, ubuntu-22.04[, latest])"
    return {
        m.group(1): (j["conclusion"] or "unknown")
        for j in jobs
        if (m := re.search(r"\(([\w.-]+)[,)]", j["name"])) and m.group(1) in known
    }


def current_builds(readme):
    """rolling tag -> (build tag, date), parsed from the existing table: what failed legs keep."""
    found = {}
    for line in readme.splitlines():
        m = re.match(
            r"\| [^|]+\|[^|]+\| `([^`]+)`[^|]*\| `([^`]+)` \((\d{4}-\d{2}-\d{2})\) \|", line
        )
        if m:
            found[m.group(1)] = (m.group(2), m.group(3))
    return found


def probe_versions(rolling):
    """(az cli, powershell) from the published rolling tag; (unknown, unknown) if unprovable."""
    if not ROLLING_RE.match(rolling):
        sys.exit(f"unparsable rolling tag: {rolling!r}")
    proc = subprocess.run(
        ["docker", "run", "--rm", f"{DH_REPO}:{rolling}", "bash", "-c", PROBE_SH],
        capture_output=True, text=True, timeout=600,
    )
    lines = [ln.strip() for ln in proc.stdout.strip().splitlines() if ln.strip()]
    if proc.returncode != 0 or len(lines) < 2:
        print(f"probe failed for {rolling}: rc={proc.returncode} stderr={proc.stderr.strip()[:300]!r}")
        return ("unknown", "unknown")
    return (lines[0], lines[1])


def build_variants_table(status, builds, run_number, run_id, today):
    lines = [
        "| Distro | Status | Rolling tag | Current build | Size |",
        "| --- | --- | --- | --- | --- |",
    ]
    for variant, rolling, display in VARIANTS:
        conclusion = status.get(variant, "unknown")
        if conclusion == "success":
            tag, day = f"{variant}-{run_number}-{run_id}", today
            word, color = "passing", "brightgreen"
        else:
            tag, day = builds.get(rolling, ("—", ""))
            word, color = conclusion, "red"
        rolling_cell = f"`{rolling}`" + ROLLING_ANNOTATIONS.get(variant, "")
        badge_name = variant.replace("-", "--") # shields: a literal dash is "--"
        lines.append(
            f"| {display} | ![status](https://img.shields.io/badge/{badge_name}-{word}-{color})"
            f" | {rolling_cell} | `{tag}`{f' ({day})' if day else ''}"
            f" | ![size](https://img.shields.io/docker/image-size/{DH_REPO}/{rolling}) |"
        )
    return "\n".join(lines)


def build_versions_table(versions, today):
    lines = [
        "| Variant | Azure CLI | PowerShell | As of |",
        "| --- | --- | --- | --- |",
    ]
    for _, rolling, display in VARIANTS:
        az, ps = versions.get(rolling, ("unknown", "unknown"))
        lines.append(f"| {display} | {az} | {ps} | {today} |")
    return "\n".join(lines)


def monthly_version_tag(az, ps, date_arg):
    """Validated <year>-<month>-<az>-<ps> tag for the latest variant, or '' when unparseable."""
    if not (VERSION_RE.match(az) and VERSION_RE.match(ps) and DATE_RE.match(date_arg)):
        return ""
    return f"{date_arg[:7]}-{az}-{ps}"


def replace_block(readme, start, end, table):
    if start not in readme or end not in readme:
        sys.exit(f"markers not found in {README}: {start}")
    return re.sub(
        re.escape(start) + r".*?" + re.escape(end),
        start + "\n" + table + "\n" + end,
        readme,
        flags=re.S,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="GitHub run id (skipped when --status-map is given)")
    ap.add_argument("--number", default="0", help="run number (build-tag component)")
    ap.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).strftime("%F"))
    ap.add_argument("--status-map", help="override conclusions, e.g. '22.04=failing,24.04=success'")
    ap.add_argument("--versions-map", help="override probes, e.g. 'ubuntu-22.04=2.91.0/7.6.8' (skips docker probes)")
    args = ap.parse_args()

    if args.status_map:
        status = dict(p.split("=") for p in args.status_map.split(","))
    else:
        if not args.run:
            ap.error("--run is required without --status-map")
        status = fetch_conclusions(args.run)

    if args.versions_map:
        versions = {
            p.split("=")[0]: tuple(p.split("=")[1].split("/"))
            for p in args.versions_map.split(",")
        }
    else:
        versions = {rolling: probe_versions(rolling) for _, rolling, _ in VARIANTS}
    version_tag = ""
    if status.get(LATEST_VARIANT) == "success":
        az, ps = versions.get("ubuntu-26.04", ("unknown", "unknown"))
        version_tag = monthly_version_tag(az, ps, args.date)

    source = Path(README)
    readme = source.read_text(encoding="utf-8")
    builds = current_builds(readme)
    readme = replace_block(
        readme, VSTART, VEND,
        build_variants_table(status, builds, args.number, args.run or "0", args.date),
    )
    readme = replace_block(
        readme, SSTART, SEND, build_versions_table(versions, args.date),
    )
    source.write_text(readme, encoding="utf-8", newline="\n")

    # the workflow captures this line into the step output (no env-provided paths are opened)
    print("statuses:", status)
    print("versions:", versions)
    print("version_tag:", version_tag or "(none)")


if __name__ == "__main__":
    main()

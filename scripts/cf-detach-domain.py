#!/usr/bin/env python3
"""Detach tv.cuicui.de from the old Pages project so the Worker can claim it.

Reads nothing sensitive; the token comes from the Actions secret.
Idempotent: if the domain is already gone, reports that and exits 0.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ["CF_TOKEN"]
ACCOUNT = os.environ["CF_ACCOUNT"]
PROJECT = os.environ.get("PAGES_PROJECT", "libretv")
HOST = os.environ.get("TARGET_HOST", "tv.cuicui.de")
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"


def call(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "hermes-agent",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:600]}


def summarize(d):
    out = []
    for e in d.get("errors") or []:
        out.append(f"ERR {e.get('code')}: {e.get('message')}")
    return out


def main():
    base = f"/accounts/{ACCOUNT}/pages/projects/{PROJECT}"

    st, d = call(base)
    print(f"[1] GET {base} -> http={st} success={d.get('success')}")
    for s in summarize(d):
        print("    " + s)
    if st != 200 or not d.get("success"):
        print("    cannot read project; aborting")
        return 0

    proj = d["result"]
    domains = proj.get("domains") or []
    print("    project subdomain:", proj.get("subdomain"))
    print("    project domains  :", domains)

    if HOST not in domains:
        print(f"[2] {HOST} is not attached to project '{PROJECT}' -- nothing to detach")
        return 0

    if DRY_RUN:
        print(f"[2] DRY_RUN=1 -> would DELETE {base}/domains/{HOST}")
        return 0

    print(f"[2] DELETE {base}/domains/{HOST}")
    st, d = call(f"{base}/domains/{HOST}", method="DELETE")
    print(f"    -> http={st} success={d.get('success')}")
    for s in summarize(d):
        print("    " + s)

    st, d = call(base)
    after = (d.get("result") or {}).get("domains") or []
    print(f"[3] verify -> domains now: {after}")
    print("    detached:", HOST not in after)
    return 0


if __name__ == "__main__":
    sys.exit(main())

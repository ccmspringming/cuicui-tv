#!/usr/bin/env python3
"""Read the ADMIN env var from the cfoo Pages project's production config.

Writes it to a file (mode 600) instead of stdout, so the value never lands in a
log or a chat transcript. Pass PRINT_LEN=1 to confirm the shape only.
"""
import json
import os
import pathlib
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ["CF_TOKEN"]
ACCOUNT = os.environ.get("CF_ACCOUNT", "")
PROJECT = os.environ.get("PROJECT", "cfoo")
OUT = pathlib.Path("/tmp/cfoo-admin.txt")


def call(path):
    req = urllib.request.Request(API + path, headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "hermes-agent",
    })
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:300]}


def main():
    st, d = call(f"/accounts/{ACCOUNT}/pages/projects/{PROJECT}")
    print(f"GET project -> http={st} success={d.get('success')}")
    for e in d.get("errors") or []:
        print(f"  ERR {e.get('code')}: {e.get('message')}")
    if st != 200 or not d.get("success"):
        print("cannot read project")
        return 1

    cfg = (d["result"].get("deployment_configs") or {}).get("production") or {}
    envs = cfg.get("env_vars") or {}
    print(f"env var keys: {list(envs.keys())}")

    admin = envs.get("ADMIN") or {}
    vtype = admin.get("type")
    value = admin.get("value")
    print(f"ADMIN type={vtype} present={value is not None}")

    if value:
        OUT.write_text(str(value), encoding="utf-8")
        OUT.chmod(0o600)
        print(f"written to {OUT} (mode 600), length={len(str(value))}")
        print(f"sha256 prefix check: first char class = "
              f"{'digit' if str(value)[:1].isdigit() else 'alpha'}")
    else:
        print("ADMIN has no readable value (secret_text is not exposed by the API)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

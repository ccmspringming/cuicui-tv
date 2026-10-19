#!/usr/bin/env python3
"""Inspect the `cfoo` Pages project: deployment source, recent deployments, and
what it actually serves. Read-only."""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ["CF_TOKEN"]
ACCOUNT = os.environ.get("CF_ACCOUNT", "")
PROJECT = os.environ.get("PROJECT", "cfoo")


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


def errs(d):
    return [f"ERR {e.get('code')}: {e.get('message')}" for e in (d.get("errors") or [])]


def main():
    print("=" * 70)
    print(f"project: {PROJECT}")
    st, d = call(f"/accounts/{ACCOUNT}/pages/projects/{PROJECT}")
    print(f"  http={st} success={d.get('success')}")
    p = d.get("result") or {}
    if p:
        for k in ("name", "subdomain", "domains", "created_on", "production_branch",
                  "build_config", "deployment_configs", "latest_deployment"):
            v = p.get(k)
            if k == "latest_deployment" and isinstance(v, dict):
                print(f"  latest_deployment: id={v.get('id')} created={v.get('created_on')} "
                      f"env={v.get('environment')} url={v.get('url')}")
            elif k == "deployment_configs" and isinstance(v, dict):
                prod = (v.get("production") or {})
                env_vars = (prod.get("env_vars") or {})
                print(f"  deployment_configs.production.env_vars: {list(env_vars.keys())}")
                for kk, vv in env_vars.items():
                    t = (vv or {}).get("type")
                    print(f"     - {kk} (type={t})")
            elif k == "build_config" and isinstance(v, dict):
                print(f"  build_config: {v}")
            else:
                print(f"  {k}: {v}")
    for e in errs(d):
        print("  " + e)

    print("=" * 70)
    print("deployments (most recent 5)")
    st, d = call(f"/accounts/{ACCOUNT}/pages/projects/{PROJECT}/deployments?per_page=5")
    print(f"  http={st} success={d.get('success')}")
    for dep in d.get("result") or []:
        print(f"  - id={dep.get('id')} created={dep.get('created_on')} "
              f"env={dep.get('environment')} trigger={dep.get('deployment_trigger',{}).get('type')}")
        stage = dep.get("latest_stage") or {}
        print(f"      stage={stage.get('name')}/{stage.get('status')} url={dep.get('url')}")
        src = dep.get("source") or {}
        if src:
            print(f"      source: {src.get('type')} {json.dumps(src.get('config') or {})[:120]}")
    for e in errs(d):
        print("  " + e)
    print("=" * 70)
    print("DONE")


if __name__ == "__main__":
    sys.exit(main())

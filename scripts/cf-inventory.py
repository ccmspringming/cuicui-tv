#!/usr/bin/env python3
"""Read-only inventory: which Cloudflare Workers / Pages projects exist, and
which hostnames they serve. Used to determine how edgetunnel was deployed.

Prints structure only -- never the token.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ["CF_TOKEN"]
ACCOUNT = os.environ.get("CF_ACCOUNT", "")


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
    print("A. Workers scripts")
    st, d = call(f"/accounts/{ACCOUNT}/workers/scripts")
    print(f"   http={st} success={d.get('success')}")
    for s in d.get("result") or []:
        print(f"   - {s.get('id')}  modified={s.get('modified_on','')[:10]}")
    for e in errs(d):
        print("   " + e)

    print("=" * 70)
    print("B. Workers subdomain / routes")
    for zname in ("cuicui.de",):
        st, d = call(f"/zones?name={zname}")
        zs = d.get("result") or []
        if not zs:
            print(f"   zone {zname} not found")
            continue
        zid = zs[0]["id"]
        st, d = call(f"/zones/{zid}/workers/routes")
        print(f"   routes http={st} success={d.get('success')}")
        for r in d.get("result") or []:
            print(f"   - pattern={r.get('pattern')} -> script={r.get('script')}")
        for e in errs(d):
            print("   " + e)

    print("=" * 70)
    print("C. Pages projects")
    st, d = call(f"/accounts/{ACCOUNT}/pages/projects")
    print(f"   http={st} success={d.get('success')}")
    for p in d.get("result") or []:
        print(f"   - {p['name']:20s} domains={p.get('domains')} created={p.get('created_on','')[:10]}")
        src = p.get("source") or {}
        if src:
            print(f"       source: type={src.get('type')} repo={src.get('config',{}).get('repo_name') if src.get('config') else None}")
        print(f"       subdomain={p.get('subdomain')}")
    for e in errs(d):
        print("   " + e)

    print("=" * 70)
    print("D. DNS records mentioning edgetunnel-ish hostnames")
    st, d = call("/zones?name=cuicui.de")
    zs = d.get("result") or []
    if zs:
        zid = zs[0]["id"]
        st, d = call(f"/zones/{zid}/dns_records?per_page=200")
        print(f"   http={st} success={d.get('success')}")
        for r in d.get("result") or []:
            if r["type"] in ("A", "AAAA", "CNAME"):
                print(f"   - {r['type']:6s} {r['name']:34s} -> {r['content'][:50]} proxied={r.get('proxied')}")
        for e in errs(d):
            print("   " + e)
    print("=" * 70)
    print("DONE")


if __name__ == "__main__":
    sys.exit(main())

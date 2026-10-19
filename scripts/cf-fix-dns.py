#!/usr/bin/env python3
"""Remove orphaned DNS records for a hostname so a Worker custom domain can claim it.

Solves Cloudflare error 100117. Only touches records whose name matches the
target host EXACTLY -- never wildcards, never other subdomains.
DRY_RUN=1 by default in the calling workflow; set DRY_RUN=0 to act.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ["CF_TOKEN"]
ZONE_NAME = os.environ.get("TARGET_ZONE", "cuicui.de")
HOST = os.environ.get("TARGET_HOST", "tv.cuicui.de")
DRY_RUN = os.environ.get("DRY_RUN", "1") == "1"


def call(path, method="GET"):
    req = urllib.request.Request(API + path, method=method, headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "hermes-agent",
    })
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read()
            return r.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:400]}


def errs(d):
    return [f"ERR {e.get('code')}: {e.get('message')}" for e in (d.get("errors") or [])]


def main():
    st, d = call(f"/zones?name={ZONE_NAME}")
    zones = d.get("result") or []
    if not zones:
        print(f"zone {ZONE_NAME} not found. token may lack zone:read")
        for s in errs(d):
            print("  " + s)
        return 1
    zid = zones[0]["id"]
    print(f"zone: {ZONE_NAME} (id={zid})")

    st, d = call(f"/zones/{zid}/dns_records?name={HOST}")
    print(f"[1] list DNS records for {HOST} -> http={st} success={d.get('success')}")
    for s in errs(d):
        print("    " + s)
    if st != 200 or not d.get("success"):
        print()
        print("VERDICT: cannot read DNS records -- token still lacks Zone:DNS:Read.")
        return 1

    recs = [r for r in (d.get("result") or []) if r["name"] == HOST]
    print(f"    exact-name records: {len(recs)}")
    for r in recs:
        print(f"      id={r['id']} type={r['type']} name={r['name']} "
              f"content={r['content']} proxied={r.get('proxied')}")

    if not recs:
        print()
        print("VERDICT: no records left -> Worker can claim the hostname. Re-run deploy.")
        return 0

    if DRY_RUN:
        print()
        print(f"DRY_RUN -> would DELETE {len(recs)} record(s) listed above")
        return 0

    print(f"[2] deleting {len(recs)} record(s)")
    ok = True
    for r in recs:
        st, d = call(f"/zones/{zid}/dns_records/{r['id']}", method="DELETE")
        status = "ok" if (st == 200 and d.get("success")) else "FAILED"
        print(f"    DELETE {r['id']} ({r['type']}) -> http={st} {status}")
        for s in errs(d):
            print("      " + s)
        if status == "FAILED":
            ok = False

    st, d = call(f"/zones/{zid}/dns_records?name={HOST}")
    left = [r for r in (d.get("result") or []) if r["name"] == HOST]
    print(f"[3] verify -> records remaining for {HOST}: {len(left)}")
    for r in left:
        print(f"      still there: id={r['id']} type={r['type']} content={r['content']}")
    print()
    print("VERDICT:", "clean -- re-run deploy to bind the custom domain"
          if not left else "records still present -- investigate")
    return 0 if (ok and not left) else 1


if __name__ == "__main__":
    sys.exit(main())

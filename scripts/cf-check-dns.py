#!/usr/bin/env python3
"""Check whether tv.cuicui.de still has DNS records left in the zone.

Read-only. If the token lacks DNS read permission this reports that clearly so
the operator knows the next step requires dashboard access.
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
            return e.code, {"raw": raw[:400]}


def main():
    st, d = call(f"/zones?name={ZONE_NAME}")
    zones = d.get("result") or []
    if not zones:
        print("zone not found; token may lack zone:read")
        return 1
    zid = zones[0]["id"]
    print("zone id:", zid)

    st, d = call(f"/zones/{zid}/dns_records?name={HOST}")
    print(f"GET /zones/<id>/dns_records?name={HOST} -> http={st} success={d.get('success')}")
    for e in d.get("errors") or []:
        print(f"  ERR {e.get('code')}: {e.get('message')}")
    recs = d.get("result") or []
    print("  records found:", len(recs))
    for r in recs:
        print(f"    id={r['id']} type={r['type']} name={r['name']} content={r['content']} proxied={r.get('proxied')}")

    if st == 403:
        print()
        print("VERDICT: token cannot read DNS -> operator must remove the record")
        print("         in the Cloudflare dashboard (DNS -> Records -> tv -> Delete).")
    elif recs:
        print()
        print("VERDICT: DNS record(s) still present -> they block the Worker custom domain (100117).")
    else:
        print()
        print("VERDICT: no DNS record for the hostname -> Worker can claim it; re-run deploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

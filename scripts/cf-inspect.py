#!/usr/bin/env python3
"""Read-only Cloudflare inspection for the tv.cuicui.de cutover.

Run inside GitHub Actions so it can use the repo's CLOUDFLARE_API_TOKEN secret
without the secret ever entering a chat transcript.
Prints only structural facts (projects, record types, hostnames) -- never the token.
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.cloudflare.com/client/v4"
TOKEN = os.environ["CF_TOKEN"]
ACCOUNT = os.environ.get("CF_ACCOUNT", "")
HOST = os.environ.get("TARGET_HOST", "tv.cuicui.de")
ZONE = os.environ.get("TARGET_ZONE", "cuicui.de")


def call(path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        API + path,
        data=data,
        method=method,
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
            "User-Agent": "hermes-agent",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:600]}


def errs(d):
    return [(e.get("code"), e.get("message")) for e in (d.get("errors") or [])]


def main():
    print("=" * 60)
    print("1. token verify")
    st, d = call("/user/tokens/verify")
    print("   http:", st, "| success:", d.get("success"),
          "| status:", (d.get("result") or {}).get("status"))
    for c, m in errs(d):
        print("   ERR", c, m)

    print("=" * 60)
    print("2. zones visible to this token")
    st, d = call("/zones?per_page=50")
    zones = d.get("result") or []
    print("   http:", st, "| success:", d.get("success"), "| count:", len(zones))
    for z in zones:
        print("   zone:", z["name"], "| id:", z["id"], "| status:", z.get("status"))
    for c, m in errs(d):
        print("   ERR", c, m)

    zone_id = next((z["id"] for z in zones if z["name"] == ZONE), "")
    if not zone_id:
        st, d = call("/zones?name=" + ZONE)
        r = d.get("result") or []
        zone_id = r[0]["id"] if r else ""
    print("   -> zone_id for", ZONE, "=", zone_id or "(NOT FOUND)")

    if zone_id:
        print("=" * 60)
        print("3. DNS records matching", HOST)
        st, d = call(f"/zones/{zone_id}/dns_records?name={HOST}")
        recs = d.get("result") or []
        print("   http:", st, "| success:", d.get("success"), "| count:", len(recs))
        for r in recs:
            print("   REC id=", r["id"], "| type=", r["type"], "| name=", r["name"],
                  "| content=", r["content"], "| proxied=", r.get("proxied"))
        for c, m in errs(d):
            print("   ERR", c, m)

        print("=" * 60)
        print("4. wildcard / subdomain records near the host")
        st, d = call(f"/zones/{zone_id}/dns_records?per_page=100")
        allr = d.get("result") or []
        for r in allr:
            if HOST in r["name"] or r["name"].startswith("*"):
                print("   REC id=", r["id"], "| type=", r["type"], "| name=", r["name"],
                      "| content=", r["content"][:60], "| proxied=", r.get("proxied"))
        print("   (total records in zone:", len(allr), ")")

    print("=" * 60)
    print("5. Pages projects and their custom domains")
    st, d = call(f"/accounts/{ACCOUNT}/pages/projects?per_page=50")
    projs = d.get("result") or []
    print("   http:", st, "| success:", d.get("success"), "| count:", len(projs))
    for p in projs:
        print("   project:", p["name"], "| subdomain:", p.get("subdomain"),
              "| domains:", p.get("domains"))
    for c, m in errs(d):
        print("   ERR", c, m)

    print("=" * 60)
    print("6. Workers scripts in account")
    st, d = call(f"/accounts/{ACCOUNT}/workers/scripts")
    scr = d.get("result") or []
    print("   http:", st, "| success:", d.get("success"), "| count:", len(scr))
    for s in scr:
        print("   worker:", s.get("id"))
    for c, m in errs(d):
        print("   ERR", c, m)

    print("=" * 60)
    print("DONE")


if __name__ == "__main__":
    sys.exit(main())

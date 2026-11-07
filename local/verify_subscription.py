#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无代理端到端体检：从订阅地址进去，把它引用的每条链接都实测一遍。
    python local/verify_subscription.py [订阅地址]
"""
import json
import ssl
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SUB = (sys.argv[1] if len(sys.argv) > 1 else
       "https://cdn.jsdelivr.net/gh/dsyzzzz/marco-list@52bd1612e066/tvbox.json")

ctx = ssl.create_default_context()
op = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.ProxyHandler({}),   # 显式禁用代理
)


def get(u, n=300):
    req = urllib.request.Request(u, headers={"User-Agent": "okhttp/3.15.3"})
    with op.open(req, timeout=15) as r:
        return r.status, r.read(n)


def check(label, u, expect=None):
    try:
        st, head = get(u)
        ok = (st == 200) and (expect is None or expect in head)
        print("  %s  %s  %s" % ("OK  " if ok else "WARN", str(st).ljust(4), label))
        return ok
    except Exception as e:
        print("  DEAD ----  %s  (%s: %s)" % (label, type(e).__name__, str(e)[:45]))
        return False


print("订阅地址:", SUB)
print("代理: 已显式禁用\n")
try:
    st, raw = get(SUB, 200000)
    sub = json.loads(raw.decode("utf-8"))
    print("订阅本体: %s  bytes=%d  sites=%d  lives=%d\n" % (
        st, len(raw), len(sub["sites"]), len(sub["lives"])))
except Exception as e:
    print("[fatal] 订阅本体读不到:", e)
    sys.exit(1)

print("[点播采集站]")
res = []
for s in sub["sites"]:
    res.append(check(s["name"], s["api"] + "?ac=list", b'"list"'))

print("\n[直播清单]")
for l in sub["lives"]:
    res.append(check(l["name"], l["url"], b"#EXTM3U"))

print("\n[EPG 节目单]")
for l in sub["lives"][:1]:
    res.append(check(l["epg"].split("/")[2], l["epg"], b"<?xml"))

print("\n[结论] %d/%d 条直连可用" % (sum(res), len(res)))

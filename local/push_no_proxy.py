#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
不走代理、不依赖 git，用 GitHub Contents REST API 推文件。

代理关了、git push 被重置、但 api.github.com 通过 Python TLS 栈可达时用这个。
内容用标准 base64 交给 PUT /contents，GitHub 会正确解码成文件。

用法：
    python push_no_proxy.py             # 推送默认 4 个文件
    python push_no_proxy.py --all       # 连同 local/ 下的脚本一起推
"""
import argparse
import base64
import json
import os
import ssl
import subprocess
import sys
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.github.com"
REPO = "dsyzzzz/marco-list"
BRANCH = "main"
CORE = ["tvbox.json", "live.m3u", "README.md", "SOURCES.md"]
EXTRA = ["local/serve.py", "local/direct_test.py", "local/mirror_test.py",
         "local/epg_test.py", "local/push_no_proxy.py"]

ctx = ssl.create_default_context()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.ProxyHandler({}),   # 显式禁用代理
)


def get_token():
    t = os.environ.get("GITHUB_TOKEN", "").strip()
    if t:
        return t
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True, text=True,
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


def call(method, path, tok, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(API + path, data=data, method=method)
    r.add_header("Authorization", "Bearer " + tok)
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("User-Agent", "marco-list-pusher")
    if data:
        r.add_header("Content-Type", "application/json")
    with opener.open(r, timeout=30) as resp:
        raw = resp.read()
        return resp.status, (json.loads(raw) if raw else {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="连 local/ 脚本一起推")
    args = ap.parse_args()

    tok = get_token()
    if not tok:
        print("[fatal] 没拿到 GitHub 凭据")
        return 1

    st, me = call("GET", "/user", tok)
    print("账号:", me.get("login"))

    files = CORE + (EXTRA if args.all else [])
    for name in files:
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            print("  skip (missing):", name)
            continue
        with open(p, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        sha = None
        try:
            st, cur = call("GET", "/repos/%s/contents/%s?ref=%s" % (REPO, name, BRANCH), tok)
            sha = cur.get("sha")
        except Exception:
            pass

        body = {
            "message": "直连版订阅 + 离线服务：%s" % name,
            "content": content,
            "branch": BRANCH,
        }
        if sha:
            body["sha"] = sha

        try:
            st, res = call("PUT", "/repos/%s/contents/%s" % (REPO, name), tok, body)
            print("  OK  %-32s %s" % (name, res.get("commit", {}).get("sha", "")[:8]))
        except Exception as e:
            print("  ERR %-32s %s: %s" % (name, type(e).__name__, str(e)[:100]))

    print("完成：https://github.com/%s" % REPO)
    return 0


if __name__ == "__main__":
    sys.exit(main())

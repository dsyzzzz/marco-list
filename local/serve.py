#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marco Movie 局域网订阅服务（零依赖，Python 3.7+）

把订阅从公网搬回家里局域网，彻底不依赖代理、不依赖 GitHub。

用法：
    python serve.py                  # 监听 0.0.0.0:8787
    python serve.py --port 9000      # 换端口

启动后终端会打印可导入的地址，形如：
    http://192.168.1.8:8787/tvbox.local.json

特点：
  * 订阅 JSON 在本机动态生成，直播清单直接读本地 live.m3u，全程不访问公网
  * 自动探测局域网 IP，不用手填
  * 带 CORS，放行 Marco Movie / TVBox 的跨域请求
  * 点播源仍是 5 个公共采集站（国内站，一般直连可达）
  * 可选：在 my-list/ 根目录放一份 epg.xml，节目单也走本地

适合放在：常开的旧电脑 / NAS / 软路由 / 树莓派 / 电视盒子（装个 Python）。
"""
import argparse
import http.server
import json
import os
import socket
import socketserver
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # my-list/
TVBOX = os.path.join(ROOT, "tvbox.json")
EPG = os.path.join(ROOT, "epg.xml")


def lan_ip():
    """UDP connect 不实际发包，只用来让系统选出通往外网的网卡地址。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("223.5.5.5", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def build_local_sub(host):
    with open(TVBOX, "r", encoding="utf-8") as f:
        sub = json.load(f)

    base = "http://" + host
    # 本地放了 epg.xml 就完全离线；没放就退回在线 EPG（节目单缺失不影响播放）
    epg_url = base + "/epg.xml" if os.path.exists(EPG) else "https://live.fanmingming.cn/e.xml"

    sub["_comment"] = "局域网本地版，由 serve.py 动态生成，无代理可用。点播源仍为公共采集站。"
    sub["lives"] = [
        {
            "name": "本地精选·4K/卫视/体育",
            "type": 0,
            "url": base + "/live.m3u",
            "playerType": 1,
            "ua": "okhttp/3.15.3",
            "epg": epg_url,
            "logo": "",
            "timeout": 20,
        }
    ]
    return json.dumps(sub, ensure_ascii=False, indent=2).encode("utf-8")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def guess_type(self, path):
        if path.endswith(".m3u") or path.endswith(".m3u8"):
            return "audio/x-mpegurl"
        if path.endswith(".json"):
            return "application/json; charset=utf-8"
        if path.endswith(".xml"):
            return "application/xml; charset=utf-8"
        return super().guess_type(path)

    def do_GET(self):
        if self.path.split("?")[0] == "/tvbox.local.json":
            body = build_local_sub(self.headers.get("Host", "127.0.0.1"))
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--host", default="0.0.0.0")
    args = ap.parse_args()

    ip = lan_ip()
    print("=" * 64)
    print("  Marco Movie 局域网订阅服务")
    print("=" * 64)
    print("  本机目录 : %s" % ROOT)
    print("  订阅地址 : http://%s:%d/tvbox.local.json   <<< 填这个" % (ip, args.port))
    print("  直播清单 : http://%s:%d/live.m3u" % (ip, args.port))
    print("  本机自测 : http://127.0.0.1:%d/tvbox.local.json" % args.port)
    print("-" * 64)
    print("  全程不依赖代理。同一 WiFi 下的电视 / 手机 / 盒子都能访问。")
    print("  Ctrl+C 停止。")
    print("=" * 64)
    sys.stdout.flush()

    with Server((args.host, args.port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止。")


if __name__ == "__main__":
    main()

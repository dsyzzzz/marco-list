import ssl
import urllib.request

ctx = ssl.create_default_context()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.ProxyHandler({}),  # 显式禁用代理
)

urls = [
    "https://www.baidu.com",
    "https://raw.githubusercontent.com/dsyzzzz/marco-list/main/tvbox.json",
    "https://raw.githubusercontent.com/dsyzzzz/marco-list/main/live.m3u",
    "https://github.com/dsyzzzz/marco-list",
    "https://cdn.jsdelivr.net/gh/dsyzzzz/marco-list@main/tvbox.json",
    "https://cj.lziapi.com/api.php/provide/vod/?ac=list",
    "https://cj.ffzyapi.com/api.php/provide/vod/?ac=list",
    "https://api.apibdzy.com/api.php/provide/vod/?ac=list",
    "https://api.wujinapi.me/api.php/provide/vod/?ac=list",
    "https://www.hongniuzy2.com/api.php/provide/vod/?ac=list",
    "https://live.fanmingming.cn/e.xml",
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "okhttp/3.15.3"})
        with opener.open(req, timeout=12) as r:
            data = r.read(200)
            print("OK   %s  len>=%d  <- %s" % (r.status, len(data), u))
    except Exception as e:
        print("ERR  %s: %s  <- %s" % (type(e).__name__, str(e)[:100], u))

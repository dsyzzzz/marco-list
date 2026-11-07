import ssl
import urllib.request

ctx = ssl.create_default_context()
op = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.ProxyHandler({}),
)

urls = [
    "https://cdn.jsdelivr.net/gh/dsyzzzz/marco-list@main/tvbox.json",
    "https://cdn.jsdelivr.net/gh/dsyzzzz/marco-list@main/live.m3u",
    "https://fastly.jsdelivr.net/gh/dsyzzzz/marco-list@main/tvbox.json",
    "https://gcore.jsdelivr.net/gh/dsyzzzz/marco-list@main/tvbox.json",
    "https://cdn.jsdelivr.net/gh/fanmingming/live@main/tv/m3u/index.m3u",
    "https://cdn.jsdelivr.net/gh/iptv-org/iptv@master/streams/cn.m3u",
    "https://epg.112114.xyz/e.xml",
    "https://live.fanmingming.com/e.xml",
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "okhttp/3.15.3"})
        with op.open(req, timeout=12) as r:
            d = r.read(300)
            print("OK   %s len=%d first=%r  <- %s" % (r.status, len(d), d[:60], u))
    except Exception as e:
        print("ERR  %s %s  <- %s" % (type(e).__name__, str(e)[:60], u))

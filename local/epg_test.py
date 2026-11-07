import ssl
import urllib.request

ctx = ssl.create_default_context()
op = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.ProxyHandler({}),
)

urls = [
    "https://epg.51zmt.top:8443/e.xml",
    "https://live.fanmingming.cn/e.xml",
    "https://cdn.jsdelivr.net/gh/fanmingming/live@main/e.xml",
    "https://cdn.jsdelivr.net/gh/EPG-Master/EPG@main/e.xml",
    "https://epg.iill.top/e.xml",
    "https://e.erw.cc/e.xml",
    "https://epg.v1.mk/e.xml",
    "https://cdn.jsdelivr.net/gh/DIYgod/epg@main/e.xml",
    "https://raw.githubusercontent.com/fanmingming/live/main/e.xml",
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "okhttp/3.15.3"})
        with op.open(req, timeout=10) as r:
            d = r.read(200)
            print("OK   %s len=%d first=%r  <- %s" % (r.status, len(d), d[:50], u))
    except Exception as e:
        print("ERR  %s %s  <- %s" % (type(e).__name__, str(e)[:60], u))

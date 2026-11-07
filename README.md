# marco-list · Marco Movie 自建订阅清单

> 一套零服务器的 TVBox / Marco Movie 订阅：5 个点播采集源 + 3 条直播源 + 一份带备份线路的精选直播清单。
> **全部走 jsdelivr CDN，代理开或关都能直连访问。**

## 订阅地址（导入 Marco Movie 用这个）

```
https://cdn.jsdelivr.net/gh/dsyzzzz/marco-list@da2db24ab177/tvbox.json
```

设置 → 订阅管理 / 配置地址 → 粘贴上面这条 → 确定 → 重启 App。

> 用固定 commit SHA 而不是 `@main`，是为了绕开 CDN 缓存：GitHub 上文件已更新，但 `@main` 可能还回旧版。
> 换源推送后把 SHA 换成新 commit 的前 12 位即可（`git log -1 --format=%h` 或看 GitHub 仓库首页）。
> 若想用跟随最新版，可以用 `https://cdn.jsdelivr.net/gh/dsyzzzz/marco-list@main/tvbox.json`，但 CDN 有缓存延迟。

## 直连可达性（2026-11-07 关代理实测）

| 目标 | 直连 |
|---|---|
| `raw.githubusercontent.com` / `github.com` | 超时，连不上 |
| `cdn.jsdelivr.net`（含 fastly / gcore 节点） | 200 通 |
| 5 个点播采集站 | 全部 200 通 |
| 直播流（国内 IP） | 通 |
| `live.fanmingming.cn` EPG | 超时 → 已换成 jsdelivr 镜像 `e.xml` |

## 文件

| 文件 | 说明 |
|---|---|
| `tvbox.json` | 订阅入口：5 个苹果CMS 点播接口 + fanmingming / iptv-org / 本仓库 live.m3u 三条直播，全部 jsdelivr |
| `live.m3u` | 自建直播清单：69 频道 / 98 条线路，央视18 + 4K6 + 卫视33 + 体育9 + 其他3，每频道 1–3 备份 |
| `check.mjs` | 体检脚本：`node check.mjs` 测死链并生成 `report.json` |
| `local/serve.py` | 完全离线的局域网订阅服务（连 jsdelivr 都不用），`python local/serve.py` |
| `local/push_no_proxy.py` | 代理关闭、git push 被重置时，用 GitHub API 直连推送 |
| `SOURCES.md` | 完整维护手册：源出处、换源步骤、故障排查、4K 与体育的现实说明 |

## 维护

```bash
node check.mjs                 # 体检全部线路
git add -A && git commit -m "换源" && git push   # 代理开着时
python local/push_no_proxy.py --all              # 代理关了 / push 被重置时
```

推送后：purge 缓存 + 换订阅地址里的 SHA：

```bash
curl https://purge.jsdelivr.net/gh/dsyzzzz/marco-list@main/tvbox.json
curl https://purge.jsdelivr.net/gh/dsyzzzz/marco-list@main/live.m3u
```

报 `all-dead` 的频道 → 去 `SOURCES.md` 里的上游仓库搜同名换新地址 → 追加一条同 `tvg-id` 的备线 → push。

## 完全离线方案

如果连 jsdelivr 都不想依赖，在常开的电脑 / NAS 上跑：

```bash
python local/serve.py
```

会打印形如 `http://192.168.1.8:8787/tvbox.local.json` 的地址，同一 WiFi 下的电视 / 手机直接填它。订阅和直播清单全在本机，点播源仍为国内公共采集站。

---

源清单整理 / 实测日期：2026-11-07。
仓库：https://github.com/dsyzzzz/marco-list

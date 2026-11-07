# marco-list · Marco Movie 自建订阅清单

> 一套零服务器的 TVBox / Marco Movie 订阅：5 个点播采集源 + 3 条直播源 + 一份带备份线路的精选直播清单。

## 订阅地址（导入 Marco Movie 用这个）

```
https://raw.githubusercontent.com/dsyzzzz/marco-list/main/tvbox.json
```

设置 → 订阅管理 / 配置地址 → 粘贴上面这条 → 确定 → 重启 App。

> 若 CDN 缓存未更新，在链接后加 `?v=2` 强制刷新。

## 文件

| 文件 | 说明 |
|---|---|
| `tvbox.json` | 订阅入口：5 个苹果CMS 点播接口 + fanmingming / iptv-org / 本仓库 live.m3u 三条直播 |
| `live.m3u` | 自建直播清单：69 频道 / 98 条线路，央视18 + 4K6 + 卫视33 + 体育9 + 其他3，每频道 1–3 备份 |
| `check.mjs` | 体检脚本：`node check.mjs` 测死链并生成 `report.json` |
| `SOURCES.md` | 完整维护手册：源出处、换源步骤、故障排查、4K 与体育的现实说明 |

## 维护

```bash
node check.mjs                 # 体检全部线路
node check.mjs --timeout=8000  # 网络慢时放宽超时
node check.mjs --json          # 只看机器可读汇总
```

报 `all-dead` 的频道 → 去 `SOURCES.md` 里的上游仓库搜同名换新地址 → 追加一条同 `tvg-id` 的备线 → push。

```bash
git add -A && git commit -m "换源" && git push
```

本机推送走 `http://127.0.0.1:7899` 代理，凭据由 Git Credential Manager 保管。

源清单整理 / 实测日期：2026-11-07。
仓库：https://github.com/dsyzzzz/marco-list

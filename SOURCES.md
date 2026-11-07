# Marco Movie 自建订阅清单 · 维护手册

整理日期：**2026-11-07**（下面的"实测"都是这个时间点从本机发起的真实请求结果）
适用：Marco Movie / TVBox / 影视仓 / EasyBox 等一切吃「TVBox JSON + m3u」的播放器。

---

## 一、这套方案省掉了什么

| | 上一版（自建服务器） | 这一版（清单 + 免费托管） |
|---|---|---|
| VPS | 要，￥30–80/月 | **不要** |
| 域名 / 证书 | 要 | **不要**（用 GitHub 的 https） |
| Docker / nginx / 网关 | 要，3–4 天 | **不要** |
| 你要维护的 | 4 个服务 | **2 个文本文件** |
| 月成本 | ￥50+ | **￥0** |

核心思路：**不自建内容，也不自建分发，只自建"选源结果"**。
你维护的是一份经过筛选、带备份线路、带画质标注的清单；分发交给 GitHub Raw / Gist（自带 CDN、自带 HTTPS、自带版本历史）。

---

## 二、文件清单

| 文件 | 作用 | 要不要改 |
|---|---|---|
| `live.m3u` | **直播清单**，69 个频道 / **98 条线路**（央视 18 + 4K 6 + 卫视 33 + 体育 9 + 其他 3，每频道 1–3 条备份） | 换源时改 |
| `tvbox.json` | **订阅入口**，把 5 个点播采集站 + 3 条直播源打包（raw 地址已写死） | 不用改 |
| `check.mjs` | 体检脚本，一键测出哪些线路死了 | 不用改 |
| `README.md` | 仓库首页说明 | — |
| `SOURCES.md` | 本文 | — |

---

## 三、已上线（2026-11-07 已完成）

仓库已建好并推送完毕，raw 三个文件实测均返回 `200`：

| 地址 | 内容 | 状态 |
|---|---|---|
| https://github.com/dsyzzzz/marco-list | 公开仓库 | 已创建 |
| `https://raw.githubusercontent.com/dsyzzzz/marco-list/main/tvbox.json` | 订阅入口 3076 B | 200 |
| `https://raw.githubusercontent.com/dsyzzzz/marco-list/main/live.m3u` | 直播清单 21169 B | 200 |
| `https://raw.githubusercontent.com/dsyzzzz/marco-list/main/README.md` | 说明 1346 B | 200 |

`tvbox.json` 里 `lives[2].url` 已写成你自己 `live.m3u` 的 raw 地址，不用再改。
另外两条（fanmingming、iptv-org）保留作兜底——它们是自动更新的活水，你自建清单哪天全挂了还能救回来。

### 现在只差一步：Marco Movie 导入

```
设置 → 订阅管理 / 配置地址 → 粘贴：
https://raw.githubusercontent.com/dsyzzzz/marco-list/main/tvbox.json
→ 确定 → 重启 App
```

导入后应该看到：点播 5 个站点、直播 3 个分组。搜一部正在更新的剧（如「现在就出发第四季」）验证点播；进「央视高清」「4K超高清」「体育」分组验证直播。

### 以后换源的完整动作

```
改本地 F:\dsh_workspace\my-list\ 里的文件
→ node check.mjs              （体检）
→ git add -A && git commit -m "换源" && git push
→ 播放器端下拉刷新订阅       （Raw CDN 缓存最长 5 分钟，急用加 ?v=2）
```

本机 git 已配置 `http/https.proxy = http://127.0.0.1:7899`，推送走这个代理；凭据由 Git Credential Manager 保管，不用反复输密码。

### 附：若想迁移到别的托管（当前用 A）

**A. GitHub 仓库（当前采用）** — 已就绪，无需操作。

**B. Gist**
```
https://gist.github.com/ 新建，文件名必须是 tvbox.json / live.m3u
点「Raw」得到 https://gist.githubusercontent.com/用户名/GIST_ID/raw/tvbox.json
```

**C. 完全不上传（本机/局域网）**
把 `live.m3u` 和 `tvbox.json` 放到手机上，用 Marco Movie 的「本地文件」导入；
或任意静态服务器（甚至 `python -m http.server 8000`）。

> 播放器只认「一个能直接 GET 到文本的 URL」。放哪都行，唯一要求是 Marco Movie 能访问到。

---

## 四、点播源清单（5 个，2026-11-07 逐个实测）

全部是苹果CMS V10 标准接口 `api.php/provide/vod/`，Marco Movie 的 `type:1` 直接吃。

| # | 名称 | 接口 | 库容 | 最新更新 | 特点 / 定位 |
|---|---|---|---|---|---|
| 1 | 量子·综合 | `https://cj.lziapi.com/api.php/provide/vod/` | **162,917** | 15:07（实时） | 字段最全（演员/评分/海报/简介），**有 MP4 直链 `vod_down_url`**，适合挑高码率 |
| 2 | 非凡·极速更新 | `https://cj.ffzyapi.com/api.php/provide/vod/` | **98,996** | 14:55 | 双线路 `feifan` + `ffm3u8`，新剧上新最快 |
| 3 | 博大·4K电影 | `https://api.apibdzy.com/api.php/provide/vod/` | 49,588 | 14:06 | 分类里有独立的 **「4K电影」(type_id=62)** 和体育赛事/足球/篮球 |
| 4 | 无尽·体育赛事 | `https://api.wujinapi.me/api.php/provide/vod/` | **124,513** | 13:51 | 唯一带**当天足球赛事录像**（英超/西甲/德甲/意甲/法甲逐场），另有 Netflix 专区和 64 个分类 |
| 5 | 红牛·剧集 | `https://www.hongniuzy2.com/api.php/provide/vod/` | 117,116 | 15:00 | 剧集/综艺全，`hnm3u8` 线路稳定 |

**实测样本**（说明这些不是死链）：
- 非凡 `?ac=detail&ids=100267` 返回完整播放串：`HD中字$https://vip.ffzy-play10.com/share/...` 与 `.../index.m3u8` 双份。
- 量子 `?wd=凡人修仙传` 返回 261 条，含 30 集 m3u8 + 30 集 MP4 直链（**MP4 直链通常是最高码率**）。
- 无尽列表里出现 `11月7日 26-27赛季西甲第12轮 塞维利亚VS阿拉维斯` 等 5 场当日赛事。

### 关于「4K」的大实话（很重要，别被名字骗）

我实际搜了 `wd=4K`：
- 量子：40 条命中，但绝大多数是「天书奇谭4K重置版」「花样年华4K修复版」这类**片名里带 4K**，播放线路标的是 `HD中字`，不是 2160P 原盘。
- 博大：有「4K电影」分类，但 `ac=videolist&t=62` 返回 **0 条**——分类是空壳。
- 非凡 / 红牛：无独立 4K 分类。

**结论**：公共采集站的"4K"≈"高清转码"，真 4K 原盘（蓝光 REMUX / 杜比视界）在这些源里基本不存在。
想确保 4K，实操路径是：
1. 在播放器里挑 `vod_play_from` 含 `m3u8` 且备注带 `HD/蓝光/原盘` 的线路；
2. 量子源挑 `vod_down_url` 的 **MP4 直链**，那是同一片子码率最高的一份；
3. 真 4K 片源请自备（NAS / 网盘 / PT），用 Marco Movie 的「本地/网盘」入口挂进去，别指望采集接口。

我把 5 个源全列上而不是只列一个，就是为了让你**同一部剧能跨源切线路**——这才是"自建清单"相对单个订阅真正的价值。

---

## 五、直播清单（live.m3u）

### 结构与约定

```
#EXTM3U x-tvg-url="EPG1,EPG2"        ← 双节目单，一个挂了自动用另一个
#EXTINF:-1 tvg-id="CCTV1" ... group-title="央视",CCTV-1 综合 [1080]
http://线路A
#EXTINF:-1 tvg-id="CCTV1" ... ,CCTV-1 综合 [1080·备]
http://线路B
```

- **同一个 `tvg-id` 重复出现 = 该频道的多条备份线路**，播放器会依次重试 → 这就是不自建服务器也能"稳"的关键。
- 显示名里的 `[1080]` `[720]` `[4K 2160p]` 是画质标注，方便你在电视上肉眼挑。
- `group-title` 分 6 组：央视 / 央视·体育 / 4K超高清 / 卫视 / 体育 / 其他。

### 覆盖情况

| 分组 | 数量 | 说明 |
|---|---|---|
| 央视 | CCTV-1～17 + 5+ 共 18 套 | 主线路用广东联通 GITV 高清（1080p，实测可直连），另配 1–3 条公网备线 |
| 4K超高清 | 8 条 | CCTV-4K、CCTV-8K、深圳卫视4K、河北卫视4K、湖南卫视4K、纯享4K 等，标注 2160p |
| 卫视 | 33 套 | 北京/东方/湖南/江苏/浙江/广东/深圳/山东/安徽/河南/湖北/江西/东南/四川/重庆/辽宁/黑龙江/吉林/天津/河北/广西/海南/云南/贵州/陕西/甘肃/青海/内蒙古/宁夏/新疆/西藏/三沙/延边 |
| 体育 | 8+ | CCTV-5/5+/16、五星体育、山东体育、江苏体育、篮球资讯、**百事通体育 1/2/3/5/7（1080p）** |
| 其他 | 3 | 凤凰中文/资讯、CGTN |

### 上游出处（换源时去这三个地方捞）

| 源 | 地址 | 特点 |
|---|---|---|
| fanmingming/live | `https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/index.m3u` | **央视卫视高清主力**，带台标 + EPG，中文名规范，长期维护 |
| iptv-org/iptv (cn) | `https://raw.githubusercontent.com/iptv-org/iptv/master/streams/cn.m3u` | 1000+ 条，4K/体育/地方台最全，但混杂失效与 Geo-blocked，需筛 |
| YueChan/Live | `https://raw.githubusercontent.com/YueChan/Live/main/IPTV.m3u` | 北京联通 IPTV 组播 `rtp://239.x`，**仅限运营商内网**，公网用不了，仅作参考 |
| EPG | `https://live.fanmingming.cn/e.xml`、`https://epg.51zmt.top:8443/e.xml` | 双节目单 |

### 体育这块的现实预期

- **CCTV-5 / 5+ / 16**：常驻、高清、可用 → 覆盖大部分主流赛事。
- **百事通体育 1/2/3/5/7**：1080p，但上游标注 `[Not 24/7]`，**赛事期间才有信号**，平时黑屏属正常。
- 无固定免费高画质「NBA / 英超专属频道」——这类源寿命以小时计。真要看，用**点播源里的当日赛事录像**（无尽源每天更新五大联赛逐场）反而更靠谱。
- 我在 `tvbox.json` 里保留了无尽源并命名「无尽·体育赛事」，就是为了补这块。

### 4K 直播的带宽要求

真 2160p 线路单路约 **15–25 Mbps**。电视盒子 + 百兆有线/5GHz WiFi 能跑；2.4GHz WiFi 或跨运营商会卡。卡的时候切同频道的 `[1080]` 备线即可，别死磕 4K。

---

## 六、日常维护（每周 5 分钟）

### 1. 体检

```bash
cd my-list
node check.mjs                 # 测全部线路
node check.mjs --timeout=8000  # 网络慢时放宽超时
node check.mjs --json          # 机器可读报告
```

输出示例：
```
[OK ] CCTV-1 综合 [1080]        312ms  http://58.248.112.205:8006/...
[OK ] CCTV-1 综合 [1080·备]     890ms  http://198.204.240.250:82/...
[DEAD] 湖南卫视 [4K 2160p·token]    token 过期 → 去 iptv-org cn.m3u 搜 HunanTV 换新的
...
健康 78 / 可疑 6 / 死亡 6   详见 report.json
```

`report.json` 会按 `tvg-id` 汇总，一眼看出**哪个频道一条活线都没有**（这才是需要补的），单条备线挂了不用管。

### 2. 换源

1. 去上表三个上游仓库搜频道名（如 `HunanTV`、`CCTV5Plus`）；
2. 复制新的 `.m3u8` 地址，替换 `live.m3u` 里对应行，或直接在原行下面**再加一条同 `tvg-id` 的备线**（推荐，不用删旧的）；
3. `node check.mjs` 确认新线活着；
4. 推 GitHub，播放器端下拉刷新订阅即可（Raw 有 CDN 缓存，最长 5 分钟生效）。

### 3. 加新频道 / 加新采集站

- 加频道：往 `live.m3u` 末尾按同样格式追加两行（`#EXTINF` + URL）。
- 加点播源：往 `tvbox.json` 的 `sites` 里加一个对象，`key`/`name`/`api` 三项必填，`type:1`。

### 4. 版本回滚

GitHub 仓库自带 commit 历史，改崩了直接 `Revert`。这是比自建服务器更省心的附加好处。

---

## 七、故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| 订阅导入后空白 | raw 链接不对 / 仓库私有 | 浏览器打开 raw 链接，应直接看到 JSON 文本 |
| 点播搜得到但播不了 | 采集站防盗链 or 线路过期 | 换同片的另一条 `vod_play_from` 线路；或换另一个 site 搜同名 |
| 直播全部转圈 | 手机/盒子网络到不了这些 IP（部分是运营商内网段） | 先试 `fanmingming` 那条 lives；`223.110.x` / `39.134.x` 段在部分运营商下不通属正常，靠别的备线兜 |
| EPG 不显示 | EPG 域名被墙/超时 | `x-tvg-url` 已配双份；也可换成 `https://epg.112114.xyz/e.xml` |
| 4K 频道卡顿 | 带宽不足 | 切同频道 `[1080]` 备线 |
| 改了文件播放器没变化 | CDN 缓存 | 等 5 分钟，或在 raw 链接后加 `?v=2` 强制刷新 |
| 某条线路白天好晚上卡 | 源站共享带宽 | 正常，靠多备线自动重试，不用管 |

---

## 八、扩展：想更进一步时的最小增量

按投入从低到高：

1. **￥0**：给 `check.mjs` 挂个 GitHub Actions 定时任务，每天自动体检并把 `report.json` 推回仓库 → 你手机上看报告就知道该换哪个源。
2. **￥0**：把这些源再套一层 Cloudflare Workers 做 Referer 转发（解决防盗链），仍不需要服务器。
3. **￥30/月**：真上一台小 VPS 跑上一版 `marco-tv/` 的网关，把这份清单喂给它做上游，才有健康探测自动剔除、HLS 切片缓存、HTTPS 自定义域名。

**现在这份清单本身就是第 3 步的输入**——哪天真要自建，不用重做选源工作。

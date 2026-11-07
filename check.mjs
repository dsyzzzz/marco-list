#!/usr/bin/env node
/**
 * 直播清单体检脚本
 * ---------------------------------------------------------------
 * 逐条 GET live.m3u 里的线路，只读取前几个字节判断是否是可用的
 * m3u8/播放列表，输出健康报告，并按 tvg-id 汇出「一条活线都没有」的频道。
 *
 * 纯 Node 内置模块，零依赖（Node >= 18）。
 *
 * 用法：
 *   node check.mjs                     # 测全部线路
 *   node check.mjs --timeout=8000      # 放宽单条超时（毫秒）
 *   node check.mjs --concurrency=32    # 并发数
 *   node check.mjs --json              # 只输出 report.json，不打印表格
 *   node check.mjs --file=./别的.m3u   # 指定其它清单
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));

/* ------------------------------ 参数 ------------------------------ */
const argv = process.argv.slice(2);
const arg = (k, d) => {
  const hit = argv.find((a) => a.startsWith(`--${k}=`));
  return hit ? hit.split('=').slice(1).join('=') : d;
};
const opt = {
  file: path.isAbsolute(arg('file', '')) ? arg('file', '') : path.join(HERE, arg('file', 'live.m3u')),
  timeout: Number(arg('timeout', 6000)),
  concurrency: Number(arg('concurrency', 24)),
  jsonOnly: argv.includes('--json'),
  ua: arg('ua', 'okhttp/3.15.3'),
};

/* ------------------------------ 工具 ------------------------------ */
const pad = (s, n) => String(s).padEnd(n, ' ').slice(0, n);
const C = {
  ok: (s) => `\x1b[32m${s}\x1b[0m`,
  warn: (s) => `\x1b[33m${s}\x1b[0m`,
  bad: (s) => `\x1b[31m${s}\x1b[0m`,
  dim: (s) => `\x1b[90m${s}\x1b[0m`,
};

async function pool(items, limit, fn) {
  const ret = new Array(items.length);
  let cursor = 0;
  const n = Math.max(1, Math.min(limit, items.length));
  await Promise.all(
    Array.from({ length: n }, async () => {
      while (cursor < items.length) {
        const i = cursor++;
        try {
          ret[i] = await fn(items[i], i);
        } catch (e) {
          ret[i] = { error: String(e?.message || e) };
        }
      }
    })
  );
  return ret;
}

/* ---------------------------- m3u 解析 ---------------------------- */
function parseM3u(text) {
  const out = [];
  let cur = null;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;

    if (line.startsWith('#EXTINF')) {
      const comma = line.lastIndexOf(',');
      const meta = comma >= 0 ? line.slice(0, comma) : line;
      const display = comma >= 0 ? line.slice(comma + 1).trim() : '';
      const attrs = {};
      const re = /([A-Za-z0-9_-]+)="([^"]*)"/g;
      let m;
      while ((m = re.exec(meta))) attrs[m[1].toLowerCase()] = m[2];
      cur = {
        name: display || attrs['tvg-name'] || '(无名)',
        group: attrs['group-title'] || '',
        id: attrs['tvg-id'] || '',
        url: '',
      };
      continue;
    }

    if (line.startsWith('#')) continue; // 跳过注释、x-tvg-url、#EXTVLCOPT

    if (cur) {
      cur.url = line;
      // 只测 http(s)；rtp/rtmp 组播留给播放器，本机多半测不了
      if (/^https?:\/\//i.test(cur.url)) out.push({ ...cur });
      cur = null;
    }
  }
  return out;
}

/* ----------------------------- 探测 ------------------------------- */
async function probe(entry) {
  const t0 = Date.now();
  try {
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), opt.timeout);
    const res = await fetch(entry.url, {
      headers: { 'User-Agent': opt.ua, Accept: '*/*' },
      redirect: 'follow',
      signal: ctl.signal,
    });
    const ms = Date.now() - t0;
    clearTimeout(timer);

    if (!res.ok) return { ...entry, status: 'dead', ms, detail: `HTTP ${res.status}` };

    // 只读前 4KB 判断内容，避免把整个视频流拉下来
    let head = '';
    const reader = res.body?.getReader();
    if (reader) {
      const { value } = await reader.read();
      if (value) head = new TextDecoder('utf-8', { fatal: false }).decode(value.slice(0, 4096));
      await reader.cancel().catch(() => {});
    }

    const isPlaylist = /#EXTM3U|#EXTINF|#EXT-X-|#EXT-X-STREAM-INF/.test(head);
    if (isPlaylist) {
      // master playlist 更好（多码率自适应）
      const master = /#EXT-X-STREAM-INF/.test(head);
      return { ...entry, status: 'ok', ms, detail: master ? 'master' : 'media', master };
    }

    // 有些源站对 Range/HEAD 返回空 body 但 200，标可疑而不是死
    if (!head.trim()) return { ...entry, status: 'warn', ms, detail: 'empty 200' };
    return { ...entry, status: 'warn', ms, detail: 'not a playlist' };
  } catch (e) {
    const msg = String(e?.message || e);
    const aborted = /abort|timeout/i.test(msg);
    return {
      ...entry,
      status: 'dead',
      ms: Date.now() - t0,
      detail: aborted ? 'timeout' : msg.slice(0, 60),
    };
  }
}

/* ----------------------------- 主流程 ----------------------------- */
async function main() {
  let text;
  try {
    text = await fs.readFile(opt.file, 'utf8');
  } catch (e) {
    console.error(`[fatal] 读不到清单：${opt.file}\n${e.message}`);
    process.exit(1);
  }

  const entries = parseM3u(text);
  if (!entries.length) {
    console.error('[fatal] 清单里没有可测的 http(s) 线路');
    process.exit(1);
  }

  if (!opt.jsonOnly) {
    console.log(C.dim(`\n清单: ${opt.file}`));
    console.log(C.dim(`线路: ${entries.length} 条  并发: ${opt.concurrency}  超时: ${opt.timeout}ms\n`));
  }

  const results = await pool(entries, opt.concurrency, probe);

  const ok = results.filter((r) => r.status === 'ok');
  const warn = results.filter((r) => r.status === 'warn');
  const dead = results.filter((r) => r.status === 'dead');

  if (!opt.jsonOnly) {
    for (const r of results) {
      const tag = r.status === 'ok' ? C.ok('[OK  ]') : r.status === 'warn' ? C.warn('[WARN]') : C.bad('[DEAD]');
      const ms = C.dim(String(r.ms ?? '-').padStart(6) + 'ms');
      const flag = r.master ? C.dim(' [master]') : '';
      console.log(`${tag} ${ms}  ${pad(r.name, 34)} ${C.dim(r.detail || '')}${flag}`);
      if (r.status === 'dead') console.log(`         ${C.dim(r.url)}`);
    }
  }

  // 按 tvg-id 汇总：找出一条活线都没有的频道
  const byId = new Map();
  for (const r of results) {
    const key = r.id || r.name;
    if (!byId.has(key)) byId.set(key, { id: r.id, name: r.name, group: r.group, lines: [] });
    byId.get(key).lines.push({ url: r.url, status: r.status, ms: r.ms, detail: r.detail });
  }
  const channels = [...byId.values()].map((c) => ({
    ...c,
    total: c.lines.length,
    alive: c.lines.filter((l) => l.status === 'ok').length,
    worst: c.lines.some((l) => l.status === 'ok') ? 'ok' : c.lines.some((l) => l.status === 'warn') ? 'degraded' : 'all-dead',
  }));
  const broken = channels.filter((c) => c.alive === 0);

  const report = {
    checkedAt: new Date().toISOString(),
    file: opt.file,
    summary: {
      lines: results.length,
      ok: ok.length,
      warn: warn.length,
      dead: dead.length,
      channels: channels.length,
      brokenChannels: broken.length,
    },
    brokenChannels: broken.map((c) => ({ id: c.id, name: c.name, group: c.group, worst: c.worst, lines: c.lines })),
    channels,
    lines: results,
  };

  await fs.writeFile(path.join(HERE, 'report.json'), JSON.stringify(report, null, 2), 'utf8');

  if (opt.jsonOnly) {
    console.log(JSON.stringify(report.summary, null, 2));
  } else {
    console.log('');
    console.log(`健康 ${C.ok(ok.length)} / 可疑 ${C.warn(warn.length)} / 死亡 ${C.bad(dead.length)}  ` +
      `频道 ${channels.length} 个，其中 ${C.bad(broken.length)} 个没有活线`);
    if (broken.length) {
      console.log(C.bad('\n无活线频道（需要补源）：'));
      for (const c of broken) console.log(`  - ${pad(c.name, 30)} ${C.dim(c.group)}`);
    }
    console.log(C.dim(`\n完整报告 -> ${path.join(HERE, 'report.json')}\n`));
  }
}

main().catch((e) => {
  console.error('[fatal]', e);
  process.exit(1);
});

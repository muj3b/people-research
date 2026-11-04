#!/usr/bin/env node
/**
 * people-research-native.js
 * Dependency-free (Node builtins only) native discovery probes for the
 * people-research skill. Text-only. No credentials. No paid APIs.
 *
 * Usage:
 *   node people-research-native.js --self-test            # offline fixture tests
 *   node people-research-native.js --smoke --query "text"  # bounded live probes:
 *       Bluesky, Hacker News, Reddit RSS, TikTok search
 *
 * Smoke output: JSON { query, sources: { <source>: { status, count, items[] } } }
 * Item schema: { source, id, url, date, title, query, status }
 * Source status: verified | partial | blocked | rate_limited
 */
'use strict';
const https = require('https');
const http = require('http');
const { URL } = require('url');

const UA = 'people-research-skill/1.0 (bounded smoke probe; contact: none)';

/* ---------------- HTTP helper ---------------- */
function fetchText(rawUrl, { headers = {}, timeoutMs = 15000, maxRedirects = 3 } = {}) {
  return new Promise((resolve, reject) => {
    let url;
    try { url = new URL(rawUrl); } catch (e) { return reject(new Error('bad url: ' + rawUrl)); }
    const lib = url.protocol === 'https:' ? https : http;
    const req = lib.request(url, {
      method: 'GET',
      headers: { 'User-Agent': UA, 'Accept': '*/*', ...headers },
    }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location && maxRedirects > 0) {
        res.resume();
        fetchText(new URL(res.headers.location, url).toString(), { headers, timeoutMs, maxRedirects: maxRedirects - 1 })
          .then(resolve, reject);
        return;
      }
      let data = '';
      res.on('data', (c) => {
        data += c;
        if (data.length > 5_000_000) { req.destroy(); reject(new Error('response too large')); }
      });
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', reject);
    req.setTimeout(timeoutMs, () => { req.destroy(new Error('timeout after ' + timeoutMs + 'ms')); });
    req.end();
  });
}

/* ---------------- Normalization / dedupe ---------------- */
const TRACKING_PARAMS = new Set([
  'utm_source','utm_medium','utm_campaign','utm_term','utm_content','utm_id',
  'si','spm','scid','fbclid','gclid','mc_cid','mc_eid','igshid',
]);
function canonicalUrl(raw) {
  const u = new URL(raw);
  u.hash = '';
  u.hostname = u.hostname.toLowerCase().replace(/^www\./, '');
  for (const p of [...u.searchParams.keys()]) {
    if (TRACKING_PARAMS.has(p.toLowerCase())) u.searchParams.delete(p);
  }
  u.searchParams.sort();
  let s = u.toString();
  if (s.endsWith('?')) s = s.slice(0, -1);
  return s;
}
function normalizeTitle(t) {
  return (t || '').toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, ' ').replace(/\s+/g, ' ').trim();
}
function dedupeItems(items) {
  const seenUrl = new Set(), seenTitle = new Set(), out = [];
  for (const it of items) {
    let cu = '';
    try { cu = canonicalUrl(it.url); } catch { cu = it.url; }
    const nt = normalizeTitle(it.title);
    if (seenUrl.has(cu)) continue;
    if (nt && seenTitle.has(nt)) continue;
    seenUrl.add(cu); if (nt) seenTitle.add(nt);
    out.push({ ...it, url: cu });
  }
  return out;
}
function classifyHttpError(err, status) {
  const msg = String((err && err.message) || status || '').toLowerCase();
  if (status === 429 || msg.includes('429') || msg.includes('rate')) return 'rate_limited';
  return 'blocked';
}

/* ---------------- Source probes ---------------- */
async function probeBluesky(query, limit = 10) {
  const paths = ['app.bsky.feed.searchPosts', 'app.bsky.feed.SEARCHPOSTS']; // fallback per skill note
  let lastErr = null;
  for (const p of paths) {
    try {
      const r = await fetchText(
        `https://public.api.bsky.app/xrpc/${p}?q=${encodeURIComponent(query)}&limit=${limit}`,
        { headers: { 'Accept': 'application/json' } }
      );
      if (r.status !== 200) { lastErr = new Error('http ' + r.status); continue; }
      const j = JSON.parse(r.body);
      const items = (j.posts || []).map((post) => {
        const rec = post.record || {};
        const uri = post.uri || '';
        const m = uri.match(/\/([^/]+)$/);
        return {
          source: 'bluesky', id: m ? m[1] : uri,
          url: `https://bsky.app/profile/${(post.author || {}).handle}/post/${m ? m[1] : ''}`,
          date: rec.createdAt || null,
          title: (rec.text || '').slice(0, 220),
          query, status: 'verified',
        };
      });
      return { status: 'verified', count: items.length, items, cursor: j.cursor || null, path: p };
    } catch (e) { lastErr = e; }
  }
  return { status: classifyHttpError(lastErr), count: 0, items: [], error: String(lastErr && lastErr.message) };
}

async function probeHN(query, limit = 10, page = 0) {
  try {
    const r = await fetchText(
      `https://hn.algolia.com/api/v1/search?query=${encodeURIComponent(query)}&tags=story&hitsPerPage=${limit}&page=${page}`,
      { headers: { 'Accept': 'application/json' } }
    );
    if (r.status !== 200) throw new Error('http ' + r.status);
    const j = JSON.parse(r.body);
    const items = (j.hits || []).map((h) => ({
      source: 'hackernews', id: String(h.objectID),
      url: `https://news.ycombinator.com/item?id=${h.objectID}`,
      date: h.created_at || null,
      title: h.title || '',
      query, status: 'verified',
      meta: { points: h.points, comments: h.num_comments, author: h.author },
    }));
    return { status: 'verified', count: items.length, items, page, nbPages: j.nbPages };
  } catch (e) {
    return { status: classifyHttpError(e), count: 0, items: [], error: String(e.message) };
  }
}

function parseRedditRss(xml, query) {
  const items = [];
  const entries = xml.match(/<entry>[\s\S]*?<\/entry>/g) || [];
  for (const e of entries) {
    const title = (e.match(/<title>([\s\S]*?)<\/title>/) || [])[1] || '';
    const link = (e.match(/<link[^>]*href="([^"]+)"/) || [])[1] || '';
    const updated = (e.match(/<updated>([^<]+)<\/updated>/) || [])[1] || null;
    const author = (e.match(/<author>\s*<name>([^<]*)<\/name>/) || [])[1] || '';
    const clean = title.replace(/<!\[CDATA\[|\]\]>/g, '').trim();
    if (!link) continue;
    items.push({
      source: 'reddit', id: link, url: link.replace(/&amp;/g, '&'),
      date: updated, title: clean, query, status: 'verified', meta: { author },
    });
  }
  return items;
}
async function probeReddit(query, limit = 10) {
  try {
    const r = await fetchText(
      `https://www.reddit.com/search.rss?q=${encodeURIComponent(query)}&sort=relevance&limit=${limit}`,
      { headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36', 'Accept': 'application/rss+xml' } }
    );
    if (r.status !== 200) throw new Error('http ' + r.status);
    const items = parseRedditRss(r.body, query).slice(0, limit);
    return { status: items.length ? 'verified' : 'partial', count: items.length, items };
  } catch (e) {
    return { status: classifyHttpError(e), count: 0, items: [], error: String(e.message) };
  }
}

async function probeTikTok(query, limit = 10) {
  try {
    const r = await fetchText(
      `https://www.tiktok.com/search?q=${encodeURIComponent(query)}`,
      { headers: { 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36', 'Accept': 'text/html' } }
    );
    if (r.status !== 200) throw new Error('http ' + r.status);
    const ids = new Set();
    for (const m of r.body.matchAll(/\/video\/(\d{10,})/g)) ids.add(m[1]);
    for (const m of r.body.matchAll(/"id"\s*:\s*"(\d{10,})"/g)) ids.add(m[1]);
    const items = [...ids].slice(0, limit).map((id) => ({
      source: 'tiktok', id, url: `https://www.tiktok.com/video/${id}`,
      date: null, title: '', query, status: 'partial',
    }));
    // IDs-only discovery; detail fetch (SSR subtitleInfos) is per-video follow-up.
    return { status: items.length ? 'partial' : 'blocked', count: items.length, items,
             note: 'anonymous search yields IDs only; use per-video page fetch for metadata/transcript' };
  } catch (e) {
    return { status: classifyHttpError(e), count: 0, items: [], error: String(e.message) };
  }
}

/* ---------------- CLI ---------------- */
function usage() {
  console.log('Usage:\n  node people-research-native.js --self-test\n  node people-research-native.js --smoke --query "text" [--limit N]');
  process.exit(2);
}

function runSelfTest() {
  const checks = [];
  const t = (name, fn) => { try { fn(); checks.push(['PASS', name]); } catch (e) { checks.push(['FAIL', name + ' :: ' + e.message]); } };
  const eq = (a, b) => { if (a !== b) throw new Error(`expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`); };

  t('canonicalUrl strips tracking + www + hash', () => {
    eq(canonicalUrl('https://WWW.Example.com/x?utm_source=a&b=2#frag'), 'https://example.com/x?b=2');
  });
  t('canonicalUrl sorts params', () => {
    eq(canonicalUrl('https://example.com/?z=1&a=2'), 'https://example.com/?a=2&z=1');
  });
  t('normalizeTitle', () => {
    eq(normalizeTitle('  Hello,   WORLD!  '), 'hello world');
  });
  t('dedupeItems drops dup urls and dup titles', () => {
    const items = [
      { url: 'https://example.com/a?utm_source=x', title: 'Same Title' },
      { url: 'https://example.com/a', title: 'Same Title' },
      { url: 'https://example.com/b', title: 'same title' },
      { url: 'https://example.com/c', title: 'Different' },
    ];
    const out = dedupeItems(items);
    eq(out.length, 2);
    eq(out[0].url, 'https://example.com/a');
  });
  t('parseRedditRss extracts entries', () => {
    const xml = `<feed><entry><title>Test &amp; Post</title><link href="https://www.reddit.com/r/x/comments/abc/test/"/><updated>2026-01-01T00:00:00Z</updated><author><name>u/bob</name></author></entry></feed>`;
    const out = parseRedditRss(xml, 'q');
    eq(out.length, 1); eq(out[0].meta.author, 'u/bob');
  });
  t('classifyHttpError', () => {
    eq(classifyHttpError(new Error('http 429')), 'rate_limited');
    eq(classifyHttpError(new Error('timeout')), 'blocked');
  });

  let fail = 0;
  for (const [s, n] of checks) { console.log(s + ' ' + n); if (s === 'FAIL') fail++; }
  console.log(fail === 0 ? `\nself-test: all ${checks.length} checks passed` : `\nself-test: ${fail}/${checks.length} FAILED`);
  process.exit(fail === 0 ? 0 : 1);
}

async function runSmoke(query, limit) {
  const sources = {};
  // Sequential to be gentle; each probe is bounded and independent.
  sources.bluesky = await probeBluesky(query, limit);
  sources.hackernews = await probeHN(query, limit);
  sources.reddit = await probeReddit(query, limit);
  sources.tiktok = await probeTikTok(query, limit);
  const all = dedupeItems(Object.values(sources).flatMap((s) => s.items || []));
  console.log(JSON.stringify({ query, limit, sources, deduped_total: all.length }, null, 2));
}

(function main() {
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) return runSelfTest();
  if (args.includes('--smoke')) {
    const qi = args.indexOf('--query');
    const li = args.indexOf('--limit');
    if (qi === -1 || !args[qi + 1]) usage();
    const limit = li !== -1 ? Math.max(1, Math.min(25, parseInt(args[li + 1], 10) || 10)) : 10;
    return runSmoke(args[qi + 1], limit).catch((e) => { console.error('smoke failed: ' + e.message); process.exit(1); });
  }
  usage();
})();

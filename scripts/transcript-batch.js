#!/usr/bin/env node
/**
 * transcript-batch.js
 * Bounded public-URL transcript retrieval for the people-research skill.
 * Dependency-free (Node builtins only). No credentials. No paid APIs.
 *
 * Submits public Instagram / TikTok / Facebook / YouTube URLs to the
 * verified fbtotranscript endpoint and normalizes results into the common
 * transcript schema. Concurrency is capped (default 3); retries with backoff.
 *
 * Usage:
 *   node transcript-batch.js --self-test
 *   node transcript-batch.js --urls "https://...,https://..." [--concurrency 3]
 *
 * Output: JSON array of { url, platform, status, text, segments, srt, vtt,
 *           provenance: { service, method, fetched_at }, error? }
 * Status: ok | no_transcript | error | rejected
 *
 * Env overrides (for endpoint drift):
 *   FBTT_ENDPOINT  default https://fbtotranscript.com/api/transcript
 *   FBTT_FIELD     default "url" (multipart form field carrying the video URL)
 *
 * NOTE: submit only public URLs the user approved. Never private,
 * follower-only, or sensitive content. The exact upstream request/response
 * shape is availability-dependent; failures are reported per URL, never fatal.
 */
'use strict';
const https = require('https');
const { URL } = require('url');

const ENDPOINT = process.env.FBTT_ENDPOINT || 'https://fbtotranscript.com/api/transcript';
const FIELD = process.env.FBTT_FIELD || 'url';
const DEFAULT_CONCURRENCY = 3;
const REQUEST_TIMEOUT_MS = 120000;

/* ---------------- platform inference + canonicalization ---------------- */
function inferPlatform(raw) {
  let host;
  try { host = new URL(raw).hostname.toLowerCase(); } catch { return null; }
  host = host.replace(/^www\.|^m\.|^vm\./, '');
  if (host.includes('instagram.com')) return 'instagram';
  if (host.includes('tiktok.com')) return 'tiktok';
  if (host.includes('facebook.com') || host === 'fb.watch') return 'facebook';
  if (host.includes('youtube.com') || host === 'youtu.be') return 'youtube';
  return null;
}
function canonicalVideoUrl(raw) {
  const u = new URL(raw);
  u.hash = '';
  const plat = inferPlatform(raw);
  if (plat === 'youtube') {
    // keep only the video id
    const id = u.hostname.includes('youtu.be') ? u.pathname.slice(1)
      : u.searchParams.get('v');
    if (id) return `https://www.youtube.com/watch?v=${id}`;
  }
  if (plat === 'tiktok') {
    const m = u.pathname.match(/\/video\/(\d+)/);
    if (m) return `https://www.tiktok.com/video/${m[1]}`;
  }
  for (const p of [...u.searchParams.keys()]) {
    if (/^utm_|^si$|^spm$|^fbclid$|^igshid$/i.test(p)) u.searchParams.delete(p);
  }
  u.searchParams.sort();
  let s = u.toString();
  if (s.endsWith('?')) s = s.slice(0, -1);
  return s;
}
function dedupeUrls(urls) {
  const seen = new Set(), out = [];
  for (const raw of urls) {
    const c = canonicalVideoUrl(raw);
    if (!seen.has(c)) { seen.add(c); out.push({ raw, canonical: c, platform: inferPlatform(raw) }); }
  }
  return out;
}

/* ---------------- multipart POST ---------------- */
function postMultipart(endpoint, fieldName, videoUrl) {
  return new Promise((resolve, reject) => {
    const boundary = '----peopleResearch' + Date.now().toString(36);
    const body =
      `--${boundary}\r\nContent-Disposition: form-data; name="${fieldName}"\r\n\r\n${videoUrl}\r\n` +
      `--${boundary}--\r\n`;
    const u = new URL(endpoint);
    const req = https.request(u, {
      method: 'POST',
      headers: {
        'Content-Type': `multipart/form-data; boundary=${boundary}`,
        'Content-Length': Buffer.byteLength(body),
        'User-Agent': 'people-research-skill/1.0 (transcript batch)',
        'Accept': 'application/json',
      },
    }, (res) => {
      let data = '';
      res.on('data', (c) => { data += c; if (data.length > 10_000_000) { req.destroy(); reject(new Error('response too large')); } });
      res.on('end', () => resolve({ status: res.statusCode, body: data }));
    });
    req.on('error', reject);
    req.setTimeout(REQUEST_TIMEOUT_MS, () => req.destroy(new Error('timeout after ' + REQUEST_TIMEOUT_MS + 'ms')));
    req.write(body);
    req.end();
  });
}

/* ---------------- tolerant response shaping ---------------- */
function findKey(obj, names) {
  if (!obj || typeof obj !== 'object') return undefined;
  for (const k of Object.keys(obj)) {
    if (names.includes(k.toLowerCase())) return obj[k];
  }
  for (const k of Object.keys(obj)) {
    const v = findKey(obj[k], names);
    if (v !== undefined) return v;
  }
  return undefined;
}
function toSegments(raw) {
  if (!Array.isArray(raw)) return [];
  return raw.map((s) => ({
    start: s.start ?? s.begin ?? s.from ?? null,
    end: s.end ?? s.to ?? null,
    text: String(s.text ?? s.caption ?? s.content ?? ''),
  })).filter((s) => s.text);
}
function shapeResult(target, httpRes) {
  const base = {
    url: target.canonical, platform: target.platform, status: 'error',
    text: '', segments: [], srt: '', vtt: '',
    provenance: { service: 'fbtotranscript', method: 'api/transcript', fetched_at: new Date().toISOString(), endpoint: ENDPOINT },
  };
  if (httpRes.status < 200 || httpRes.status >= 300) {
    base.error = `upstream http ${httpRes.status}: ${httpRes.body.slice(0, 200)}`;
    return base;
  }
  let j;
  try { j = JSON.parse(httpRes.body); }
  catch { base.error = 'upstream returned non-JSON'; base.raw = httpRes.body.slice(0, 500); return base; }
  const errFlag = findKey(j, ['error', 'errormessage', 'message']);
  if (errFlag && /fail|error|invalid|not found|unsupported/i.test(String(errFlag))) {
    base.error = String(errFlag).slice(0, 300);
    return base;
  }
  const segments = toSegments(findKey(j, ['segments', 'subtitles', 'captions', 'lines']) || []);
  const text = findKey(j, ['transcript', 'text', 'fulltext', 'full_text']);
  base.text = typeof text === 'string' ? text : segments.map((s) => s.text).join(' ');
  base.segments = segments;
  base.srt = String(findKey(j, ['srt']) || '');
  base.vtt = String(findKey(j, ['vtt']) || '');
  base.status = base.text.trim() ? 'ok' : 'no_transcript';
  return base;
}

async function processOne(target, attempt = 0) {
  if (!target.platform) {
    return { url: target.canonical, platform: null, status: 'rejected',
             error: 'unsupported platform (need instagram/tiktok/facebook/youtube public URL)',
             provenance: { service: 'fbtotranscript', method: 'none' } };
  }
  try {
    const httpRes = await postMultipart(ENDPOINT, FIELD, target.canonical);
    if (httpRes.status >= 500 && attempt < 2) {
      await new Promise((r) => setTimeout(r, 2000 * (attempt + 1)));
      return processOne(target, attempt + 1);
    }
    return shapeResult(target, httpRes);
  } catch (e) {
    if (attempt < 2 && /timeout|ECONNRESET|ENOTFOUND/i.test(e.message)) {
      await new Promise((r) => setTimeout(r, 2000 * (attempt + 1)));
      return processOne(target, attempt + 1);
    }
    return { url: target.canonical, platform: target.platform, status: 'error',
             error: String(e.message).slice(0, 300),
             provenance: { service: 'fbtotranscript', method: 'api/transcript', fetched_at: new Date().toISOString() } };
  }
}
async function runBatch(targets, concurrency) {
  const results = new Array(targets.length);
  let next = 0;
  async function worker() {
    while (next < targets.length) {
      const i = next++;
      results[i] = await processOne(targets[i]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, targets.length) }, worker));
  return results;
}

/* ---------------- CLI ---------------- */
function usage() {
  console.log('Usage:\n  node transcript-batch.js --self-test\n  node transcript-batch.js --urls "https://...,https://..." [--concurrency 3]');
  process.exit(2);
}
function runSelfTest() {
  const checks = [];
  const t = (name, fn) => { try { fn(); checks.push(['PASS', name]); } catch (e) { checks.push(['FAIL', name + ' :: ' + e.message]); } };
  const eq = (a, b) => { if (a !== b) throw new Error(`expected ${JSON.stringify(b)}, got ${JSON.stringify(a)}`); };

  t('inferPlatform', () => {
    eq(inferPlatform('https://www.instagram.com/p/abc/'), 'instagram');
    eq(inferPlatform('https://vm.tiktok.com/xyz/'), 'tiktok');
    eq(inferPlatform('https://www.tiktok.com/@u/video/1234567890123456789'), 'tiktok');
    eq(inferPlatform('https://www.facebook.com/watch/?v=123'), 'facebook');
    eq(inferPlatform('https://youtu.be/dQw4w9WgXcQ'), 'youtube');
    eq(inferPlatform('https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10'), 'youtube');
    eq(inferPlatform('https://example.com/x'), null);
  });
  t('canonicalVideoUrl normalizes youtube + tiktok', () => {
    eq(canonicalVideoUrl('https://youtu.be/dQw4w9WgXcQ?si=abc'), 'https://www.youtube.com/watch?v=dQw4w9WgXcQ');
    eq(canonicalVideoUrl('https://www.tiktok.com/@u/video/1234567890123456789?lang=en'), 'https://www.tiktok.com/video/1234567890123456789');
  });
  t('dedupeUrls', () => {
    const out = dedupeUrls(['https://youtu.be/dQw4w9WgXcQ?si=1', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'https://example.com/x']);
    eq(out.length, 2);
    eq(out[1].platform, null);
  });
  t('shapeResult parses transcript json', () => {
    const r = shapeResult(
      { canonical: 'https://x', platform: 'tiktok' },
      { status: 200, body: JSON.stringify({ transcript: 'hello world', segments: [{ start: 0, end: 1.5, text: 'hello world' }] }) }
    );
    eq(r.status, 'ok'); eq(r.text, 'hello world'); eq(r.segments.length, 1);
  });
  t('shapeResult flags upstream error', () => {
    const r = shapeResult({ canonical: 'https://x', platform: 'tiktok' }, { status: 200, body: JSON.stringify({ error: 'video not found' }) });
    eq(r.status, 'error');
  });
  t('shapeResult handles http 500', () => {
    const r = shapeResult({ canonical: 'https://x', platform: 'tiktok' }, { status: 500, body: 'boom' });
    eq(r.status, 'error');
  });

  let fail = 0;
  for (const [s, n] of checks) { console.log(s + ' ' + n); if (s === 'FAIL') fail++; }
  console.log(fail === 0 ? `\nself-test: all ${checks.length} checks passed` : `\nself-test: ${fail}/${checks.length} FAILED`);
  process.exit(fail === 0 ? 0 : 1);
}

(function main() {
  const args = process.argv.slice(2);
  if (args.includes('--self-test')) return runSelfTest();
  const ui = args.indexOf('--urls');
  if (ui === -1 || !args[ui + 1]) usage();
  const ci = args.indexOf('--concurrency');
  const concurrency = ci !== -1 ? Math.max(1, Math.min(5, parseInt(args[ci + 1], 10) || DEFAULT_CONCURRENCY)) : DEFAULT_CONCURRENCY;
  const rawUrls = args[ui + 1].split(',').map((s) => s.trim()).filter(Boolean);
  if (!rawUrls.length) { console.error('no urls given'); process.exit(2); }
  const targets = dedupeUrls(rawUrls);
  runBatch(targets, concurrency)
    .then((res) => console.log(JSON.stringify(res, null, 2)))
    .catch((e) => { console.error('batch failed: ' + e.message); process.exit(1); });
})();

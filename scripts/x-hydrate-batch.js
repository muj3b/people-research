#!/usr/bin/env node
/**
 * x-hydrate-batch.js
 * Bounded batch hydration of known X (Twitter) post URLs via the public
 * oEmbed endpoint. No login, no API key. Dependency-free (Node builtins).
 *
 * This hydrates KNOWN tweet URLs (discovered via web search) into full text +
 * author + date. There is no free anonymous X search; discovery is separate.
 *
 * Verified 2026-09-28: 7/7 real tweets HTTP 200, no rate limits at
 * concurrency 5, nonexistent tweet -> clean HTTP 404.
 *
 * Usage:
 *   node x-hydrate-batch.js --urls "https://x.com/a/status/1,https://x.com/b/status/2"
 *   node x-hydrate-batch.js --file urls.txt [--concurrency 3]
 *
 * Output: JSON array of { url, platform, status, text, author_name,
 *           author_handle, author_url, posted_at, provenance, error? }
 * Status: ok | not_found | error
 */
'use strict';
const https = require('https');
const fs = require('fs');

const OEMBED = 'https://publish.x.com/oembed?url=';
const DEFAULT_CONCURRENCY = 3;
const TIMEOUT_MS = 20000;

function get(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      let body = '';
      res.on('data', (c) => { body += c; if (body.length > 200000) req.destroy(); });
      res.on('end', () => resolve({ statusCode: res.statusCode, body }));
    });
    req.on('error', reject);
    req.setTimeout(TIMEOUT_MS, () => { req.destroy(new Error('timeout')); });
  });
}

// Tweet text lives in the <p> inside the oEmbed blockquote html.
function extractTweetText(html) {
  const m = html.match(/<blockquote[^>]*>([\s\S]*?)<\/blockquote>/i);
  if (!m) return '';
  const inner = m[1];
  const p = inner.match(/<p[^>]*>([\s\S]*?)<\/p>/i);
  let text = p ? p[1] : inner;
  text = text
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<a[^>]*>([^<]*)<\/a>/gi, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'");
  // strip the trailing "— Author (@handle) Date" attribution line
  text = text.replace(/\s*—\s*[^\n]*$/, '').trim();
  return text;
}

function extractHandle(authorUrl) {
  const m = (authorUrl || '').match(/(?:x|twitter)\.com\/([A-Za-z0-9_]+)/);
  return m ? '@' + m[1] : '';
}

function extractDate(html) {
  const m = html.match(/>(\w+ \d{1,2}, \d{4})<\/a>\s*<\/blockquote>/);
  return m ? m[1] : '';
}

async function hydrateOne(rawUrl) {
  const url = rawUrl.trim();
  const base = {
    url, platform: 'x', status: 'error', text: '',
    provenance: {
      service: 'x-oembed', method: 'publish.x.com/oembed',
      fetched_at: new Date().toISOString(),
    },
  };
  try {
    const { statusCode, body } = await get(OEMBED + encodeURIComponent(url));
    if (statusCode === 404) return { ...base, status: 'not_found', error: 'tweet not found / deleted / private' };
    if (statusCode !== 200) return { ...base, error: `oembed http ${statusCode}` };
    const data = JSON.parse(body);
    return {
      ...base,
      status: 'ok',
      text: extractTweetText(data.html || ''),
      author_name: data.author_name || '',
      author_handle: extractHandle(data.author_url),
      author_url: data.author_url || '',
      posted_at: extractDate(data.html || ''),
    };
  } catch (e) {
    return { ...base, error: String(e.message || e).slice(0, 200) };
  }
}

async function run(urls, concurrency) {
  const out = new Array(urls.length);
  let i = 0;
  async function worker() {
    while (i < urls.length) {
      const idx = i++;
      out[idx] = await hydrateOne(urls[idx]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, urls.length) }, worker));
  return out;
}

function main() {
  const args = process.argv.slice(2);
  let urls = [], concurrency = DEFAULT_CONCURRENCY;
  for (let k = 0; k < args.length; k++) {
    if (args[k] === '--urls' && args[k + 1]) urls = args[++k].split(',').map(s => s.trim()).filter(Boolean);
    else if (args[k] === '--file' && args[k + 1]) {
      urls = fs.readFileSync(args[++k], 'utf8').split('\n').map(s => s.trim()).filter(Boolean);
    }
    else if (args[k] === '--concurrency' && args[k + 1]) concurrency = Math.max(1, parseInt(args[++k], 10) || 3);
  }
  if (!urls.length) { console.error('usage: --urls "u1,u2" | --file urls.txt [--concurrency N]'); process.exit(2); }
  run(urls, concurrency).then(out => console.log(JSON.stringify(out, null, 1)));
}
main();

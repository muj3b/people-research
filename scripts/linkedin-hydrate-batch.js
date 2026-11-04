#!/usr/bin/env node
/**
 * linkedin-hydrate-batch.js
 * Bounded batch hydration of known public LinkedIn post URLs via the public
 * embed endpoint. No login, no API key. Dependency-free (Node builtins).
 *
 * Pattern: extract the numeric activity id from the post URL, fetch
 *   https://www.linkedin.com/embed/feed/update/urn:li:activity:{id}
 * Full post body sits in <meta name="description"> (not truncated in tests).
 * Comment count via data-num-comments; comment BODIES are signup-gated.
 *
 * There is no anonymous LinkedIn search; discovery comes from web search.
 *
 * Verified 2026-09-28: 4/4 real posts HTTP 200 (~26-31KB each), no rate
 * limits at concurrency 3, fake activity id -> clean HTTP 404.
 *
 * Usage:
 *   node linkedin-hydrate-batch.js --urls "https://www.linkedin.com/posts/...-activity-123-XYZ,https://..."
 *   node linkedin-hydrate-batch.js --file urls.txt [--concurrency 3]
 *
 * Output: JSON array of { url, platform, status, text, activity_id,
 *           comments_count, provenance, error? }
 * Status: ok | not_found | error
 */
'use strict';
const https = require('https');
const fs = require('fs');

const EMBED = 'https://www.linkedin.com/embed/feed/update/urn:li:activity:';
const DEFAULT_CONCURRENCY = 3;
const TIMEOUT_MS = 25000;
const UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

function get(url) {
  return new Promise((resolve, reject) => {
    const req = https.get(url, { headers: { 'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.9' } }, (res) => {
      let body = '';
      res.on('data', (c) => { body += c; if (body.length > 500000) req.destroy(); });
      res.on('end', () => resolve({ statusCode: res.statusCode, body }));
    });
    req.on('error', reject);
    req.setTimeout(TIMEOUT_MS, () => { req.destroy(new Error('timeout')); });
  });
}

function extractActivityId(rawUrl) {
  const m = rawUrl.match(/activity-(\d{10,25})/) || rawUrl.match(/urn:li:activity:(\d{10,25})/);
  return m ? m[1] : null;
}

function decodeEntities(s) {
  return s.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&#x27;/g, "'");
}

function extractBody(html) {
  const m = html.match(/<meta\s+name="description"\s+content="([^"]*)"/i)
         || html.match(/<meta\s+content="([^"]*)"\s+name="description"/i);
  return m ? decodeEntities(m[1]) : '';
}

function extractCommentsCount(html) {
  const m = html.match(/data-num-comments="(\d+)"/);
  return m ? parseInt(m[1], 10) : null;
}

async function hydrateOne(rawUrl) {
  const url = rawUrl.trim();
  const base = {
    url, platform: 'linkedin', status: 'error', text: '',
    provenance: {
      service: 'linkedin-embed', method: 'linkedin.com/embed/feed/update',
      fetched_at: new Date().toISOString(),
    },
  };
  const activityId = extractActivityId(url);
  if (!activityId) return { ...base, error: 'could not extract activity id from URL' };
  try {
    const { statusCode, body } = await get(EMBED + activityId);
    if (statusCode === 404) return { ...base, activity_id: activityId, status: 'not_found', error: 'post not found / deleted / private' };
    if (statusCode !== 200) return { ...base, activity_id: activityId, error: `embed http ${statusCode}` };
    const text = extractBody(body);
    if (!text) return { ...base, activity_id: activityId, error: 'no post body found in embed response' };
    return {
      ...base, activity_id: activityId, status: 'ok', text,
      comments_count: extractCommentsCount(body),
    };
  } catch (e) {
    return { ...base, activity_id: activityId, error: String(e.message || e).slice(0, 200) };
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

---
name: "people-research"
description: "Mass deep research into what people say across social platforms, forums, videos, comments, and communities. Use for people-driven topic, product, trend, competitor, audience, and sentiment research."
---

# People Research

**Status: ready for use, with named gaps.** Native collectors, cursor pagination, normalization, dedupe/ranking, transcript parsing, browser-session routes, and bounded smoke tests are verified. Run the self-test and smoke probe before a large research job. Pinterest and Rumble are excluded from the active default scope. No-login coverage is NOT complete for everything: see "Setup: what works no-login, what needs a login" below. Do not claim a platform/capability works no-login unless that section says so.

## SKILLLESS rule: never stop at a block

This is the top operating rule, above every platform section. If you hit a block, do NOT just tell the user you are blocked and stop. Figure out an alternative by yourself and continue with it. That is the whole point of this skill.

Fallback ladder, in order, for any blocked route. Work it top to bottom, and keep going until you have delivered something useful:

1. Retry the same route once, with backoff, in case it is a transient 502/429/422.
2. Try a different instance of the same service (Piped/Invidious/Redlib host rotation; re-check the public instance list first).
3. Try a different no-key tool for the same job (for YouTube transcripts: yt-dlp Android subtitles, then ytscrape, then npm youtube-transcript, then Invidious, then local Whisper; for TikTok comments: TikWM; for slideshows: gallery-dl, then TikWM images; for Reddit: Arctic Shift scoped search, then Redlib global search, then search-engine indexing).
4. Try a different client variant (yt-dlp `--extractor-args youtube:player_client=android` when the web client is bot-blocked; curl_cffi Chrome impersonation when stock curl gets a JS shell).
5. Download the public media and do it locally: yt-dlp download plus local faster-whisper for transcripts, plus ffmpeg frames for what is happening in the video, plus vision-reading of ordered slides.
6. Use search-engine indexing to find the URL, then hydrate that known URL with a working route.
7. Use a paste-link browser tool for public URLs only (see "Paste-link browser tools for the still-blocked items"): open it in your browser, paste the public URL, submit, let any Turnstile complete normally in the browser, copy the rendered result.
8. Use the logged-in browser, logged in as the user, and read the page directly (see "Manual login / logged-in browser is required for these").
9. Only after all of the above, report what remains blocked, and report it as a partial result: what you delivered, exactly what you tried for the missing piece (route, tool, error), and what the next test would be. Never report a block as the whole answer when a partial result exists.

Hard boundaries, which never move: never circumvent a CAPTCHA, access control, paywall, or rate/IP block with script tricks; never use another person's credentials; never send private, follower-only, or sensitive content to a third-party tool; never store cookies or session tokens in the skill or logs. Browser Turnstile completing normally in-browser is allowed; script bypass of Turnstile or a CAPTCHA is not. If a route would need one of those forbidden tricks, skip that route and move to the next rung of the ladder.

## Setup: what works no-login, what needs a login

Copy-paste setup, no login, no keys, no paid services. A fresh user following only this section can run the no-login routes. Extra installs are free and are listed here, not hidden in later sections.

Free installs needed for the full no-login matrix (install once, then the skill's commands work as written):

```sh
# yt-dlp, gallery-dl, ytscrape (all free, no key). System pip is PEP 668
# externally-managed on some machines, so use a venv and call the venv binaries
# by full path (bare `yt-dlp` is NOT on PATH on this VM):
python3 -m venv ~/workspace/tools/ytdlp-env
~/workspace/tools/ytdlp-env/bin/pip install yt-dlp gallery-dl ytscrape
~/workspace/tools/ytdlp-env/bin/yt-dlp --version       # 2026.10.26 verified
~/workspace/tools/ytdlp-env/bin/gallery-dl --version   # 1.32.19 verified
~/workspace/tools/ytdlp-env/bin/ytscrape --help        # v2.2.0 verified
# curl_cffi (free, no key) for Threads no-login pages (browser TLS fingerprint):
pip install curl_cffi
# npm youtube-transcript (free, no key) as a second YouTube transcript implementation:
mkdir -p ~/workspace/tools/yttranscript-npm && cd ~/workspace/tools/yttranscript-npm
npm init -y && npm install youtube-transcript
# Local Whisper (free, no key, cached model, offline after first download):
# use ~/workspace/tools/whisper-env/bin/python with HF_HUB_OFFLINE=1; system Python's
# faster-whisper is broken against its PyAV on this VM (TypeError: metadata_errors).
# ffmpeg (system package) for frame extraction in scripts/local-video-transcribe.py.
# Accessibility note (Nov 4, 2026 self-test): a fresh checkout that only runs
# `pip install yt-dlp` will FAIL on PEP 668 systems and will miss gallery-dl,
# ytscrape, and npm youtube-transcript entirely (they were not on PATH here
# until the installs above were run). Follow the venv paths above, not bare names.
```

No-login, verified (see platform sections for commands and evidence): YouTube discovery/transcripts/comments; TikTok comments via TikWM, slideshows via gallery-dl/TikWM, transcripts via native VTT/fbtotranscript/local Whisper; Instagram carousels via embed HTML, transcripts via fbtotranscript/local Whisper; Facebook video captions via yt-dlp auto-subs and video transcripts via fbtotranscript/local Whisper on a supplied URL; Threads post text, first-batch replies, profile/keyword/tag discovery, and video transcripts via curl_cffi; X post bodies via oEmbed and first-page replies via FxTwitter conversation; LinkedIn post bodies via embed and comment counts via embed title; Reddit scoped search via Arctic Shift and global search via Redlib/RSS; Bluesky, Hacker News, and forums fully.

### Manual login / logged-in browser is required for these (setup notice)

After a wide sweep (about 68 web queries, 169 repo/tool entries, plus a second paste-link sweep), NO no-login route was found for the items below. During setup, tell the user plainly: these need a manual login in the AI's own browser, logged in as the user. This is not a failure of setup; it is the current state of those platforms. No credentials are ever stored in this skill, no session tokens are pasted into logs, and live tokens/IDs are harvested from the live page per session only.

- TikTok search/discovery, and nested reply bodies (top-level comments work no-login via TikWM; reply-to-reply bodies do not).
- Instagram comment bodies verbatim, and native transcripts (captions and local-Whisper transcripts work; verbatim comment threads and a native text track do not).
- Facebook posts, comments, discovery, and ordered multi-photo slides (video captions/transcripts on a supplied URL work; finding and reading posts/comments/slides does not).
- Threads pagination and full reply trees (first batch of replies works no-login; paging beyond it does not).
- X keyword/topic search, and full reply trees (first page of replies works no-login; keyword search and deeper trees do not).
- LinkedIn full comment threads (post bodies and comment counts work no-login; full verbatim threads do not).
- Saveto end to end (its API is Turnstile-gated; it is a browser-form fallback only, see below).

Logged-in browser procedure for any of the above (works for Muse, Grok, Duet, Dots, Aside browser, Claude Code, Codex, or any equivalent AI with browser access): the user logs in to the platform in that AI's browser, as themselves; the AI opens the post, profile, search page, or thread in that logged-in browser; the AI reads or copies the comments, slides, or transcript directly from the rendered page, preserving order; the AI never asks the user for a password, never stores cookies or tokens, and never sends private or follower-only content to a third-party tool. If the platform shows a login wall or checkpoint, stop and report that the logged-in session is needed, do not work around it with scraped credentials.

### Browser fallback: paste-link online tools (last resort, before login)

For the still-blocked items, a second last resort exists before or alongside login: paste-link tools in the AI's browser, where you paste a public URL and copy the rendered result. Procedure: open the tool in the AI's browser, paste the public URL only, submit, let any Turnstile/CAPTCHA complete in the browser itself (never solve it from a script), copy the rendered comments/transcript/slides, and record the tool name, URL, and time in provenance. Never send private, follower-only, or sensitive content to these tools. A browser-form tool is NOT a curl/API route: do not claim it works from a script. Tools marked unverified below have not had a live-browser paste test yet; the exact test is: open the tool, paste a known public URL for that platform, submit, read the rendered panel. That live-browser test is still queued and is not claimed as passed here. See "Paste-link browser tools for the still-blocked items" for the per-item table.

### Fallback ladder per platform (summary; full commands are in the platform sections)

Every row ends the same way: paste-link browser tool, then logged-in browser, then a partial-results report. Never stop before the end of the row.

- YouTube: Piped search/comments, then yt-dlp Android subtitles/comments, then ytscrape, then npm youtube-transcript, then Invidious, then local Whisper, then paste-link transcript tools, then logged-in browser, then partial report.
- TikTok: SSR/TikWM metadata, then TikWM comments, then gallery-dl/TikWM slideshows, then native VTT, then fbtotranscript, then local Whisper, then paste-link tools (TTViewer, TikRapid, TikSaveHub, Adlicio), then logged-in browser search/comments, then partial report.
- Instagram: embed HTML caption/carousel, then fbtotranscript, then local Whisper, then paste-link tools (Adlicio, ZocialComment, InstaScript), then logged-in browser comments, then partial report.
- Facebook: oEmbed validity check, then yt-dlp auto-subs, then fbtotranscript, then local Whisper on a supplied URL, then paste-link tools (ExportComments, TweetMediaArchive), then logged-in browser posts/comments/slides, then partial report.
- Threads: curl_cffi post/profile/search/tag, then SSR video_versions plus local Whisper, then paste-link tools (ThreadsTools, Adlicio, ZocialComment), then logged-in browser pagination/full trees, then partial report.
- X: web-search discovery, then oEmbed hydration, then FxTwitter conversation (first page), then paste-link tools (TwitterViewer, FinchView, GetXAPI), then logged-in browser search/full trees, then partial report.
- LinkedIn: web-search discovery, then embed hydration, then title comment counts, then paste-link tools (Adlicio, GetSendable, Connie), then logged-in browser full threads, then partial report.
- Reddit: Arctic Shift scoped search, then Redlib global search, then search.rss (bridge only, expires Nov 13, 2026), then search-engine indexing, then logged-in browser search, then partial report.
- Bluesky, Hacker News, forums: native APIs and feeds first; on failure, retry once, then search-engine indexing, then partial report.

## Mission

Research what real people say, demonstrate, recommend, complain about, and debate. Prioritize social posts, comments, transcripts, forums, reviews, and community evidence over academic papers or generic SEO pages unless the user asks for formal research. Exclude arXiv, Douyin, Xiaohongshu, and Bilibili unless the user explicitly asks; default to the US-stack sources in this skill.

Default window: the last 30 days. Change it when requested.

## Source priority

Use the strongest available native/direct method first:

1. YouTube/Shorts: `youtube.search`, metadata, captions/transcripts, comments.
2. X: `twitter.search`, user timelines, individual posts, visible same-author threads.
3. Reddit: bundled `reddit-reading` script. Run its doctor once, then search/posts/threads/comments. Prefer OAuth script-app mode when configured.
4. Hacker News: Algolia search and Firebase item/comment endpoints.
5. Bluesky: public AT Protocol endpoints, especially `app.bsky.feed.searchPosts` and `getPostThread`.
6. Forums and Q&A/reviews: web search, RSS, sitemaps, site-native feeds, and `webfetch`.
7. LinkedIn: native web search for public LinkedIn posts, articles, profiles, and discussions; use the logged-in `linkedin` global for known-author profiles and posts.
8. TikTok: native page SSR data first; search/comments through direct endpoints only when the current signer/session path is verified.
9. Instagram: logged-in same-origin requests and current GraphQL/API operations; browser page reading is fallback, not the main mass method.
10. Facebook: same-origin GraphQL or public HTML only after current tokens/operation IDs are verified.
11. Threads: use the logged-in native search/session path when available; otherwise report it as partial rather than pretending zero results.

Pinterest and Rumble are outside the default scope. Do not spend collection budget on them unless the user explicitly re-adds them.

Never use OpenCLI, ScrapeCreators, SocialCrawl, Apify, Brave paid search, Perplexity, paid proxies, paid search, or paid transcription unless the user explicitly approves it. Optional free public-URL transcript websites may be used as a capped fallback for public content — standing user approval granted Sep 28, 2026, no per-batch confirmation needed; never send private content or credentials. Target remains free-forever: no monthly fees and no credits that run out.

## Query planning

Before fetching, create 6-12 targeted queries:

- exact topic/person/product terms
- how users describe the problem in ordinary language
- criticism, complaints, alternatives, pricing, failures, and recommendations
- platform-specific terms and hashtags
- disambiguation terms when names or brands collide

Run independent source searches in parallel when safe. Google searches must be sequential to avoid CAPTCHA. Respect each platform's rate limits.

## Efficient collection pipeline

### Tier 1: discovery

Collect transcript candidates only. Default fields are URL, source, date for last-30-days filtering, and minimal title/caption text for relevance. Do not collect likes, comments, shares, views, or author unless the user asks or supplies an author filter.

```json
{"source":"tiktok","id":"...","url":"...","date":"...","title":"...","query":"..."}
```

If the user names an author, filter by that author directly instead of broad author harvesting. Target 50-300 candidate URLs across sources. Detect media kind cheaply from the URL pattern (`/photo/`, `/reel/`, `/watch/`, carousel hints) and defer full slide extraction. Do not fetch comments, engagement, or videos yet.

### Tier 2: deterministic filtering

Normalize URLs and IDs. Exact-dedupe first, then near-dedupe titles/captions. Rank with:

- relevance to the actual question
- recency
- first-hand specificity
- source diversity

Skip engagement, comment count, and author diversity unless the user explicitly asks. Keep roughly 20-40 candidates.

### Tier 3: text expansion

Split by media kind. For video posts, fetch transcripts first. For image/slide posts, collect ordered slide images and vision-read them.

Video order:

- native transcript/caption endpoint first
- approved transcript website batch for public video URLs
- post description/caption only when needed for context
- comments/replies only if the user explicitly asks

Image/slide order:

- detect image post vs video post from URL pattern plus page data
- collect ordered slide image URLs plus caption/alt text
- vision-read each slide in order, one idea per slide
- return caption once plus text per slide

Keep roughly 8-15 deep sources. Cache results by canonical source ID.

### Tier 4: transcript fallback

This skill stays text-only. After native captions/transcripts and visible text layers, use an approved free public-URL transcript website for a small set of high-value public videos. Treat each service as availability-dependent, record provenance, and stop on quotas, errors, or unclear privacy terms.

Decision order:

`native transcript/caption -> direct subtitle sidecar -> description/caption/comments -> approved free public-URL transcript website -> official/mirrored text -> skip and disclose gap`

## Platform-specific rules

### YouTube

Use the existing YouTube skill. Fetch transcripts and comments directly. Do not use browser DOM or download videos for ordinary research.

No-login fallback routes (verified live Sep 28, 2026):
- Discovery: Piped API `https://api.piped.private.coffee/search?q=<query>&filter=videos` returns video IDs, titles, uploaders (20 real on-topic results in test). Backup: Invidious `https://invidious.f5.si/api/v1/search` (instance churn is the risk; re-check the public instance list if it 502s).
- Transcripts (primary): `scripts/youtube-transcript-batch.py` — self-hosted `youtube-transcript-api`, no key, no login, venv at `~/workspace/tools/ytapi-env`. Verified live returning real transcripts (129 segments / 4,733 chars on the Wharton test video). Rate reality from this VM: strictly sequential, ~65s between videos (~40-60/hour); bursts trigger YouTube `IpBlocked`, which lifts after a cooldown — the script stops the batch cleanly on `ip_blocked` so the caller can resume later.
- Transcripts via Piped: DEAD from this VM as of Sep 28, 2026 — `/streams/:id` returns HTTP 500 `SignInConfirmNotBotException` (LOGIN_REQUIRED, IP-level) on the one reachable instance; re-tested 0/8 instances Nov 4, 2026. Do not use Piped for transcripts until re-verified.
- Transcripts, new no-key routes (Nov 4, 2026): `ytscrape transcript <id> --format json` (pip, 299 snippets on the test video) and npm `youtube-transcript` (same 299 snippets); yt-dlp Android client is the only client that downloads subtitles. Invidious: fetch `/api/v1/videos/<id>` first for the exact caption label (`English (auto-generated)`), or use `?lang=en`; never hardcode `label=English`; single working API instance only.
- Transcripts via third-party converters: all dead via curl as of Sep 28, 2026 (kome.ai 429/bot-wall, youtubetotranscript.com Cloudflare 403, youtubetranscript.com Vercel checkpoint, notegpt 404, tactiq JS-required). fbtotranscript returns 422 "YouTube temporarily blocked automated access from this server" — dead for YouTube, still alive for TikTok/Instagram.
- Comments: Piped `/comments/:id` returns real comment data, no login; yt-dlp Android `--write-comments` also works, truncating `.info.json` post-hoc to cap (no `--max-comments` option in yt-dlp 2026.10.26).
- Metadata: oEmbed (`https://www.youtube.com/oembed?url=<video-url>`) or noembed.com for title/author without login.

### X

Use the existing `twitter` global. Use Latest for discovery and Top for consensus. Fetch individual posts and visible same-author threads for the strongest evidence. Do not claim exhaustive reply-tree coverage.

No-login fallback (verified Sep 24, 2026): discover tweet URLs via web search, then hydrate each with `https://publish.x.com/oembed?url=<tweet-url>` — returns tweet text, author, and date with no auth (verified live on a real tweet). Nitter instances are dead as of Sep 2026 (X legal action; repo re-archived) and the syndication API returns empty from servers — do not build on either. Search-engine indexing of x.com is thin for niche topics; the logged-in session remains the only true search route.

Batch hydration (verified Sep 28, 2026): `scripts/x-hydrate-batch.js --urls "u1,u2" [--concurrency 3]` — 7/7 real tweets returned HTTP 200 with full text, author handle, and date; no rate limits observed at concurrency 5 or across 20 rapid sequential requests; nonexistent tweet returns clean HTTP 404 (usable as validity check). X batch search alternatives are all dead as of Sep 28, 2026: xcancel.com → HTTP 451 (legal block), nitter.net/lightbrd.com → timeouts, the public guest-activate API endpoint times out from this VM, twscrape-class tools need a logged-in account's cookies (not permitted), Apify scrapers are paid. X batch = hydrate known URLs via oEmbed; discovery comes from web-search indexing (`site:x.com`) or the logged-in session.

Replies, first page (Nov 4, 2026, no-login): `https://api.fxtwitter.com/2/conversation/<id>?ranking_mode=recency` returns full reply bodies with author, date, likes, and `replying_to`. Do NOT use `/2/thread` for replies (same-author chain only). Keyword search via FxTwitter was unresolved, not proven dead (the text crawler sends no custom User-Agent; FxEmbed docs stress a descriptive UA) — the follow-up is `curl -A <descriptive UA> https://api.fxtwitter.com/2/search?q=...` from a shell/browser-capable agent. Pagination beyond page 1 and nested reply trees are unverified; older example IDs can 404 on conversation.

### Reddit

Use the Arctic Shift adapter `scripts/reddit-arctic.py` (stdlib only): `doctor`, `search "q" --sub NAME` (or `--subs A,B` fan-out), `thread URL-or-ID`, `sub NAME`, `user NAME`, plus `--json`. Backend is the arctic-shift.photon-reddit.com anonymous API — verified live Nov 4, 2026 returning real submissions, comments with scores, and permalinks, with newest-post lag ~30 min. Polite by default (~1 request per second, one retry on 429/422/5xx/disconnect).

Hard limits, by the API's own design — do not work around by guessing:
- NO global cross-subreddit keyword search: `query`/`title`/`selftext`/`body` require `author` or `subreddit` (HTTP 400 otherwise). Unscoped `search` exits with a clear error; fan out over known subs with `--subs`, or discover a thread URL via search-engine indexing and hydrate it with `thread`.
- Keyword searches are windowed by default (`--days 30` → `after=<unix>`). Unwindowed keyword queries on busy subs return HTTP 422 "Timeout".
- `sort` is date order only; `--sort top` is client-side by score, and fresh scores/counts are ingest snapshots (often score=1, num_comments=0 on brand-new posts) — do not treat them as settled.
- `permalink` is not a valid Arctic field; the adapter rebuilds `https://www.reddit.com/r/<sub>/comments/<id>/`.
- No uptime guarantee. Transient disconnects/422s occur; the adapter retries once, then reports the failure — retry later rather than hammering.

Previous backend: pullpush.io (in `reddit-reading/scripts/reddit.py`) is DOWN as of Nov 4, 2026 — `doctor` returns HTTP 521, search times out. Do not use it until re-verified; the Arctic adapter is the primary scoped route.

Global keyword search (Nov 4, 2026, no-login, FIXED): Redlib via `https://safereddit.com/search?q=...` — cross-sub results with exact scores, pagination via `after=`, sub-scoped search works; bare `sort=new|top|comments` 404s, add `type=posts`; use `/user/`, not `/u/`. Only safereddit worked out of 6 Redlib hosts tried, so re-check the instance if it fails. Bridge route: `search.rss` with a full Chrome UA (curl default and bare `Mozilla/5.0` both 403) returns 25 entries, but Reddit RSS ends Nov 13, 2026 and the public Data API ends Mar 2027 — Redlib is the durable route. Live scores come from Redlib, not Arctic: same thread read Arctic 91 vs Redlib 104. The Arctic adapter retries posts-query up to 3x with exponential backoff on 422/disconnect, then falls back to Redlib search and hydrates via Arctic ids/comments. Direct reddit.com anonymous fetches remain bot-walled (403) from servers, as are old.reddit (302 → 403) and `.json` endpoints. Search-engine indexing of Reddit is spotty (a `site:reddit.com` query returned 0 results in testing; a topic query surfaced the source article, not the Reddit thread). The task-named hosts `search.arctic-shift.com` and `api.arctic-shift.com` do NOT work from this VM (521); the working base is `arctic-shift.photon-reddit.com`.

The only untested route is the logged-in browser session: a main agent with live browser access can open reddit.com search/thread pages while logged in and read them directly. That path was NOT tested by this probe (subagents have no live browser) — do not claim it works until a browser-capable agent verifies it. It is not needed for the archive route above.

### TikTok

For a known public video, fetch the page and parse `__UNIVERSAL_DATA_FOR_REHYDRATION__`. Read `subtitleInfos` or caption-info URLs and fetch the VTT sidecar directly. This avoids downloading the video.

Search and comments require current TikTok request signing and anti-replay values such as `msToken`, `X-Bogus`, and sometimes `X-Gnarly`. Do not hardcode stale signatures. Use a verified current local signer or a verified session request. If blocked, report the limitation and continue with other sources.

Image posts: TikTok photo carousels use `/photo/` URLs. No-login slideshow routes (Nov 4, 2026, FIXED with a caveat): gallery-dl returns all slides as ordered JPGs plus the slideshow MP3; TikWM `https://www.tikwm.com/api/?url=<photo-post-url>` returns `images[]` with ordered CDN URLs (hashes matched gallery-dl exactly on the test post) plus caption and audio. yt-dlp on `/photo/` still fails (Unsupported URL); anonymous SSR still has no `image_post_info`, so do not rely on page data for slides. Caveat (self-test 2026-11-04): a different public photo post failed both routes (TikWM parsing failed, gallery-dl "post not available"), so slideshows are post-dependent; fall back to TTViewer/TikRapid in a browser or the logged-in browser when both routes fail. There is no speech transcript for slide posts; vision-read the slides in order instead.

Comments (Nov 4, 2026, FIXED, no-login): TikWM `https://www.tikwm.com/api/comment/list?url=<tiktok-video-url>&count=20&cursor=0` — 20/20 on page 1, pagination via `cursor`, each comment with id, text, like count, reply count, timestamp, author. Caveat: about 300 req/mo free advertised; anonymous GETs worked on test day. Nested reply-to-reply bodies are still blocked; the unsigned TikTok comment API itself still returns an error envelope, so TikWM is the route, not the native API.

Native captions without login (verified Sep 24, 2026; status change Sep 28, 2026): fetching the video page and parsing `subtitleInfos` from the SSR data still works — caption tracks and signed VTT URLs are detectable from this server, no login. But downloading the signed VTT bytes is now network-blocked from this VM (the sandbox egress proxy blackholes TikTok CDN hosts after the TLS handshake), so the full native VTT path must run from an unproxied network (e.g. the user's own machine). Working transcript route from this VM: the fbtotranscript fallback (verified 2/2 real videos Sep 28, 2026). Clean edge-case signals: `"subtitleInfos":[]` = video has no captions; missing key = photo-mode post. Discovery stays the hard part: anonymous `/search?q=` is captcha-walled and TikWM search endpoints 404/Cloudflare 403, so use web-search indexing (`site:tiktok.com` queries) for discovery, then per-video fetches. TikTok search remains a still-blocked item (browser/login fallback only).

### Instagram

Use the logged-in same-origin session when available. Prefer current page hydration and live requests over stale GraphQL/API hashes or doc IDs. Fetch caption text, metadata, and comments first. The tested Reel had no publicly exposed native text track. For high-value public Reels, use the approved free transcript-website fallback. Saveto returned a timestamped 00:00-00:26 transcript from the tested public Reel. Keep the workflow text-only.

Image posts: single images and `CAROUSEL_ALBUM` posts expose ordered children through the logged-in page/session data (`/{media-id}/children` shape: each child with `media_type` plus `media_url`). Collect child image URLs in order plus parent caption and per-item alt text when exposed, then vision-read each slide in order. The official API shape only covers owned/business media, so arbitrary public posts go through the logged-in page/session path.

No-login carousel route (Nov 4, 2026): the embed endpoint `/p/<id>/embed/` (HTTP 200) exposes post-media images in document order with signed query params (one tag literally reads `CAROUSEL_ITEM`). Use the FULL signed URL: stripping a URL at `.jpg` breaks it ("Bad URL hash", 403). On the test post all 3 embed images downloaded as real JPEGs and were vision-readable. Caveats: embed order is assumed to equal app slide order (unverified against the app), and embed showed 3 images while yt-dlp enumerated 8 playlist items for the same mixed photo/video post, so embed may show a subset. Comment bodies verbatim remain session-only; embed gives caption plus a "View all N comments" link only.

No clean no-login bulk route exists (verified Sep 24, 2026): the `/reel/<id>/embed/captioned/` endpoint returns 200 but the caption only renders in JS DOM (needs a browser render); Dumpor-class viewers (dumpor.com, greatfon.io, picuki.com) are alive but shallow; imginn is 403 from servers. Keep fbtotranscript as the primary transcript route — verified 5/5 on real public reels (2 Sep 24, 3 Sep 28, including Hindi and English content) — and browser render as backup. Raw curl of reel pages is a dead end (logged-out JS shell, no og: tags or caption JSON).

### Public transcript service fallback

- Primary verified fallback: `https://fbtotranscript.com/` with direct endpoint `https://fbtotranscript.com/api/transcript`; it accepts public Facebook, Instagram, and TikTok URLs. YouTube is NOT accepted (HTTP 422 "YouTube temporarily blocked automated access from this server" — use `scripts/youtube-transcript-batch.py` for YouTube instead).
- `scripts/transcript-batch.js --urls "u1,u2" [--concurrency 3]` submits bounded public-URL batches and normalizes results into the common transcript schema. Live-verified end to end Sep 28, 2026 on real URLs: 3/3 (TikTok 487 chars, Instagram 471 + 1,859 chars).
- Reliability note: fbtotranscript throws intermittent HTTP 525/502 (service/Cloudflare-side flakiness, not content verdicts); every failure in testing succeeded on immediate retry — the script's retry-with-backoff is the correct handling. Keep concurrency at 3.
- Backup verified for Instagram/TikTok: Saveto pages `https://saveto.ai/instagram-transcript-generator/` and `https://saveto.ai/ai-transcription/`.
- Standing approval (Sep 28, 2026): the user has approved third-party transcript processing for public URLs outright — no per-batch confirmation needed. Never submit private, follower-only, or sensitive content.
- Treat services as availability-dependent, not permanent APIs; dedupe and cap concurrency.

### Facebook

Use current same-origin requests or public page HTML only. Facebook `fb_dtsg`, `lsd`, and GraphQL operation IDs rotate. Harvest them from the live page when needed and never assume old IDs remain valid. Some public videos expose a native `Captions` control and caption text through the browser player accessibility tree; use that when present. A second tested public video had no caption control, so mark transcript availability per video.

No anonymous server route exists for posts/comments/discovery/slides (verified Sep 24, 2026; re-confirmed Sep 28, 2026 and Nov 4, 2026): mbasic.facebook.com returns an error page, the page plugin renders a shell with no post text, and search engines surfaced zero facebook.com posts for the test topic. Facebook posts/comments/discovery/ordered slides are session-only — state that rather than "blocked". Re-probe Sep 28, 2026 found no anonymous batch route either: direct post fetches return 400 bot-rejection pages. Update Nov 4, 2026: Facebook oEmbed is now tokenless (HTTP 200, about 1,000 req/hr documented) but still textless — validity/author check only. Video fast path, no-login, on a supplied URL: yt-dlp `--list-subs` shows automatic captions `en_US` in SRT; try `--write-auto-subs --sub-langs en_US` before downloading + Whisper. The only other server-side fallback is the fbtotranscript third-party service for public *video* URLs (transcripts, not post text). Ordered multi-photo slides no-login: gallery-dl photo/set/page-photos all fail `AuthRequired`; a single-photo page via curl_cffi gives `scontent` image URLs with duplicates but no order, per-slide captions, or alt text — ordered carousel vision-reading remains blocked.

Image posts: multi-photo posts expose ordered images through post `attachments{subattachments}` or Photo-node `images[]` shapes in session/page data. Collect image URLs in subattachment order plus post message and per-photo `alt_text` when exposed, then vision-read each slide in order. Official Graph endpoints only cover owned/page media, so arbitrary public posts go through the logged-in page/session path.

### Threads

No-login routes (Nov 4, 2026, via curl_cffi `impersonate="chrome"`, free, no key; stock curl gets a stripped JS shell): post text via `facebookexternalhit/1.1` or Googlebot UA in `og:description`; post + first-batch replies via curl_cffi post page `thread_items` captions (post + 4 replies verified, with authors, like and reply counts); profile discovery via curl_cffi profile page (4 recent posts, full captions); keyword discovery via curl_cffi search page (22 captions + 10 authors) and tag page (20 `thread_items`), first page only. Video transcript: SSR `video_versions` direct CDN mp4, curl download, then local faster-whisper (774 chars on a 67 s test video). yt-dlp has no Threads extractor. Tokenless oEmbed (`graph.threads.com/oembed`) has no post text and needs the bare code URL. Pagination and full reply trees are still blocked (browser/login fallback only). The logged-in native Search UI for Top, Recent, and Profiles remains the session route; preserve live cursors/request shapes for post details and replies.

### LinkedIn

Use native web search for bulk discovery of public LinkedIn URLs. Run several ordinary-language queries per topic, paginate result pages when available, keep only canonical `linkedin.com/posts/`, `linkedin.com/pulse/`, `linkedin.com/feed/update/`, profile, company, and article URLs, then exact-dedupe and rank. Open public results with `webfetch` when readable; use the logged-in `linkedin` global for known authors, profiles, companies, and `getUserPosts`.

This is search-index bulk discovery, not an exhaustive LinkedIn firehose. It can miss login-gated posts, unindexed posts, comments, and feed-only content. LinkedIn text posts/articles are supported; LinkedIn video transcripts are not currently verified and must be marked unavailable unless a visible caption/transcript exists.

Post bodies without login (verified Sep 24, 2026): after discovering `linkedin.com/posts/...activity-{id}-...` URLs via search, extract the activity ID and fetch `https://www.linkedin.com/embed/feed/update/urn:li:activity:{id}` — returns the full post body, no login (2/2 test posts returned 6,078 and 617 chars). The public post-page HTML also carries the body plus some top comments. Deeper comment threads: search-engine snippets only. The Voyager API without auth is dead (requires session cookies).

Batch hydration (verified Sep 28, 2026): `scripts/linkedin-hydrate-batch.js --urls "u1,u2" [--concurrency 3]` — 4/4 real public posts returned HTTP 200 with complete post bodies (850–1,625 chars, not truncated) and comment counts via `data-num-comments`; no rate limits at concurrency 3; fake activity ID returns clean HTTP 404. Comment *bodies* stay behind the signup CTA — bodies + counts only. No anonymous LinkedIn search exists; this hydrates known post URLs found via web search.

Comment counts, corrected (Nov 4, 2026): the `data-num-comments` attribute claim is unrefuted but the text crawler strips attributes, and embed hydration returned `comments_count: None` on 3/3 in the latest probe. Parse `| (\d+) comments?` from the embed/public-page `<title>` as primary ("24 comments", "83 comments" verified), keep the attribute as secondary, and report `count_unknown` (never 0) when neither is present. Full comment threads remain blocked (browser/login fallback only).

### Pinterest

Outside the active default scope. Do not collect it unless explicitly requested.

### Forums and other communities

Prefer RSS, JSON feeds, sitemaps, and native search. Use `webfetch` for the bounded thread body. Search multiple communities rather than over-weighting one forum.

Verified no-login routes (Sep 24, 2026):
- WSO (Wall Street Oasis): thread pages fetch directly with a browser UA — full OP + all replies, no login. The old "login-gated" label was wrong.
- Quora: discover via search engine, read via the text-reader (`browser.open`) — full question + multiple complete answers. Direct curl is Cloudflare-walled (403).
- Stack Exchange API: `https://api.stackexchange.com/2.3/...` — no key needed (300 req/day anonymous); use `filter=withbody` and `/questions/{id}/answers` for full bodies. Useful sites: money, workplace, academia.
- Discourse forums: the generic JSON pattern `/search.json` and `/t/{id}.json` works on any Discourse instance — find finance-relevant instances per topic.
- CollegeVine Q&A: full expert Q&A pages via reader — good for high-school topics.
- Lemmy API (`lemmy.ml/api/v3/search`): works mechanically, thin content for niche topics.
- Reddit bodies: pullpush.io mirror (see Reddit section).
Dead ends: Indie Hackers programmatic search, Lobsters (bot wall for curl), Quora direct curl, r.jina.ai proxy from our servers.

### Fix wiring 2026-11-04 (second sweep, applied to the skill)

All routes below are no-login, no key, public URLs only, unless marked otherwise. Evidence is from the 2026-11-04 fix sweep (`~/workspace/people-research-fix-sweep-2026-11-04.md`).

- **TikTok comments (FIXED, no-login):** TikWM public API, no key: `https://www.tikwm.com/api/comment/list?url=<tiktok-video-url>&count=20&cursor=0` — page 1 gave 20/20 comments, total 8,737, cursor 20; page 2 gave 5 comments, cursor 25. Each comment carries id, text, like count, reply count, timestamp, author. Caveat: TikWM advertises about 300 req/mo free; anonymous GETs worked on test day, availability is not guaranteed. Nested reply-to-reply bodies are still blocked (guessed reply endpoint 404s).
- **TikTok slideshows (FIXED, no-login, two routes, with a post-dependence caveat):** gallery-dl (already installed, no login) returned all 7 slides as ordered JPGs plus the slideshow MP3 on a real photo post; TikWM `https://www.tikwm.com/api/?url=<photo-post-url>` returned `images[]` with 7 ordered CDN URLs whose hashes matched gallery-dl's files exactly, plus caption and audio. yt-dlp on `/photo/` still fails (Unsupported URL); anonymous SSR still has no `image_post_info`. Caveat from the 2026-11-04 self-test: on a DIFFERENT public photo post (`@jcxv.ts/photo/7411023031876750599`), TikWM returned `Url parsing is failed` and gallery-dl returned "Requested post not available". Slideshows are therefore working with a caveat, not universally fixed; if both routes fail on a post, use the paste-link browser fallback (TTViewer/TikRapid) or the logged-in browser, and do not claim the post is unavailable on one route alone.
- **Threads (largely FIXED, no-login):** the missed variable was browser TLS fingerprinting. Stock curl gets a stripped page; `curl_cffi` with `impersonate="chrome"` (free PyPI, no key) gets full SSR JSON. Post text cheap route: `facebookexternalhit/1.1` or Googlebot UA returns full post text in `og:description` (309 and 391 chars verified). Post + first-batch replies: curl_cffi post page gave 5 `thread_items` captions (post + 4 replies, with authors, like and reply counts). Profile discovery: 4 recent posts with full captions. Keyword discovery: search page gave 22 real post captions + 10 authors; tag page gave 20 `thread_items`. First page only; pagination and full trees are still blocked. Video: SSR `video_versions` gives a direct CDN mp4 (curl download 200, 5.7 MB, 67 s) then local faster-whisper gave 774 coherent chars. yt-dlp has NO Threads extractor; do not route Threads video through yt-dlp. Tokenless Threads oEmbed (`graph.threads.com/oembed`, HTTP 200) contains no post text, only "View on Threads", and requires the bare code URL (slug-suffixed URLs 400).
- **X replies, first page (FIXED, no-login):** `https://api.fxtwitter.com/2/conversation/<id>?ranking_mode=recency` (also `likes`) — verified on a real public post: HTTP 200, full third-party reply bodies with author, date, likes, `replying_to`, plus `cursor.bottom` for pagination. Do NOT use `/2/thread` for replies: it returns the same-author chain only. Also verified: author timeline `api.fxtwitter.com/2/profile/<handle>/statuses` and per-author RSS. Caveat: an older example ID returned 404 on conversation, so recent posts are proven, arbitrary old IDs are not; pagination beyond page 1 and nested reply trees are unverified.
- **LinkedIn comment counts (FIXED via a different field):** parse `| (\d+) comments?` from the embed/public-page `<title>` as primary ("24 comments" and "83 comments" verified); keep `data-num-comments` as secondary. If neither is present, report `count_unknown`, never 0. A post with no count suffix most likely means 0 comments, but that is an inference, not a verified rule. Full comment threads are still blocked.
- **Reddit global search (FIXED, with expiry warnings):** Redlib via `https://safereddit.com/search?q=...` — HTTP 200, 7 cross-sub results with exact scores, pagination via `after=` works, sub-scoped search works. Sort quirk: bare `sort=new|top|comments` 404s; with `type=posts` present they work. Use `/user/`, not `/u/` (302/bot-wall). Only safereddit worked that night out of 6 Redlib hosts tried. Second route: `search.rss` with a full Chrome UA (curl default and bare `Mozilla/5.0` both 403) — HTTP 200, 25 entries. Hard expiries: Reddit RSS ends Nov 13, 2026, public Data API ends Mar 2027; Redlib is the durable route, RSS is a bridge. Live scores via Redlib (same thread: Arctic 91 vs Redlib 104, plus 22 comment scores). Arctic scores are not always 1, but fresh posts read 1/0; never rank by an Arctic fresh score. Arctic adapter now retries posts-query up to 3x with exponential backoff on 422/disconnect, then falls back to Redlib search and hydrates via Arctic ids/comments.
- **YouTube transcripts (new routes, old block moot):** `ytscrape` (pip, no key, v2.2.0): `ytscrape transcript <id> --format json` gave 299 timestamped snippets on the test video, matching yt-dlp/Invidious; also verified for search, video metadata, and comments, and a second video's manual captions. npm `youtube-transcript`: same 299 snippets on the same video, a second independent no-key implementation. yt-dlp client sweep: android is the only client that downloads subtitles; iOS and web list subs but download fails; web_safari hit 429 then "no captions"; tv, android_vr, tv_embedded bot-blocked — this contradicts 2026 guides claiming android_vr/iOS bypasses. Invidious method fix: `/api/v1/captions/<id>?label=English` 404s; fetch `/api/v1/videos/<id>` first for the exact label `English (auto-generated)`, or use `?lang=en`. Still single-instance (only `yt.chocolatemoo53.com` has `api: true` in the registry). Piped `/streams` dead on 0/8 instances tested; Piped search and comments survive on one instance.
- **Facebook video captions (new fast path):** yt-dlp `--list-subs` on the test video shows automatic captions `en_US` in SRT; try `--write-auto-subs --sub-langs en_US` before downloading + Whisper. Facebook oEmbed is now tokenless (HTTP 200, about 1,000 req/hr documented) but still textless — validity/author check only, not hydration.
- **Scripts already referenced:** `scripts/local-video-transcribe.py` (yt-dlp Android subs → Invidious → youtube-transcript-api → download + local Whisper + ffmpeg frames; `--self-test` passes) and `scripts/reddit-arctic.py` (Arctic Shift adapter, now with 3x exponential-backoff retry; `doctor` verified) are the wired entry points for the video and Reddit chains above. Do not re-derive those chains by hand when the scripts exist.

### Paste-link browser tools for the still-blocked items (browser fallback, NOT curl)

Status language, used consistently below: **docs-claimed** = the tool's own site/docs describe a paste-link flow; it has NOT had a live-browser paste test, so it is not claimed to work end to end. **Live-browser test queued** = the exact test is: open the tool in a browser-capable AI's browser, paste a known public URL, submit, let any Turnstile/CAPTCHA complete in the browser itself, copy the rendered result, and record what actually came back versus the claim, any cap hit, and any login/key/paywall hit. Never paste private, follower-only, or sensitive content into any of these tools. Never claim a browser-form tool works via curl. Keyed/paid APIs (Supadata API, Apify actors, ScrapeCreators, Bright Data, HarvestAPI, Scavio) were checked and are excluded from the no-key workflow; they are listed in the full research notes only so the check is auditable. Full research notes (about 61 web/GitHub queries across three tracks, about 140 tool/repo rows): `~/workspace/people-research-opensource/paste-link-tiktok-instagram-2026-11-04.md`, `paste-link-facebook-threads-x-linkedin-2026-11-04.md`, `paste-link-transcript-tools-2026-11-04.md`.

Priority test order (live browser): (1) Adlicio TikTok/IG/Threads/LinkedIn viewers, (2) TikSaveHub TikTok comments (verify or reject the outlier 5,000-free claim), (3) InstaScript + InstagramTranscripts.com (IG transcript, no-key), (4) TTViewer TikTok slideshow + Navid.me IG carousel, (5) Supadata web form (TikTok/IG/FB transcript), (6) ExportComments Facebook free tier, TweetMediaArchive carousel ZIP, TwitterViewer.app/FinchView/GetXAPI (X thread/reply/search), ZocialComment Threads exporter, GetSendable/Connie LinkedIn.

| Still-blocked item | Paste-link browser fallback (docs-claimed, live test queued) | Caveat |
|---|---|---|
| TikTok search | None found as a paste-link search tool; use web-search indexing, then the logged-in browser search UI | Search remains browser/login only |
| TikTok nested reply bodies | TikSaveHub comment downloader (tiksavehub.com/tiktok-comment-downloader, top-level only), ZocialComment (zocialcomment.com/export/tiktok, replies claimed), CommentTok (commenttok.com), ExportTok (export-tok.com), Adlicio comment viewer (tryadlicio.com/tools/comment-viewer, up to 500/pull) | Top-level comments already work no-login via TikWM; nested completeness is untested |
| TikTok slideshows (when gallery-dl/TikWM fail) | TTViewer slideshow downloader (ttviewer.org/tiktok-slideshow-downloader, up to 40 images), TikRapid photo downloader (tikrapid.com/tiktok-photo-downloader), SnapTik family, Klipa (klipa.ai, ZIP + MP4) | Slideshow routes are post-dependent: see self-test note below |
| Instagram comment bodies verbatim | ZocialComment IG exporter (zocialcomment.com/export/instagram, free first 100), Adlicio IG comment viewer (tryadlicio.com/tools/instagram-comment-viewer, free up to 100), Giveaway Ninja comment picker (giveaway.ninja, up to 100, picker not exporter), ExportComments (exportcomments.com, account-gated for full use) | No tool guarantees every nested reply; free tiers cap at 100 |
| Instagram native transcripts | InstaScript (instascript.app, English only, in-browser Whisper), InstagramTranscripts.com (instagramtranscripts.com, 6/hr claimed), TranscriptClip IG (transcriptclip.com/instagram-transcript), Supadata IG web form (supadata.ai/instagram-transcript), Eden IG (eden.so/tools/instagram-transcript-generator, audio-based, TXT only free) | Local Whisper on yt-dlp download already works; these are browser alternatives, not curl routes |
| Facebook posts | No dedicated free post-text viewer found; TweetMediaArchive (tweetmediaarchive.com/free-social-media-downloader-no-signup.html) previews media/carousel as ZIP; Insta FB Viewer (insta-fb-viewer.cooldevint.workers.dev) claims caption + carousel view | Post-text reading remains logged-in browser only |
| Facebook comments | ExportComments Facebook (exportcomments.com/export-facebook-comments, free up to 100/post), FreeCommentPicker (freecommentpicker.com/facebook, 1 draw/day, up to 100, picker not exporter), ZocialComment Facebook (third-party claim only, first 100 free) | No free tool guarantees a full nested thread; caps at 100 |
| Facebook ordered multi-photo slides | TweetMediaArchive (full carousel as one browser-built ZIP, strongest claim), ClipsSaver Facebook photo downloader (clipssaver.com/facebook-photo-downloader, single photos only, not bulk carousel) | Ordered carousel reading remains logged-in browser only if these fail in live test |
| Facebook video transcripts | Supadata FB web form (supadata.ai/facebook-transcript), TranscriptClip FB (transcriptclip.com/facebook-transcript, first transcript free, then paid), ScreenApp FB (screenapp.io/features/facebook-video-transcript, free plan 2x45 min), Downloaders.co video-link-to-text (downloaders.co/video-link-to-text) | yt-dlp auto-subs + local Whisper already work on a supplied URL; discovery is the blocker |
| Threads pagination / full reply trees | ThreadsTools thread reader (threadstools.app, unroll claim, completeness untested), ZocialComment Threads exporter (zocialcomment.com/export/threads, first 100 free, full-set claim untested), Adlicio Threads viewer/comment viewer (tryadlicio.com/tools/threads-viewer, first replies only) | First batch already works no-login via curl_cffi; full trees are browser/login only |
| Threads video transcripts | ScreenApp Threads (screenapp.io/transcription/threads, free plan 2x45 min), Downloaders.co (as above), ReelScribe (reelscribe.app, 40-word preview free) | SSR video_versions + local Whisper already works no-login for a known post URL |
| X keyword search | GetXAPI Twitter viewer search tab (getxapi.com/tools/twitter-viewer, operator search claimed), UnifAPI Twitter viewer (unifapi.com/tools/twitter-viewer, 20 results first page), FinchView (finchview.com, operator search claimed), Postel advanced search (postel.app/twitter-advanced-search, 1 free search/day, up to 20 posts) | FxTwitter search via curl is unresolved (needs a descriptive-UA curl test); these are browser alternatives |
| X full reply trees | TwitterViewer.app (twitterviewer.app, first page of replies free), FinchView (finchview.com, logged-out reply set only), Social Fetch X viewer (socialfetch.dev/tools/twitter-profile-viewer, Load more claimed), FxTwitter conversation API (api.fxtwitter.com, scriptable, first page verified in self-test) | Full/deep trees beyond first page are browser/login only |
| LinkedIn full comment threads | Adlicio LinkedIn viewer (tryadlicio.com/tools/linkedin-viewer, comments returned but explicitly may miss nested/logged-in-only replies), GetSendable comment exporter (getsendable.io/tools/linkedin-comment-exporter, "every comment" claim untested), Connie post engagers (connie.ai/free/linkedin-post-engagers, commenters list) | Post bodies + counts already work no-login via embed; full threads are browser/login only |
| Saveto end to end | Saveto itself, browser-form only: TikTok page (saveto.ai/tiktok-transcript-generator), Instagram page (saveto.ai/instagram-transcript-generator), generic video-to-text (saveto.ai/video-to-text, saveto.ai/ai-transcription). Its API (api-v1.saveto.ai/api/app/workflow/transcript) is Turnstile-gated (probe 403) and is NOT a curl route | Live-browser test queued, exact steps: open the page, paste a known public URL, submit, let Turnstile complete in-browser, read the rendered panel, record timestamp/SRT export or failure mode |
| Generic transcript alternatives (cross-platform) | Supadata web form (supadata.ai, one-off free, no login; API is keyed, excluded), GetTheScript (getthescript.app, 3 short/day free), TokScript (tokscript.com, 5/day with free account), Transcript24 (transcript24.com, no sign-up claimed), VideoToScript.app (videotoscript.app, 3 short/day), Facebook to Transcript (facebooktotranscript.com, ad-funded, Whisper fallback), TranscribeVideo.ai (transcribevideo.ai, first minute free) | Caption-only trap: VexaScribe, TokConnect, TokCaption, 1Lookup, Scrivi free tier return nothing when the platform has no captions; they are not AI transcription |

### Self-test pass 2026-11-04 (every platform x capability, real public URLs, no login, no keys)

Log: `~/workspace/people-research-opensource/selftest-2026-11-04.log`. Script self-tests all pass: `people-research-native.js` 6/6, `transcript-batch.js` 6/6, `local-video-transcribe.py` self-test passes, `reddit-arctic.py doctor` ok. Native smoke on "iphone 17": Bluesky + Hacker News returned results, Reddit RSS route is separate from the native script's blocked RSS check, TikTok search blocked as expected.

| Platform | Discovery | Post/body | Comments | Transcript | Full video understanding | Slideshows | Verdict |
|---|---|---|---|---|---|---|---|
| YouTube | PASS, Piped search returned MKBHD video | PASS, oEmbed title/author | PASS, Piped comments returned real comments | PASS, ytscrape 299 snippets, npm youtube-transcript 299 snippets, yt-dlp Android VTT 19,491 bytes (exact flags: `--write-auto-sub` alone; the `--write-auto-subs + --write-subs` combo fails "Only images available") | PASS, `local-video-transcribe.py` on MKBHD video returned full text after the script fix below | n/a | Working and accessible, with the exact-flag caveat |
| TikTok | FAIL no-login (web-search indexing only; anonymous search captcha-walled) | PASS, SSR/TikWM metadata | PASS, TikWM comment list returned first comment "how about the battery po?" with reply count | PASS, local Whisper via fixed script returned full Taglish transcript | PASS, same fixed-script run | CAVEAT, see below | Working except discovery and nested replies |
| Instagram | FAIL bulk no-login (embed per-post only) | PASS, embed HTML 302,919 bytes with carousel image URLs | FAIL verbatim no-login (embed gives caption + comment count link only) | PASS via fbtotranscript/local Whisper (prior round; re-verified chain via script) | PASS via download + frames + caption (prior round) | PASS with caveat, embed images present, order assumed = app order | Working except comments and bulk discovery |
| Facebook | FAIL no-login (login wall only) | FAIL no-login | FAIL no-login | PASS on a supplied URL, yt-dlp `--list-subs` shows `en_US` automatic SRT | PASS on a supplied URL (prior round download + Whisper) | FAIL ordered no-login (gallery-dl AuthRequired; curl_cffi single-photo gives unordered duplicates) | Browser/login only except video transcripts on a supplied URL |
| Threads | PASS first page, curl_cffi search/tag/profile | PASS, curl_cffi post page 200, 825,209 bytes, 5 `thread_items`, "Mist Blue" present | PASS first batch only (5 thread_items) | PASS, SSR video_versions + local Whisper (prior round, 774 chars) | PASS via SSR mp4 + Whisper (prior round) | n/a | Working with caveat: pagination/full trees browser/login only |
| X | FAIL keyword no-login (`site:x.com` 0; FxTwitter search unresolved) | PASS, oEmbed on real NASA tweet 2113776971603689874 returned full text/author | PASS first page, FxTwitter conversation returned 6 replies + `cursor.bottom` | n/a | n/a | n/a | Working with caveat: search and full trees browser/login only |
| LinkedIn | PASS via web-search indexing (Ruslan post found) | PASS, embed page 27,417 bytes, full body text present ("scratched", "Siri") | FAIL bodies no-login; counts PASS via title rule, but this test post had no count suffix, so `count_unknown` (correct per the rule, not 0) | n/a | n/a | n/a | Working except comment bodies/threads |
| Reddit | PASS, Redlib global search 7 `post_title` results; Arctic sub/thread PASS (thread 1xn8j9w, 20 comments, score 202 in that thread's listing) | PASS, Arctic thread + Redlib thread page | PASS, Arctic comments with scores | n/a | n/a | n/a | Working and accessible; RSS bridge expires Nov 13, 2026; never rank by Arctic fresh scores |
| Bluesky | PASS, SEARCHPOSTS 5 posts | PASS via getPostThread (prior round) | PASS via getPostThread (prior round) | n/a | n/a | n/a | Working and accessible |
| Hacker News | PASS, Algolia 3 hits | PASS, Firebase (prior round) | PASS, Firebase (prior round) | n/a | n/a | n/a | Working and accessible |
| Forums/Q&A | PASS, Stack Exchange search returned items | PASS, WSO/Discourse/SE (prior rounds) | PASS, replies/answers (prior rounds) | n/a | n/a | n/a | Working and accessible |

Fixes applied during this self-test (not just documented):
- `scripts/local-video-transcribe.py`: (1) YouTube subs command changed from `--write-auto-subs --write-subs` to `--write-auto-sub` alone, because the combo failed in this self-test while the single flag returned the exact 19,491-byte VTT; (2) `--no-check-certificates` added to all yt-dlp commands in the script, because this VM's self-signed proxy otherwise fails SSL on both subs and downloads (on a normal network it is unnecessary but harmless for public URLs). After the fix, the script returned status ok with full text for both the TikTok test video and the YouTube MKBHD video. Re-test after the fix is in the log.
- `scripts/reddit-arctic.py`: retry raised from 1 retry to up to 3 attempts with exponential backoff on 422/disconnect/5xx; `doctor` still ok after the change; `py_compile` passes for both scripts.
- Installs fixed during this self-test: gallery-dl 1.32.19, ytscrape v2.2.0, and npm youtube-transcript were NOT installed on this VM at self-test start (bare `yt-dlp` is not on PATH; only `~/workspace/tools/ytdlp-env/bin/yt-dlp` exists). They are now installed into `~/workspace/tools/ytdlp-env` and `~/workspace/tools/yttranscript-npm`, and the Setup section now lists those exact venv paths instead of bare names. A fresh user who only runs `pip install yt-dlp` will fail on PEP 668 systems and will miss the other three tools; the Setup section says so explicitly.

Still failing after fixes, and why they cannot be fixed no-login here:
- TikTok slideshows on a NEW public photo post (`@jcxv.ts/photo/7411023031876750599`): TikWM returned `code:-1, Url parsing is failed`, and gallery-dl returned "Requested post not available" (it rewrites `/photo/` to `/video/`). The prior sweep's different photo post returned 7 slides on both routes. Verdict: TikTok slideshows are **working with a caveat, post-dependent**, not universally fixed; if both routes fail on a post, use the paste-link browser fallback (TTViewer/TikRapid) or the logged-in browser, and do not claim the post is unavailable on the basis of one route.
- TikTok search, Instagram comment bodies, Facebook posts/comments/discovery/ordered slides, Threads pagination, X keyword search/full trees, LinkedIn full threads, Saveto end to end: no no-login fix was found in this or the prior sweeps; they are browser/login fallback only, with paste-link tools above as the first browser step and the logged-in browser as the second. That is the honest end of the no-login road for those items in this pass; the only remaining verification that could change any of them is the queued live-browser paste test for the docs-claimed tools above.
- Native script smoke still reports Reddit and TikTok as blocked: that is the script's own bounded smoke (Reddit RSS 403 in that script, TikTok search), not a verdict on the Arctic/Redlib/TikWM routes above, which were tested separately and pass. Do not "fix" the smoke by conflating the two.

## Transcript coverage

Transcript availability is source-specific. Do not equate metadata or visible captions with a transcript.

| Source | Transcript status | What can be extracted |
| --- | --- | --- |
| YouTube/Shorts | Strong via local bypass chain | `scripts/local-video-transcribe.py` — yt-dlp Android-client subs first, then Invidious timedtext, then `youtube-transcript-batch.py` (now usually `IpBlocked` from this VM), then yt-dlp format-18 download + local faster-whisper; comments via yt-dlp Android client `--write-comments` (5,812 extracted, cap by truncating `.info.json` comments post-hoc; `--max-comments` does NOT exist in yt-dlp 2026.10.26). Discovery via Piped `/search`; Piped `/streams` dead (LOGIN_REQUIRED); fbtotranscript 422s YouTube |
| TikTok | Working, comments + slideshows now no-login | Comments via TikWM `api/comment/list` (20/20, cursor pagination); slideshows via gallery-dl or TikWM `images[]` (7 ordered slides, hashes matching). Transcripts via `scripts/transcript-batch.js` → fbtotranscript, native VTT, or local Whisper (`scripts/local-video-transcribe.py`). Discovery via web-search indexing only; anonymous search captcha-walled; TikTok search and nested reply bodies are browser/login only |
| Instagram/Reels | Working via third-party/local fallback; carousels no-login | `scripts/transcript-batch.js` → fbtotranscript verified 5/5 real reels, or local Whisper. Carousels via embed HTML ordered JPEGs (use full signed URLs). Comment bodies verbatim and native transcripts are browser/login only |
| Facebook/Reels | Video transcripts no-login on a supplied URL; posts/comments session-only | Video captions via yt-dlp `--write-auto-subs --sub-langs en_US` first, then fbtotranscript/local Whisper. oEmbed now tokenless but textless. Post text, comments, discovery, ordered slides are browser/login only |
| Threads | Largely no-login, first page only | Post text, first-batch replies, profile/keyword/tag discovery via curl_cffi Chrome impersonation; video transcript via SSR `video_versions` mp4 + local Whisper. Pagination and full reply trees are browser/login only |
| X | Strong for known URLs; first-page replies no-login | `scripts/x-hydrate-batch.js` — oEmbed batch 7/7 verified; first-page replies via FxTwitter `api.fxtwitter.com/2/conversation/<id>`. No free anonymous keyword search (unresolved, needs a descriptive-UA curl test); discovery via web search or logged-in session; full reply trees are browser/login only |
| LinkedIn | Strong for known URLs; counts via title | `scripts/linkedin-hydrate-batch.js` — embed batch 4/4 verified, full post bodies; comment counts via embed `<title>` (`| N comments`), attribute secondary, else `count_unknown`. Comment bodies and full threads are browser/login only |
| Reddit, Hacker News, Bluesky | Not video-transcript sources | Reddit: Arctic scoped search + Redlib global search (RSS bridge until Nov 13, 2026). Native post/comment text; video transcripts are not assumed |

For any source without a verified transcript path, report `no_native_transcript` and use an approved transcript website only for a tiny high-value shortlist.

Never dump the raw corpus into the main model context.

1. Normalize text locally and preserve source IDs, URLs, timestamps, and offsets.
2. Exact- and near-dedupe before model calls.
3. Extract atomic claims in compact batches.
4. Preserve exact quotes under 40-50 words with source offsets.
5. Cluster claims into themes while keeping dissent separate.
6. Build evidence packets containing theme, support, dissent, counts, and links.
7. Send only evidence packets to the final model.

Each final claim needs a direct source link. Never invent engagement numbers, transcripts, comments, or coverage.

## Quality and stopping rules

Stop when:

- all research questions have multiple independent sources
- new batches add no meaningful themes
- platform diversity and dissent are represented
- the evidence packet is sufficient for a confident answer
- rate limits, CAPTCHA, or missing transcripts make further collection unreliable

Report what was searched, what worked, what failed, and what was not covered. A blocked source is not evidence of no discussion.

## Output format

Return:

1. Bottom line.
2. What people broadly say.
3. Important disagreements and minority views.
4. Platform/source breakdown.
5. Concrete examples and short verbatims.
6. Confidence and coverage gaps.
7. Direct citations grouped by claim.
8. Brief method note with candidate count, deep-source count, and transcript limits. Do not report engagement unless asked.

## Current audit

The file is structurally valid as an Aside skill and has two dependency-free collectors: `scripts/people-research-native.js` for native discovery/text sources and `scripts/transcript-batch.js` for bounded public-URL transcript retrieval. (Rebuilt Sep 24, 2026 — the scripts were missing from disk. Both `--self-test` suites pass 6/6. Live `--smoke --query "Wharton Global High School Investment Competition"`: Bluesky verified (2 results), Reddit verified (4), Hacker News verified (endpoint OK, 0 results for query), TikTok blocked-as-expected with correct classification.) The transcript batcher infers platform, canonicalizes/deduplicates URLs, submits multipart requests to the verified endpoint with concurrency limits and retries, and returns the common transcript schema with text, segments, SRT/VTT, status, and provenance. Browser-session collectors for Instagram discovery, TikTok UI comments, Threads, and Facebook caption controls remain skill-driven because they require the live logged-in page/session.

Alternative-routes pass (Sep 24, 2026): every partial/blocked adapter was re-probed for no-login GitHub/third-party/browser routes, all live-tested from this server. New verified routes: YouTube discovery/transcripts/comments via Piped API (instance rotation on 500s), TikTok native VTT captions with no login, LinkedIn full post bodies via the embed URL, WSO full threads with no login (old "login-gated" label was wrong), Quora via text-reader, Stack Exchange API (no key), Discourse JSON pattern, CollegeVine. `reddit-reading/scripts/reddit.py` was rebuilt on the pullpush.io anonymous API (direct reddit.com is 403 bot-walled from servers; web search surfaced zero reddit.com results on the test topic while the mirror found 4 real threads).

Deep-audit + batch pass (Sep 28, 2026, per user instruction to find alternatives and make batch work): three parallel researchers re-tested every adapter for batch-capable routes, all live from this VM. New batch scripts, all live-verified: `scripts/youtube-transcript-batch.py` (self-hosted youtube-transcript-api, venv `~/workspace/tools/ytapi-env`; Piped `/streams` and all curl-reachable third-party YouTube converters are dead from this VM as of this date), `scripts/x-hydrate-batch.js` (oEmbed, 7/7, no rate limits; X batch search confirmed dead: xcancel 451, nitter gone, guest API unreachable), `scripts/linkedin-hydrate-batch.js` (embed endpoint, 4/4, full bodies + comment counts). `scripts/transcript-batch.js` finally live-tested end to end on real URLs: 3/3 (TikTok + Instagram). Status changes recorded: TikTok native VTT download now network-blocked from this VM (page-fetch caption detection still works; full native path needs the user's own network); Facebook confirmed to have no anonymous batch route at all (oEmbed deprecated, graph oembed returns no text). Reddit `sub` command live-verified; the OAuth placeholder was removed from `reddit.py` (no credentials read or used, by design). The user granted standing approval for third-party transcript processing of public URLs — no per-batch confirmation needed; private/follower-only/sensitive content stays excluded.

### Acceptance matrix for each platform

A platform is `verified` only after a live, current test proves the specific capabilities the workflow needs:

- discovery returns multiple relevant candidates
- canonical URL/ID, author, date, text, and engagement normalize into the common schema
- the body/caption/transcript can be retrieved without prohibited paid services
- comments/replies can be retrieved when the source supports them
- pagination/cursors, rate limits, and empty/block responses are classified correctly
- at least one evidence packet can be produced with a direct link and short source quote

Test each adapter with a small fixture before mass collection. A platform may be `partial` or `blocked`, but the final answer must show that state instead of pretending it is complete.

### Operational readiness

1. Run `--self-test` before a large job, then run a bounded `--smoke --query` probe for the current topic.
2. Prefer native connectors, RSS, JSON, captions, and same-origin browser-session data. Use approved public transcript websites only for a tiny high-value shortlist when native text is unavailable.
3. Persist only normalized evidence or JSONL when repeat runs need saved history. Use the built-in URL normalization, dedupe, ranking, pagination, retry/backoff, and status taxonomy (`verified`, `partial`, `blocked`, `unavailable`, `not_applicable`).
4. For browser-session sources, use the live logged-in page/request shape and current cursors. Never hardcode stale GraphQL IDs, cookies, signing values, or tokens.
5. In every final report, state candidate/deep-source counts, transcript/comment method, direct links, inaccessible sources, platform skew, and cleanup status. Do not include Pinterest or Rumble by default.
6. Treat blocked, rate-limited, empty, and transcript-unavailable results as explicit gaps, never as evidence that nobody discussed the topic.

### Evidence-quality rules

Separate first-hand users, expert analysis, creator/affiliate marketing, brand-owned posts, reposts, bots, likely AI-generated content, and obvious ragebait. Do not treat comment count, virality, or repeated identical wording as consensus. Weight specific first-hand detail and independent author diversity more than raw engagement. State when the sample is platform-skewed, English/US-skewed, recent-only, or too small to generalize.

## Current verification matrix

These are the latest live probes, not assumptions:

| Source | Current result | Runtime level |
| --- | --- | --- |
| YouTube | Native connector returned 5 search results; metadata worked; 4/5 sampled videos exposed caption tracks and transcripts; comments returned. One video correctly reported transcripts disabled. **No-login routes verified Sep 24, 2026:** Piped API discovery (20 on-topic results), `/streams` → timedtext transcripts (flaky per-video, rotate instances), `/comments` working. | Strong; no-login fallback strong with instance-rotation caveat |
| X | Logged-in `@ilikemujeeb` session worked through the native connector; Latest and Top each returned 5 results with cursors. Post text works; video transcripts are not verified. **No-login fallback verified Sep 24, 2026:** web-search discovery + `publish.x.com/oembed` hydration per tweet URL. Nitter and the syndication API are dead (X legal action). | Strong text, video-transcript partial |
| LinkedIn | Added to the workflow through native web search for public posts/articles/profiles, with the logged-in `linkedin` global for known authors and `getUserPosts`. Search-index coverage is not an exhaustive LinkedIn firehose; video transcripts are not verified. **No-login post bodies verified Sep 24, 2026:** `linkedin.com/embed/feed/update/urn:li:activity:{id}` returns full body text. | Bulk discovery partial, text strong |
| Reddit | `scripts/reddit-arctic.py` (Arctic Shift) verified live Nov 4, 2026: `doctor`, `search --sub/--subs`, `thread` (post + comments), `sub`, `user` all return real data; newest-post lag ~30 min. Global keyword search is NOT supported by Arctic (requires author/subreddit); direct reddit.com, `.json`, and `.rss` are all 403 bot-walled from servers. | Partial text via archive; global search missing, fresh scores are ingest snapshots |
| Hacker News | Algolia returned stories; Firebase item lookup exposed child-comment IDs. | Strong |
| Bluesky | Uppercase `app.bsky.feed.SEARCHPOSTS` returned 5 posts; `getPostThread` returned a thread. Lowercase path returned 403, so retain the fallback. | Strong text; not a video-transcript source |
| TikTok | Search HTML returned video IDs; known-video SSR exposed metadata and `subtitleInfos`; direct VTT returned a 1,472-character transcript; the unified Facebook-to-Transcript endpoint returned 1,477 characters across 15 timestamped segments; logged-in UI showed comments and visible replies. **Verified Sep 24, 2026:** native VTT caption route works from server with no login; anonymous search is captcha-walled (use web-search discovery). | Strong native and website transcript paths, bulk/comment API partial |
| Instagram | Logged-in session returned 24 hashtag post links; a Reel exposed caption, metadata, engagement, and visible comments. The unified Facebook-to-Transcript endpoint returned 473 characters across 9 timestamped segments after the native page exposed no text track. No clean no-login bulk route found (embed needs browser render; viewer sites shallow). | Strong UI and website transcript path, native bulk partial |
| Threads | Logged-in session loaded; search produced Top/Recent/Profiles and post text, authors, dates, likes, replies, reposts, and shares. No native video-transcript path was verified. | Strong discovery, reply-body/transcript partial |
| Facebook | Logged-in search returned public groups/posts and Reels. The unified Facebook-to-Transcript endpoint returned 83 characters across 2 timestamped segments for a public Watch video. Native `Captions` controls remain conditional. **No anonymous server route exists (verified Sep 24, 2026)** — session-only. | Strong UI and website transcript path, pagination partial |
| Forums/Q&A | **Verified Sep 24, 2026:** WSO thread pages fetch directly (full OP + replies, no login); Quora via text-reader (full answers); Stack Exchange API no-key (`filter=withbody`); Discourse `/search.json` + `/t/{id}.json` pattern; CollegeVine Q&A. | Strong text; source-dependent |

### How the final workflow should use this matrix

- Run strong sources in parallel for discovery and text evidence.
- Use logged-in session adapters for TikTok, Instagram, Threads, and Facebook.
- If the user approves third-party processing, use the verified transcript batcher for high-value public URLs, capped by concurrency and deduplicated per batch.
- Use approved public transcript websites or mark the transcript unavailable.
- Keep source status per result: `verified`, `partial`, `blocked`, `no_native_transcript`, or `rate_limited`.
- A platform's UI working does not automatically prove its hidden bulk endpoint works. Keep discovery, detail, transcript, comments, pagination, and cleanup as separate tests.

## Adapter hardening rules

### TikTok

- Discovery: use the native search page/hydration payload for candidate IDs before using signed endpoints.
- Detail: parse `__UNIVERSAL_DATA_FOR_REHYDRATION__` and fetch `subtitleInfos` VTT URLs directly.
- Comments: prefer the logged-in page/session request path; otherwise use a fresh signed request with current cookies and matching User-Agent.
- Pagination: persist the returned cursor/token per query, stop on repeated cursors, and classify 403/429/empty responses separately.
- Never reuse stale `msToken`, `X-Bogus`, `X-Gnarly`, or operation IDs across sessions.

### Instagram

- Discovery: use the logged-in hashtag/search page and extract canonical `/p/` links, then deduplicate.
- Detail: read caption, author, date, engagement, media type, and visible comments from the same-origin page or a request captured from that page.
- Pagination: use the current page's cursor/request shape; do not hardcode old query hashes or doc IDs as permanent APIs.
- Transcripts: first inspect native caption text and the live page. If no native text exists, use the approved Saveto public-URL fallback for a few high-value public Reels or mark `no_native_transcript`.
- Rate limits: pace requests, cap repeated authors, and stop after 429/checkpoint signals instead of retrying aggressively.

### Threads

- Discovery: use the logged-in Search UI's Top, Recent, and Profiles views. Search currently returns usable post text, author, dates, engagement, and reply counts.
- Detail/replies: capture the current same-origin request or open the post through the SPA; preserve reply cursors and stop on repeated/empty pages.
- Do not rely on stale GraphQL doc IDs. If the SPA returns a home page or indefinite loading, classify the result as `session_or_route_unavailable` and continue with other sources.

### Facebook

- Do not attempt collection until the user has completed login in the opened Facebook tab.
- After login, verify home/session state first, then capture live `fb_dtsg`, `lsd`, `jazoest`, and current GraphQL operation IDs from the page/bundles.
- Test Page search, public post detail, comments, and group visibility separately. Never assume access to arbitrary user posts.
- Refresh tokens/operation IDs per session and never store cookie values or secrets in the skill, cache, logs, or evidence packets.

### LinkedIn

- Bulk discovery uses native web search, not a brittle hidden LinkedIn firehose. Search several query variants, paginate available result pages, keep public LinkedIn URLs, and deduplicate canonical post/article/profile URLs.
- Use `webfetch` for readable public result pages and the logged-in `linkedin` global for known profiles, companies, and `getUserPosts`.
- Extract text posts/articles, author, date, URL, reactions/comments when visible, and whether the result is public or login-gated.
- Do not claim exhaustive LinkedIn coverage. Search-index results miss unindexed, private, feed-only, and comment-only content.
- LinkedIn video transcripts are `no_native_transcript` unless a visible caption or transcript is actually present. Do not treat video metadata as transcript evidence.

## Repeatable native collector

Script: `scripts/people-research-native.js`

When Bash is available:

```sh
node skills/user/people-research/scripts/people-research-native.js --self-test
node skills/user/people-research/scripts/people-research-native.js --smoke --query "ai agents"
```

The smoke command performs bounded native probes against Bluesky, Hacker News, Reddit RSS, and TikTok search. It stays text-only, writes no credentials, and invokes no paid APIs. Use the returned cursors for subsequent Bluesky pages and the `page` parameter for subsequent Hacker News pages. Browser-session sources remain in the logged-in browser workflow and must use their live cursors/request shapes rather than stale hardcoded IDs.

## Repeatable transcript batcher

Script: `scripts/transcript-batch.js`

This is the transcript-focused path. It submits public Instagram, TikTok, Facebook, or YouTube URLs to the verified `fbtotranscript.com/api/transcript` endpoint, with platform inference, canonical URL dedupe, bounded concurrency, retry handling, timestamped segments, SRT/VTT, and provenance fields. It does not require browser tabs and never accepts private URLs or credentials.

When Node is available:

```sh
node skills/user/people-research/scripts/transcript-batch.js --self-test
node skills/user/people-research/scripts/transcript-batch.js --urls "https://www.instagram.com/p/...,https://www.tiktok.com/@.../video/...,https://www.facebook.com/watch/?v=..."
```

Use concurrency 3 by default and never treat the website as an unlimited or permanent API. Keep the batch to public high-value winners, preserve failures per URL, and report the service/method used. Ask for one confirmation for the batch before submitting any URLs; after approval, do not re-ask for individual URLs unless the destination or scope materially changes.

## Re-probe 2026-11-04 (open-source prep, no-login-first)

Tested from the VM, sequential, no keys, no login, public URLs only. Full matrix is in the open-source draft README.

- Self-tests: `people-research-native.js` 6/6, `transcript-batch.js` 6/6. Native smoke "ai agents": Bluesky verified (10), Hacker News verified (10), Reddit blocked (0), TikTok blocked (0).
- Bluesky discovery: lowercase `searchPosts` on public.api.bsky.app can 403; the uppercase `SEARCHPOSTS` fallback in `people-research-native.js` is what works — do not drop it.
- YouTube: Piped search (with `filter=videos`) and Piped comments verified; Piped streams bot-blocked (`LOGIN_REQUIRED`) and the venv transcript script returned `IpBlocked` tonight. Treat YouTube transcripts from this IP as cooldown-dependent, not always-on.
- X oEmbed: verified 2/2 for known tweet URLs (snippet text, author, date; no replies). Discovery via `site:x.com` returned 0 results tonight — discovery is the weak link.
- Reddit: REGRESSION. `reddit.py` doctor reported pullpush.io HTTP 521 and search timed out, vs verified Sep 28. Treat Reddit as degraded/blocked until pullpush recovers; fallback is web-search indexing (`site:reddit.com`).
- Reddit RESTORED (partial) Nov 4, 2026: new adapter `scripts/reddit-arctic.py` on the Arctic Shift API (arctic-shift.photon-reddit.com, no key) — `doctor`, `sub`, `search --sub/--subs`, `thread`, `user` all live-verified with real data. NOT a full restoration: Arctic has no global cross-subreddit keyword search, keyword queries must be time-windowed, and fresh scores/counts are ingest snapshots. See the Reddit section above for the full limits. pullpush.io still HTTP 521; direct reddit.com/`.json`/`.rss` all 403 from servers.
- Instagram: correction — `/reel/<id>/embed/captioned/` raw HTML contained caption text for the tested reel, so the "JS-DOM-only" note is overstated. Comments remain session-only. Instagram transcript via fbtotranscript failed twice with upstream 502 tonight (vs 5/5 in Sep) — flaky, retry later, do not call it dead.
- TikTok: transcript via fbtotranscript verified again (5,475 chars, 106 segments) on a caption-less video; unsigned comment API still session-only (error envelope); anonymous search still captcha-walled.
- Facebook: post text still session-only (mbasic error, oEmbed deprecated 400, graph oembed = embed div only); video transcript via fbtotranscript verified (685 chars).
- Threads: direct page curl is a JS shell; post/replies need a logged-in browser render. Search-index snippets can surface post text.
- LinkedIn: hydrate batch verified 2/2 full bodies (2,023 and 1,121 chars); comment bodies still signup-gated.
- Script fix 2026-11-04: `youtube-transcript-batch.py` now handles `--help` before importing and exits with a clear missing-package message on system Python instead of a traceback. It still requires `youtube-transcript-api` (pip install, or the project venv).

### Local bypass verification 2026-11-04 (yt-dlp + local Whisper, free, no login)

New preferred entry point for video transcripts: `scripts/local-video-transcribe.py` (self-test passes; live-verified end to end on real public videos). It runs sequentially, never passes cookies/credentials to yt-dlp (public content only), and returns the common transcript schema plus extracted frame paths.

- YouTube chain, in order: (1) yt-dlp subtitles with `--extractor-args youtube:player_client=android` — the default web client is bot-blocked from this VM ("Sign in to confirm you're not a bot") but the Android client is NOT: 19 KB VTT, 10,998 chars / 151 segments on MKBHD "iPhone 17 Review: No Asterisks!" (`rng_yUSwrgU`) in ~4 s. A second video (`GfDm2xC_sws`) legitimately had no English subtitles under the same command — a real no-subs result, not a failure. (2) Invidious timedtext — only `yt.chocolatemoo53.com` served `/api/v1/captions` (88.7 KB VTT, ~33k raw chars on the same MKBHD video); `inv.nadeko.net` 502s, `yewtu.be` returns frontend HTML, other listed instances unreachable, so rotation is effectively single-instance and fragile. (3) `youtube-transcript-batch.py` — still `IpBlocked` from this VM on the same video tonight, so it is now step 3, not step 1; `ip_blocked` no longer ends the job, the chain continues to local Whisper. (4) Local Whisper: Android-client format 18 (360p mp4 + audio, the only format the Android client exposes for that video) downloaded 33 MB / 680 s in 34 s, then faster-whisper transcribes locally.
- Piped timedtext still dead: `/streams` on `api.piped.private.coffee` returns HTTP 500 `SignInConfirmNotBotException` / LOGIN_REQUIRED; other instances 502/timeout/HTML-shell. Piped search and comments still work (search verified again tonight).
- YouTube comments via yt-dlp Android client work: `--write-comments` extracted 5,812 comments into `.info.json` on the MKBHD video (took ~10 min of pagination — cap by truncating `.info.json` comments post-hoc; `--max-comments` does NOT exist in yt-dlp 2026.10.26 for research use; the default client is bot-blocked for comments too).
- Instagram / TikTok / Facebook, download + local Whisper + frames, all live-verified on real public URLs: IG carousel post `instagram.com/p/DdXJ5sHEjuN/` (video item 18.7 s, 2.8 MB; photo slides in the same post report "No video formats found" and are skipped), TikTok `@harvey1e9/video/7644390876655013150` (99.5 s, 10.5 MB in ~5 s — TikTok CDN video download works from this VM, unlike the old native-VTT sidecar block), Facebook `facebook.com/watch/?v=452917150558324` (485.7 s, 15 MB in ~9 s). Whisper base/int8 on CPU via `~/workspace/tools/whisper-env` (model cached, `HF_HUB_OFFLINE=1`): IG 377 chars / 5 segs in 4.1 s, TikTok 1,226 chars / 33 segs in 13.9 s, FB 6,940 chars / 201 segs in 111.8 s — total 130.8 s for 604 s of video (~4.6x realtime). Cross-check: local Whisper text matches fbtotranscript on all three videos to within a few chars (IG 377 vs 379, TikTok 1,226 vs 1,225, FB 6,940 vs 6,741).
- Whisper environment gotchas: system Python's faster-whisper is broken against its PyAV (`TypeError: metadata_errors`) — always use `~/workspace/tools/whisper-env/bin/python`. The venv tries to phone home to HuggingFace unless `HF_HUB_OFFLINE=1` is set and/or a cached snapshot path is passed; the sandbox proxy env breaks that lookup (`httpx.InvalidURL` on the proxy port). The script handles both.
- fbtotranscript re-test tonight: 3/3 first attempt, no 502s (IG 379 chars / 2 segs, TikTok 1,225 / 16, FB 6,741 / 121, 32 s total) — the Nov 4 502 flakiness did not recur, but keep retry-with-backoff; it remains the cheaper first try for IG/TikTok/FB before local download.
- Saveto: NOT re-verified end to end. Its transcript pages are alive (HTTP 200) but the form is JS-driven with no discoverable API endpoint in static HTML, so it needs a live-browser check (paste URL, submit, read result) — do not claim Saveto works from curl. It stays a browser-only backup.
- Tooling: yt-dlp 2026.10.26 installed in venv `~/workspace/tools/ytdlp-env` (system pip is PEP 668 externally-managed, so plain `pip install yt-dlp` fails; use the venv). ffmpeg is system-installed. Frame extraction verified 5/5 frames on all three test videos (`ffmpeg -vf fps=N/duration`).
- For IG/TikTok/FB the script goes straight to download + Whisper; fbtotranscript (`transcript-batch.js`) stays the cheaper first try for those platforms when only text is needed.

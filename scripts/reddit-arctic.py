#!/usr/bin/env python3
"""
reddit-arctic.py — Reddit reader backed by the Arctic Shift archive API.
Stdlib only. No login, no key, no posting, no voting.

Replaces reddit.py (pullpush.io backend) while pullpush is down:
pullpush returned HTTP 521 on 2026-11-04 and its search timed out.
Arctic Shift base (verified live 2026-11-04 from this VM):
  https://arctic-shift.photon-reddit.com/api
NOT search.arctic-shift.com / api.arctic-shift.com — both 521 from this VM.
Docs: https://github.com/arthurheitmann/arctic_shift/blob/HEAD/api/README.md

Commands (same shape as reddit.py):
  python3 reddit-arctic.py doctor
  python3 reddit-arctic.py sub NAME [--sort new|top] [--limit N] [--json]
  python3 reddit-arctic.py search "q" --sub NAME [--subs A,B] [--limit N]
      [--days N] [--json]
  python3 reddit-arctic.py thread URL-or-ID [--limit N] [--json]
  python3 reddit-arctic.py user NAME [--limit N] [--json]

Hard limits of this backend (do not work around by guessing):
  * NO global cross-subreddit keyword search. Arctic's `query`/`title`/
    `selftext`/`body` parameters REQUIRE `author` or `subreddit` (HTTP 400
    otherwise). `search` without --sub/--author therefore fails with a clear
    message. Use --subs A,B to fan out over known subs, or discover a thread
    URL via search-engine indexing and hydrate it with `thread`.
  * Keyword searches MUST be time-windowed: pass --days (default 30) so the
    adapter sends `after=<unix>`. Unwindowed keyword queries on busy subs
    return HTTP 422 "Timeout. Maybe slow down a bit".
  * `sort` is date order only (asc/desc). --sort top is done client-side by
    score, and scores are ingest snapshots: posts <~36h old read score=1,
    num_comments=0. Do not treat fresh scores/counts as real.
  * Pagination: before=<created_utc of last item> (date cursor, not a token).
    The adapter does single-page fetches; callers page with --before.
  * `permalink` is NOT a valid Arctic field — permalinks are rebuilt as
    https://www.reddit.com/r/<sub>/comments/<id>/ (slug omitted, still valid).
  * No uptime guarantee (project's own words). On 422/5xx, wait and retry once.

Polite by default: ~1 request per second, up to 3 attempts with exponential backoff on 429/422/5xx/disconnect. On repeated 422, fall back to Redlib global search (safereddit.com/search) and hydrate via Arctic ids/comments.
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://arctic-shift.photon-reddit.com/api"
UA = {"User-Agent": "reddit-arctic-skill/1.0 (research; contact: none)"}
MIN_INTERVAL = 1.0
_last_req = 0.0

POST_FIELDS = "id,subreddit,author,created_utc,title,selftext,score,num_comments,url"
COMMENT_FIELDS = "id,subreddit,author,created_utc,body,score,link_id,parent_id"


def _polite():
    global _last_req
    wait = MIN_INTERVAL - (time.time() - _last_req)
    if wait > 0:
        time.sleep(wait)


def _get(path, params):
    _polite()
    params = {k: v for k, v in params.items() if v is not None}
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    # Retry up to 3x with exponential backoff on 422/disconnect/5xx (2026-11-04:
    # Arctic posts-query is flaky/overloaded, not deterministically dead).
    # On repeated 422, callers should fall back to Redlib global search
    # (safereddit.com/search) and hydrate threads via Arctic ids/comments.
    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                global _last_req
                _last_req = time.time()
                return json.load(r)
        except urllib.error.HTTPError as e:
            body = e.read(400).decode("utf-8", "replace")
            if e.code in (429, 422, 500, 502, 503, 504) and attempt < 2:
                time.sleep(5 * (2 ** attempt))
                continue
            last_err = f"HTTP {e.code}: {body[:200]}"
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(3 * (2 ** attempt))
                continue
            last_err = f"{type(e).__name__}: {e}"
            break
    raise RuntimeError(f"arctic-shift request failed ({url.split('?')[0]}): {last_err}")


def _permalink(sub, sid):
    return f"https://www.reddit.com/r/{sub}/comments/{sid}/"


def _post_items(data):
    return [{
        "id": s.get("id"),
        "title": s.get("title"),
        "author": s.get("author"),
        "subreddit": s.get("subreddit"),
        "score": s.get("score"),
        "num_comments": s.get("num_comments"),
        "created_utc": s.get("created_utc"),
        "selftext": (s.get("selftext") or "")[:2000],
        "url": s.get("url") or _permalink(s.get("subreddit"), s.get("id")),
        "permalink": _permalink(s.get("subreddit"), s.get("id")),
    } for s in data.get("data", [])]


def _comment_items(data):
    return [{
        "id": x.get("id"),
        "author": x.get("author"),
        "score": x.get("score"),
        "created_utc": x.get("created_utc"),
        "body": x.get("body") or "",
        "link_id": x.get("link_id"),
        "parent_id": x.get("parent_id"),
        "subreddit": x.get("subreddit"),
    } for x in data.get("data", [])]


def _window(args):
    """Default keyword window: last `days` days, as unix `after`."""
    if getattr(args, "after", None):
        return args.after
    days = getattr(args, "days", 30) or 30
    return int(time.time()) - days * 86400


def _emit(obj, args):
    if args.json:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
        return
    if isinstance(obj, dict) and "post" in obj:
        p = obj["post"] or {}
        print(f"# {p.get('title')}\nr/{p.get('subreddit')} u/{p.get('author')} "
              f"score={p.get('score')}\n{p.get('permalink')}\n")
        if p.get("selftext"):
            print(p["selftext"][:1500] + "\n")
        print(f"--- {len(obj['comments'])} comments ---")
        for cm in obj["comments"]:
            print(f"\nu/{cm['author']} ({cm['score']}):\n{cm['body'][:800]}")
        return
    for it in obj:
        print(f"- {it.get('title')}\n  r/{it.get('subreddit')} u/{it.get('author')} "
              f"score={it.get('score')} comments={it.get('num_comments')}\n  {it.get('permalink')}")
        if it.get("selftext"):
            print("  " + it["selftext"][:300].replace("\n", " ") + "...")
        print()


def cmd_doctor(_args):
    out = {"backend": "arctic-shift.photon-reddit.com", "auth": "anonymous",
           "oauth": "not_implemented_no_credentials_used"}
    try:
        d = _get("/posts/search", {"subreddit": "technology", "limit": 1,
                                   "sort": "desc", "fields": "id,title"})
        out["status"] = "ok" if d.get("data") else "degraded"
        out["note"] = "arctic-shift reachable"
    except RuntimeError as e:
        out["status"] = "error"
        out["note"] = str(e)[:200]
    print(json.dumps(out, indent=2))


def cmd_sub(args):
    params = {"subreddit": args.name, "limit": args.limit, "sort": "desc",
              "fields": POST_FIELDS}
    if args.before:
        params["before"] = args.before
    items = _post_items(_get("/posts/search", params))
    if (args.sort or "new").lower() == "top":
        items.sort(key=lambda x: (x.get("score") or 0), reverse=True)
    _emit(items, args)


def cmd_search(args):
    subs = []
    if args.subs:
        subs = [s.strip() for s in args.subs.split(",") if s.strip()]
    elif args.sub:
        subs = [args.sub]
    if not subs and not args.author:
        print("error: arctic-shift has no global keyword search: `query` requires "
              "--sub, --subs, or --author. Example: search \"ai agents\" "
              "--subs technology,MachineLearning,artificial --days 30",
              file=sys.stderr)
        sys.exit(2)
    items = []
    for sub in subs or [None]:
        params = {"q": None, "query": args.query, "limit": args.limit,
                  "sort": "desc", "fields": POST_FIELDS,
                  "after": _window(args)}
        if sub:
            params["subreddit"] = sub
        if args.author:
            params["author"] = args.author
        if args.before:
            params["before"] = args.before
        try:
            items.extend(_post_items(_get("/posts/search", params)))
        except RuntimeError as e:
            print(f"warning: sub r/{sub} failed: {e}", file=sys.stderr)
    items.sort(key=lambda x: (x.get("created_utc") or 0), reverse=True)
    _emit(items[:args.limit] if subs and len(subs) > 1 else items, args)


def cmd_thread(args):
    m = re.search(r"/comments/([a-z0-9]+)", args.target, re.I)
    sid = m.group(1) if m else args.target.strip()
    sid = sid[3:] if sid.lower().startswith("t3_") else sid
    d = _get("/posts/ids", {"ids": sid, "fields": POST_FIELDS})
    post = None
    if d.get("data"):
        post = _post_items(d)[0]
    c = _get("/comments/search", {"link_id": f"t3_{sid}", "limit": args.limit,
                                  "sort": "desc", "fields": COMMENT_FIELDS})
    comments = _comment_items(c)
    if post is None and comments:
        post = {"id": sid, "title": "(title unavailable via arctic-shift)",
                "author": None, "subreddit": comments[0].get("subreddit"),
                "score": None, "selftext": "",
                "permalink": _permalink(comments[0].get("subreddit"), sid),
                "note": "post lookup returned nothing; comments still retrieved"}
    _emit({"post": post, "comments": comments}, args)


def cmd_user(args):
    params = {"author": args.name, "limit": args.limit, "sort": "desc",
              "fields": POST_FIELDS}
    if args.before:
        params["before"] = args.before
    _emit(_post_items(_get("/posts/search", params)), args)


def main():
    import argparse
    p = argparse.ArgumentParser(prog="reddit-arctic.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    q = sub.add_parser("sub"); q.add_argument("name")
    q.add_argument("--sort", default="new"); q.add_argument("--limit", type=int, default=10)
    q.add_argument("--before", default=None); q.add_argument("--json", action="store_true")
    q = sub.add_parser("search"); q.add_argument("query"); q.add_argument("--sub")
    q.add_argument("--subs", default=None, help="comma-separated subreddits to fan out over")
    q.add_argument("--author", default=None)
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--days", type=int, default=30, help="keyword window in days (default 30)")
    q.add_argument("--after", default=None, help="unix timestamp or date, overrides --days")
    q.add_argument("--before", default=None); q.add_argument("--json", action="store_true")
    q = sub.add_parser("thread"); q.add_argument("target")
    q.add_argument("--limit", type=int, default=20); q.add_argument("--json", action="store_true")
    q = sub.add_parser("user"); q.add_argument("name")
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--before", default=None); q.add_argument("--json", action="store_true")
    args = p.parse_args()
    try:
        {"doctor": cmd_doctor, "sub": cmd_sub, "search": cmd_search,
         "thread": cmd_thread, "user": cmd_user}[args.cmd](args)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

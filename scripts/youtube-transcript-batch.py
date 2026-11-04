#!/usr/bin/env python3
"""
youtube-transcript-batch.py (people-research skill: self-hosted, no key, no login)
Batch YouTube transcripts via youtube-transcript-api (no key, no login).

Rate-limit reality on this VM (measured 2026-09-28):
- YouTube allows ~1 transcript fetch per ~60s from this IP.
- Bursts (>~3 rapid requests) trigger IpBlocked; block lifts after ~60-90s cooldown.
- Throughput: ~40-60 videos/hour. Sequential only. No concurrency.

Chain note (2026-11-04): this script is now step 3 of the YouTube chain in
scripts/local-video-transcribe.py, after yt-dlp Android-client subtitles and
Invidious timedtext, and before local faster-whisper. From this VM it is
IpBlocked more often than not; local-video-transcribe.py treats ip_blocked
as "continue to Whisper", not as a batch-ending failure.

Usage:
    ~/workspace/tools/ytapi-env/bin/python youtube-transcript-batch.py <VIDEO_ID> [<VIDEO_ID> ...]
    ~/workspace/tools/ytapi-env/bin/python youtube-transcript-batch.py --self-test

Output: JSON array of { video_id, url, status, text, segments, provenance, error? }
Status: ok | no_transcript | error | ip_blocked
"""
import json, sys, time, datetime

INTER_REQUEST_DELAY_S = 65  # measured safe spacing on this VM's IP

def fetch_one(api, video_id):
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, IpBlocked,
    )
    try:
        t = api.fetch(video_id)
        segs = [{"text": s.text, "start": s.start, "duration": s.duration} for s in t]
        return {
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "status": "ok",
            "text": " ".join(s.text for s in t),
            "segments": segs,
            "provenance": {
                "service": "youtube-transcript-api",
                "method": "fetch (timedtext)",
                "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        }
    except IpBlocked:
        return {"video_id": video_id, "status": "ip_blocked",
                "error": "YouTube IpBlocked: cooldown 90s+ then retry"}
    except (TranscriptsDisabled, NoTranscriptFound):
        return {"video_id": video_id, "status": "no_transcript",
                "error": "no captions available for this video"}
    except VideoUnavailable:
        return {"video_id": video_id, "status": "error",
                "error": "video unavailable/private/deleted"}
    except Exception as e:
        return {"video_id": video_id, "status": "error",
                "error": f"{type(e).__name__}: {str(e)[:200]}"}

def main(argv):
    if argv[:1] in (["--help"], ["-h"]):
        print(__doc__.strip())
        print("\nRequires: youtube-transcript-api (install: pip install youtube-transcript-api,")
        print("or use the project's venv, e.g. ~/workspace/tools/ytapi-env/bin/python).")
        print("System Python without that package will fail with a clear error below.")
        return
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("ERROR: youtube_transcript_api is not installed for this Python.", file=sys.stderr)
        print("Install it with: pip install youtube-transcript-api", file=sys.stderr)
        print("or run with the project's venv, e.g.: ~/workspace/tools/ytapi-env/bin/python youtube-transcript-batch.py <VIDEO_ID>", file=sys.stderr)
        sys.exit(2)
    api = YouTubeTranscriptApi()
    if argv[:1] == ["--self-test"]:
        r = fetch_one(api, "dkfomIeInLA")
        print(json.dumps({"self_test": r["status"] == "ok", "detail": r}, indent=1)[:600])
        return
    ids = [a for a in argv if not a.startswith("-")]
    out = []
    for i, vid in enumerate(ids):
        out.append(fetch_one(api, vid))
        if out[-1]["status"] == "ip_blocked":
            break  # stop the batch; caller should wait and resume
        if i < len(ids) - 1:
            time.sleep(INTER_REQUEST_DELAY_S)
    print(json.dumps(out, indent=1))

if __name__ == "__main__":
    main(sys.argv[1:])

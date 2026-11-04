#!/usr/bin/env python3
"""
local-video-transcribe.py (people-research skill: free local bypass, no key, no login)

End-to-end transcript + frames for a public video URL, without paid APIs.
Never passes cookies/credentials to yt-dlp, so it only ever sees public content.
Public URLs only. Sequential only (one URL at a time).

Chain (YouTube):
  1. yt-dlp subtitles with the Android player client
     (default web client is bot-blocked from this VM: "Sign in to confirm
     you are not a bot"; the Android client bypasses it for subtitles).
  2. Invidious timedtext captions (instance rotation; only
     yt.chocolatemoo53.com served the captions API on 2026-11-04).
  3. Self-hosted youtube-transcript-api (scripts/youtube-transcript-batch.py).
     From this VM this is IP-blocked more often than not (IpBlocked);
     on ip_blocked the chain continues to local Whisper instead of stopping.
  4. Local Whisper: yt-dlp downloads the video (YouTube Android client only
     exposes format 18, 360p mp4 with audio) and faster-whisper transcribes
     it locally (whisper-env venv, cached model, HF_HUB_OFFLINE=1).
     System Python's faster_whisper is broken against its installed PyAV
     (TypeError: metadata_errors) -- use the whisper-env venv.

Chain (Instagram / TikTok / Facebook):
  No subtitle sidecar exists, so go straight to step 4 (download + local
  Whisper). The cheaper first try for these platforms is still
  scripts/transcript-batch.js (fbtotranscript); use this script when that
  service fails or when frames are also needed.

Frames: ffmpeg extracts N frames spread across the video duration
(default 5) for video-understanding. Only written when media was downloaded.

Usage:
    python3 local-video-transcribe.py --urls "https://...,https://..."
    python3 local-video-transcribe.py <URL> [<URL> ...]
    python3 local-video-transcribe.py --urls "..." --model small --frames 3
    python3 local-video-transcribe.py --self-test   # offline parser checks
    python3 local-video-transcribe.py --urls "..." --workdir /tmp/vt --keep-media

Output: JSON array of { url, platform, status, text, segments, frames,
        provenance: { service, method, fetched_at }, error? }
Status: ok | no_transcript | error | bot_blocked

Environment overrides:
    YTDLP_BIN        default: ~/workspace/tools/ytdlp-env/bin/yt-dlp, else PATH
    WHISPER_PY       default: ~/workspace/tools/whisper-env/bin/python, else sys.executable
    WHISPER_MODEL    default: base (tiny/small/base/medium cached locally)
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

HOME = os.path.expanduser("~")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
YTAPI_SCRIPT = os.path.join(SCRIPTS_DIR, "youtube-transcript-batch.py")
INVIDIOUS_INSTANCES = [
    "https://yt.chocolatemoo53.com",  # only instance serving captions API, 2026-11-04
    "https://inv.nadeko.net",         # 502 on captions, 2026-11-04
    "https://yewtu.be",               # frontend HTML only, no API, 2026-11-04
]


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def find_ytdlp():
    override = os.environ.get("YTDLP_BIN")
    if override and os.path.exists(override):
        return override
    venv_bin = os.path.join(HOME, "workspace/tools/ytdlp-env/bin/yt-dlp")
    if os.path.exists(venv_bin):
        return venv_bin
    for cand in ("yt-dlp", os.path.join(HOME, ".local/bin/yt-dlp")):
        if "/" in cand and os.path.exists(cand):
            return cand
        if "/" not in cand:
            import shutil
            if shutil.which(cand):
                return cand
    return None


def find_whisper_py():
    override = os.environ.get("WHISPER_PY")
    if override and os.path.exists(override):
        return override
    venv_py = os.path.join(HOME, "workspace/tools/whisper-env/bin/python")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable


def infer_platform(raw):
    try:
        from urllib.parse import urlparse
        host = urlparse(raw).hostname or ""
    except Exception:
        return None
    host = host.lower().replace("www.", "").replace("m.", "")
    if "youtube.com" in host or host == "youtu.be":
        return "youtube"
    if "instagram.com" in host:
        return "instagram"
    if "tiktok.com" in host:
        return "tiktok"
    if "facebook.com" in host or host == "fb.watch":
        return "facebook"
    return None


def youtube_id(raw):
    from urllib.parse import urlparse, parse_qs
    u = urlparse(raw)
    if u.hostname and "youtu.be" in u.hostname:
        return u.path.strip("/")
    q = parse_qs(u.query).get("v")
    if q:
        return q[0]
    m = re.search(r"/(?:shorts|embed|live)/([\w-]{6,})", u.path)
    return m.group(1) if m else None


# ---------------- VTT parsing ----------------

def vtt_to_segments(vtt_text):
    """Parse WEBVTT into [{text, start, duration}]; dedupes consecutive repeats
    (auto-generated captions repeat each cue). Times in seconds."""
    segments = []
    cue_re = re.compile(
        r"(\d+):(\d+):(\d+)[.,](\d+)\s*-->\s*(\d+):(\d+):(\d+)[.,](\d+)")

    def to_sec(h, m, s, ms):
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    cur = None
    for line in vtt_text.splitlines():
        line = line.strip()
        m = cue_re.search(line)
        if m:
            if cur and cur["text"]:
                segments.append(cur)
            g = m.groups()
            cur = {"text": "", "start": to_sec(*g[0:4]),
                   "duration": to_sec(*g[4:8]) - to_sec(*g[0:4])}
            continue
        if cur is None:
            continue
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if line.isdigit():
            continue
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean:
            cur["text"] = (cur["text"] + " " + clean).strip() if cur["text"] else clean
    if cur and cur["text"]:
        segments.append(cur)
    deduped = []
    for seg in segments:
        if not deduped or deduped[-1]["text"] != seg["text"]:
            deduped.append(seg)
    return deduped


def segments_to_text(segments):
    return " ".join(s["text"] for s in segments)


# ---------------- chain steps ----------------

def run(cmd, timeout=180):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"


def yt_subs_via_ytdlp(ytdlp, video_id, workdir):
    """Step 1: yt-dlp Android-client subtitles. Returns (status, segments, err)."""
    if not ytdlp:
        return "error", [], "yt-dlp not installed (venv ~/workspace/tools/ytdlp-env)"
    url = f"https://www.youtube.com/watch?v={video_id}"
    # NOTE 2026-11-04 self-test: --write-auto-subs + --write-subs together fails
    # ("Only images are available for download"); --write-auto-sub alone works.
    # --no-check-certificates is load-bearing on this VM's self-signed proxy;
    # on a normal network it is unnecessary but harmless for public URLs.
    cmd = [ytdlp, "--no-check-certificates",
           "--extractor-args", "youtube:player_client=android",
           "--write-auto-sub", "--sub-langs", "en",
           "--skip-download", "--no-warnings", "--no-playlist",
           "-o", os.path.join(workdir, "%(id)s"), url]
    rc, out, err = run(cmd, timeout=120)
    blob = out + err
    if "Sign in to confirm" in blob:
        return "bot_blocked", [], "yt-dlp bot check on all clients"
    vtts = sorted(glob.glob(os.path.join(workdir, f"{video_id}*.vtt")))
    if not vtts:
        return "no_transcript", [], "no en subtitles via yt-dlp android client"
    try:
        segs = vtt_to_segments(open(vtts[0], encoding="utf-8", errors="ignore").read())
    except Exception as e:
        return "error", [], f"vtt parse failed: {e}"
    if not segs:
        return "no_transcript", [], "subtitle file empty after parsing"
    return "ok", segs, ""


def invidious_captions(video_id):
    """Step 2: Invidious timedtext. Returns (status, segments, err)."""
    for base in INVIDIOUS_INSTANCES:
        try:
            req = urllib.request.Request(
                f"{base}/api/v1/captions/{video_id}",
                headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8", errors="ignore"))
            tracks = data.get("captions", [])
            pick = None
            for t in tracks:
                if t.get("languageCode") == "en":
                    pick = t
                    break
            if not pick:
                return "no_transcript", [], f"{base}: no en caption track"
            cap_url = pick["url"]
            if cap_url.startswith("/"):
                cap_url = base + cap_url
            req = urllib.request.Request(cap_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                vtt = r.read().decode("utf-8", errors="ignore")
            segs = vtt_to_segments(vtt)
            if segs:
                return "ok", segs, ""
            return "no_transcript", [], f"{base}: caption file empty after parsing"
        except Exception as e:
            last_err = f"{base}: {type(e).__name__}: {str(e)[:120]}"
            continue
    return "error", [], f"all Invidious instances failed; last: {last_err}"


def yt_api_transcript(video_id):
    """Step 3: youtube-transcript-api batch script (single video)."""
    venv_py = os.path.join(HOME, "workspace/tools/ytapi-env/bin/python")
    py = venv_py if os.path.exists(venv_py) else sys.executable
    if not os.path.exists(YTAPI_SCRIPT):
        return "error", [], "youtube-transcript-batch.py missing"
    rc, out, err = run([py, YTAPI_SCRIPT, video_id], timeout=180)
    try:
        res = json.loads(out)[0]
    except Exception:
        return "error", [], f"transcript-api script output unparseable: {(out + err)[:150]}"
    if res.get("status") == "ok":
        return "ok", res.get("segments", []), ""
    return res.get("status", "error"), [], res.get("error", "")[:200]


def download_media(ytdlp, url, platform, workdir):
    """Step 4a: download lowest usable video. Returns (path, err)."""
    if not ytdlp:
        return None, "yt-dlp not installed"
    out_tmpl = os.path.join(workdir, "media.%(ext)s")
    if platform == "youtube":
        # Android client only exposes format 18 (360p mp4 + audio).
        cmd = [ytdlp, "--no-check-certificates",
               "--extractor-args", "youtube:player_client=android",
               "--no-warnings", "-f", "18", "-o", out_tmpl, url]
        rc, out, err = run(cmd, timeout=600)
        if rc != 0:
            # Fall back to default client low-res (usually bot-blocked).
            cmd = [ytdlp, "--no-check-certificates", "--no-warnings",
                   "-f", "bv*[height<=480]+ba/b[height<=480]/b",
                   "-o", out_tmpl, url]
            rc, out, err = run(cmd, timeout=600)
    else:
        cmd = [ytdlp, "--no-check-certificates", "--no-warnings",
               "-f", "bv*[height<=480]+ba/b[height<=480]/b",
               "-o", out_tmpl, url]
        rc, out, err = run(cmd, timeout=600)
    cands = []
    for ext in ("mp4", "webm", "mov", "mkv", "m4a"):
        cands += glob.glob(os.path.join(workdir, f"media.{ext}"))
        cands += glob.glob(os.path.join(workdir, f"media.*.{ext}"))
    if not cands:
        return None, f"download failed: {(out + err)[-300:]}"
    # Carousel posts (Instagram) can yield several files; take the largest video.
    cands.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return cands[0], ""


WHISPER_RUNNER = r"""
import json, sys, glob, os
media, out_path, model = sys.argv[1], sys.argv[2], sys.argv[3]
snap = glob.glob(os.path.expanduser(
    f"~/.cache/huggingface/hub/models--Systran--faster-whisper-{model}/snapshots/*"))
src = snap[0] if snap else model
from faster_whisper import WhisperModel
m = WhisperModel(src, device="cpu", compute_type="int8")
segs, info = m.transcribe(media, beam_size=5)
seglist = [{"text": s.text.strip(), "start": round(s.start, 2),
            "duration": round(s.end - s.start, 2)} for s in segs]
json.dump({"segments": seglist, "language": info.language,
           "duration": info.duration}, open(out_path, "w"))
"""


def whisper_transcribe(media, model, workdir):
    """Step 4b: local faster-whisper via the whisper-env venv."""
    py = find_whisper_py()
    runner = os.path.join(workdir, "_whisper_runner.py")
    with open(runner, "w") as f:
        f.write(WHISPER_RUNNER)
    out_path = os.path.join(workdir, "whisper.json")
    env = dict(os.environ)
    env["HF_HUB_OFFLINE"] = "1"
    try:
        p = subprocess.run([py, runner, media, out_path, model],
                           capture_output=True, text=True, timeout=3600, env=env)
    except subprocess.TimeoutExpired:
        return "error", [], "whisper timed out after 1h"
    if p.returncode != 0 or not os.path.exists(out_path):
        return "error", [], f"whisper failed: {(p.stdout + p.stderr)[-300:]}"
    data = json.load(open(out_path))
    segs = [s for s in data["segments"] if s["text"]]
    return ("ok", segs, "") if segs else ("no_transcript", [], "whisper returned no speech")


def extract_frames(media, n, outdir):
    """ffmpeg: N frames spread across duration. Returns [paths]."""
    os.makedirs(outdir, exist_ok=True)
    rc, out, _ = run(["ffprobe", "-v", "error", "-show_entries",
                      "format=duration", "-of", "csv=p=0", media], timeout=60)
    try:
        dur = float(out.strip())
    except ValueError:
        return []
    if dur <= 0 or n <= 0:
        return []
    rc, _, _ = run(["ffmpeg", "-v", "error", "-y", "-i", media,
                    "-vf", f"fps={n}/{dur}", "-frames:v", str(n),
                    os.path.join(outdir, "frame-%02d.jpg")], timeout=300)
    return sorted(glob.glob(os.path.join(outdir, "frame-*.jpg")))


# ---------------- per-URL driver ----------------

def process_url(url, model, n_frames, workdir, keep_media):
    plat = infer_platform(url)
    if not plat:
        return {"url": url, "platform": None, "status": "error",
                "text": "", "segments": [], "frames": [],
                "provenance": {"service": "local-video-transcribe",
                               "method": "unsupported platform", "fetched_at": now_iso()},
                "error": "unsupported platform (youtube/instagram/tiktok/facebook only)"}
    rec = {"url": url, "platform": plat, "status": "error", "text": "",
           "segments": [], "frames": [],
           "provenance": {"service": "local-video-transcribe",
                          "method": "", "fetched_at": now_iso()}}
    ytdlp = find_ytdlp()
    vid = youtube_id(url) if plat == "youtube" else None

    if plat == "youtube" and vid:
        status, segs, err = yt_subs_via_ytdlp(ytdlp, vid, workdir)
        if status == "ok":
            rec.update(status="ok", segments=segs, text=segments_to_text(segs))
            rec["provenance"]["method"] = "yt-dlp android-client subtitles"
            return rec
        status, segs, err = invidious_captions(vid)
        if status == "ok":
            rec.update(status="ok", segments=segs, text=segments_to_text(segs))
            rec["provenance"]["method"] = "invidious timedtext"
            return rec
        # transcript-api ip_blocked is not fatal: local Whisper does not
        # need YouTube timedtext at all, so continue to download.
        status, segs, err = yt_api_transcript(vid)
        if status == "ok":
            rec.update(status="ok", segments=segs, text=segments_to_text(segs))
            rec["provenance"]["method"] = "youtube-transcript-api"
            return rec
        api_note = f"transcript-api: {status}: {err}"
    else:
        api_note = ""

    # Local fallback: download + Whisper + frames.
    media, err = download_media(ytdlp, url, plat, workdir)
    if not media:
        rec["error"] = (api_note + " | " if api_note else "") + err
        rec["status"] = "bot_blocked" if "Sign in to confirm" in err else "error"
        return rec
    status, segs, err = whisper_transcribe(media, model, workdir)
    if status != "ok":
        rec["error"] = (api_note + " | " if api_note else "") + err
        rec["status"] = status
        return rec
    rec.update(status="ok", segments=segs, text=segments_to_text(segs))
    rec["provenance"]["method"] = "yt-dlp download + local faster-whisper"
    if api_note:
        rec["provenance"]["timedtext_fallback_note"] = api_note
    if n_frames > 0:
        rec["frames"] = extract_frames(media, n_frames,
                                       os.path.join(workdir, "frames"))
    if not keep_media:
        try:
            os.remove(media)
        except OSError:
            pass
    return rec


def self_test():
    vtt = ("WEBVTT\nKind: captions\n\n00:00:01.000 --> 00:00:02.000\n"
           "Hello <c>world</c>\n\n00:00:02.000 --> 00:00:03.000\n"
           "Hello world\n\n00:00:03.000 --> 00:00:04.000\nNext line\n")
    segs = vtt_to_segments(vtt)
    ok = (len(segs) == 2 and segs[0]["text"] == "Hello world"
          and segs[1]["text"] == "Next line"
          and infer_platform("https://www.tiktok.com/@x/video/123") == "tiktok"
          and youtube_id("https://www.youtube.com/watch?v=rng_yUSwrgU") == "rng_yUSwrgU"
          and youtube_id("https://youtu.be/rng_yUSwrgU") == "rng_yUSwrgU")
    print(json.dumps({"self_test": ok, "segments": segs}, indent=1))
    return 0 if ok else 1


def main(argv):
    ap = argparse.ArgumentParser(description="Local video transcript + frames (no key, no login)")
    ap.add_argument("pos_urls", nargs="*", help="video URLs")
    ap.add_argument("--urls", default="", help="comma-separated video URLs")
    ap.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "base"))
    ap.add_argument("--frames", type=int, default=5, help="frames to extract (0 = none)")
    ap.add_argument("--workdir", default="", help="work dir (default: temp, deleted unless --keep-media)")
    ap.add_argument("--keep-media", action="store_true", help="keep downloaded media + frames")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    urls = list(args.pos_urls)
    if args.urls:
        urls += [u.strip() for u in args.urls.split(",") if u.strip()]
    if not urls:
        ap.print_help()
        return 2
    results = []
    for url in urls:
        if args.workdir:
            os.makedirs(args.workdir, exist_ok=True)
            wd = args.workdir
            tmp = None
        else:
            tmp = tempfile.TemporaryDirectory(prefix="local-video-transcribe-")
            wd = tmp.name
        try:
            results.append(process_url(url, args.model, args.frames, wd,
                                       args.keep_media or bool(args.workdir)))
        finally:
            if tmp and not args.keep_media:
                tmp.cleanup()
    print(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

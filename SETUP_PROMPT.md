# Copy-paste setup prompt

Copy everything below the line into any AI you use: Muse, Grok bot, Duet, Dots by OpenAI, Aside browser, Claude Code, or Codex. It sets up people-research completely.

---

Set up the people-research skill completely, with no login and no API keys, using only free tools.

1. Get the skill files: clone https://github.com/muj3b/people-research (or copy its SKILL.md and scripts/ folder into your skills directory, with scripts/ next to SKILL.md).
2. Install the free tools. Use a venv, because system pip may be PEP 668 externally-managed and bare `pip install yt-dlp` can fail:

```sh
python3 -m venv ~/workspace/tools/ytdlp-env
~/workspace/tools/ytdlp-env/bin/pip install yt-dlp gallery-dl ytscrape
pip install curl_cffi
mkdir -p ~/workspace/tools/yttranscript-npm && cd ~/workspace/tools/yttranscript-npm
npm init -y && npm install youtube-transcript
```

Local Whisper is free with a cached model: use `~/workspace/tools/whisper-env/bin/python` with `HF_HUB_OFFLINE=1`. ffmpeg is a system package for frame extraction. Call the venv binaries by full path, not bare names.
3. Run the self-test and fix anything that fails before a large job:

```sh
node scripts/people-research-native.js --self-test
node scripts/transcript-batch.js --self-test
python3 scripts/reddit-arctic.py doctor
```

4. Read SKILL.md fully and follow it for every research job: discovery, filtering, text expansion, transcripts, comments, video understanding, and ordered slideshows, with citations and dissent where sources disagree.
5. SKILLLESS RULE, which overrides any tendency to stop early: if you hit a block, do NOT just tell me you are blocked and stop. Figure out an alternative by yourself and continue. Work the fallback ladder in SKILL.md in order: retry with backoff, different instance, different no-key tool, different client variant, local download plus Whisper and frames, search-engine indexing, paste-link browser tool for public URLs only, logged-in browser, and only then a partial-results report listing exactly what you tried.
6. Hard boundaries: never circumvent a CAPTCHA, access control, paywall, or rate/IP block with script tricks; never use another person's credentials; never send private, follower-only, or sensitive content to a third-party tool. Turnstile completing normally in-browser is allowed; script bypass is not. Never use paid APIs (OpenCLI, ScrapeCreators, SocialCrawl, Apify, Brave paid search, Perplexity, paid proxies, paid transcription) unless I explicitly approve them.
7. Report honestly: what works no-login, what works with a caveat, and what needs a manual login or browser, using the tested matrix in SKILL.md. Never claim a platform or capability works no-login unless SKILL.md says so.

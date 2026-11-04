# 🔍 People Research

![Free](https://img.shields.io/badge/free-$0-brightgreen) ![No login](https://img.shields.io/badge/login-none-blue) ![No API keys](https://img.shields.io/badge/API%20keys-none-blue)

I kept hitting a paywall.

Every research tool I opened wanted a key, a login, or money at some point. So I built the version I wanted to use. This one is free, and it stays free.

<p align="center">
  <img src="intro.gif" width="900" alt="People Research intro: free, no login, no keys, comments, transcripts, videos, slides, versus Last 30 Days, Agent Reach, Sherlock, Maigret, and Social Analyzer">
</p>

## Start in one step

Copy this, paste it to any AI, and you are done. It sets everything up by itself.

```text
Set up People Research completely from https://github.com/muj3b/people-research.

Use only free tools. No login, no API keys, no paid services.
Follow the skill in that repo, install what it needs, test it, and fix anything that fails until it works.
If you hit a block, find another way yourself and keep going. Do not just stop and tell me you are blocked.
When you are ready, say so in one line, then wait for my first research question.
```

That is it. No setup list for you to follow. Your AI does the work.

It works with Muse, Grok Bot, Codex, Claude Code, Duet, Dots, Aside browser, and any other AI you paste it to.

## How it works

You ask a question. Anything. A product, a trend, a topic you care about.

It searches everywhere at once. YouTube, TikTok, Reddit, X, Instagram, Threads, Bluesky, Hacker News, and forums.

You get a brief you can actually read. Evidence, with links, in plain language, including when sources disagree.

## What it finds that others don't

| | People Research | Last 30 Days | Agent Reach | Profile tools |
|---|:---:|:---:|:---:|:---:|
| Comments, in full | ✅ | ✅ | ✅ | ❌ |
| Video transcripts | ✅ | ✅ | ✅ | ❌ |
| What happens in the video | ✅ | ❌ | ❌ | ❌ |
| Slides, in order | ✅ | ❌ | ❌ | ❌ |
| A real brief, with both sides | ✅ | ✅ | ❌ | ❌ |
| Free forever, no keys, no login | ✅ | ❌ | ✅* | ✅ |

\* Agent Reach costs no money, but it costs you logins and cookies. See below. Brutally honest version, tool by tool:

Star counts in the intro animation are approximate, from Nov 2026.

### Last 30 Days

**What it is:** a research skill that searches Reddit, X, YouTube, TikTok, Instagram, Hacker News, Polymarket, GitHub, and the web, but only from the last 30 days, then writes a cited, engagement-ranked brief and stores it in a local database.

**What you pay:** its core is free, but the full version is not. TikTok, Instagram, LinkedIn, and Pinterest run through a ScrapeCreators key, 10,000 free calls, then pay as you go. Web search runs through a Brave key, 2,000 free queries a month, then you pay. Perplexity and OpenRouter runs are pay per query. X works through your browser cookies for free, or through a paid xAI key.

**What it has that we don't:** a strict 30-day window, a stored and deduped research database, and extra sources like Polymarket, StockTwits, arXiv, and Techmeme. Its briefs are polished, and on a straight news-style brief it can beat ours.

**What it's missing:** video understanding, slides in order, and TikTok and Instagram transcripts without a paid key. Setup is a wizard and a file full of keys, not one prompt.

### Agent Reach

**What it is:** a capability layer that installs and routes other tools for you, across web pages, X, Reddit, Bilibili, Xiaohongshu, Facebook, LinkedIn, GitHub, and RSS. It does not scrape by itself, it picks the best backend for each platform.

**What you pay:** no money. Its own docs say completely free, with a possible $1 a month server proxy if you are not on your own machine. The price is logins instead. X, Reddit, Facebook, Instagram, and LinkedIn need cookies or a logged-in browser session, and its docs warn that automated access can get an account banned, so it tells you to use a burner account. Reddit and X have no zero-config path at all.

**What it has that we don't:** Bilibili, Xiaohongshu, V2EX, Xueqiu, Facebook feeds and groups through a logged-in browser, and automatic backend switching when a route dies.

**What it's missing:** a brief. It fetches posts and pages. It does not synthesize them into a cited brief with both sides, and it does not do video understanding or slides in order.

### Sherlock

**What it is:** a Python command line tool that takes one username and checks if that exact username exists on 400+ sites, then exports the hits as text, CSV, or Excel. It needs no keys and no login.

**What you pay:** nothing. It is free.

**What it has that we don't:** far wider username coverage than we do, in one command, including bulk usernames and Tor or proxy routing.

**What it's missing:** everything this repo is for. It cannot research a topic, read a comment, transcribe a video, read slides, or write a brief. Give it a question instead of a username and it has nothing to do.

### Maigret

**What it is:** a username dossier tool, a bigger version of Sherlock. It checks 3,000+ sites, 500 popular ones by default, reads the public profile pages it finds, pulls out other usernames and links, then searches those leads too. It can output HTML, PDF, CSV, and JSON reports, and it has a web view that shows results as a graph.

**What you pay:** nothing for the core tool, no keys required. Its optional AI summary mode needs an OpenAI-compatible API, and that part you would pay for.

**What it has that we don't:** recursive discovery, username permutations, profile extraction, and thousands more sites than we cover.

**What it's missing:** topic research. Like Sherlock, it starts from a username, not a question. It does not read comments at scale, transcribe videos, read slides in order, or write a multi-topic brief with dissent.

### Social Analyzer

**What it is:** a username and profile analyzer with an API, a command line tool, and a web app. It searches 1,000+ sites, scores each hit from 0 to 100 to cut false positives, extracts profile metadata, screenshots, and patterns, and can search name variations and multiple usernames at once.

**What you pay:** nothing for the core tool. Some modules use a Google API, which is optional and can cost.

**What it has that we don't:** a confidence score per hit, metadata and screenshot extraction, and a heavier profile analysis setup, including browser driver modules for some sites.

**What it's missing:** the same as the other profile tools. No topic research, no comments, no transcripts, no video understanding, no slides, no brief.

### The honest bottom line

People Research is the only one here that is completely free, needs no keys and no login for its core work, and still gives you comments, transcripts, video understanding, slides, and a brief with both sides. Last 30 Days is the one that will charge you once you use it properly. Agent Reach is free in money but charges you in logins and ban risk. Sherlock, Maigret, and Social Analyzer are free, but they answer a different question: does this username exist, not what do people actually say.

## What a result looks like

> **Should you buy the base iPhone 17 or the Pro?**
>
> Most people say buy the base. It finally has the same 120Hz screen as the Pro, and most owners say they are happy with it.
>
> The other side: the Pro is better if you need the better camera, battery, and cooling, and some owners say the aluminum Pro scratches more easily.
>
> Sources: a TikTok creator video, a YouTube review and its comments, LinkedIn posts, Hacker News threads, and Quora answers, all linked in the full brief.

## One honest note

A few comment sections, like some on Instagram and Facebook, need your browser logged in. Your AI handles that step too, in your own browser, as yourself. Nothing private leaves your machine to a third party tool, and nothing in this repo asks for a key, a password, or a login from you.

## What's inside

- `SKILL.md`: the full skill your AI follows
- `scripts/`: the tools it uses, all free
- `SETUP_PROMPT.md`: the one prompt to copy
- `intro.gif`: the intro animation above

## Find this repo by searching

free people research, free social media research, social media comment research, video transcript research, TikTok comment research, YouTube transcript research, Reddit research, free AI research skill, AI agent research tool, people research skill, open source research agent, no API key research, no login research tool

License: MIT. See [LICENSE](LICENSE).

Paste the prompt above. Ask it something you actually care about.

# Content Factory

> Expanded fork of [mutonby/OpenShorts](https://github.com/mutonby/openshorts) — MIT licensed.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![GitHub stars](https://img.shields.io/github/stars/Jahanzaib211/content-factory?style=social)](https://github.com/Jahanzaib211/content-factory)

**Content Factory** is an expanded, open source fork of OpenShorts. We are **closing the loop** on vendor lock-in by replacing paid-only APIs with free and local alternatives. Every critical capability now has a **free tier or self-hosted fallback** so you can run the entire platform without paying a single dollar to any cloud provider.

**This is no longer just a clip generator.** It is a full content production system: clip generation, AI shorts with actors, voice cloning, video editing, trend research, analytics, scheduling, and a unified gallery — all self-hosted, all open source.

---

## What We Changed (vs Original OpenShorts)

The original OpenShorts was a solid clip generator but locked behind paid APIs (Gemini for everything, ElevenLabs for TTS, Upload-Post for publishing). We expanded it into a complete content factory with free fallbacks at every layer.

### Free Integrations We Added

| What | How It's Free | Replaces |
|------|--------------|----------|
| **edge-tts** | Microsoft Edge TTS — 400+ voices, 70+ languages, zero cost forever | ElevenLabs (paid) |
| **faster-whisper** | Local transcription — 99 languages, word-level timestamps, runs on CPU | OpenAI Whisper API (paid) |
| **CosyVoice** | Local TTS + voice cloning — runs in Docker with GPU | MiniMax voice clone ($1.50/voice) |
| **Wan 2.1** | Local video generation — text-to-video and image-to-video | fal.ai video gen ($0.50+/video) |
| **LiteLLM** | Multi-provider LLM router — works with Ollama, vLLM, any OpenAI-compatible API | Direct vendor API calls |
| **SeaweedFS** | Self-hosted S3-compatible object storage — no AWS bill | AWS S3 (paid) |
| **YouTube/TikTok/Instagram APIs** | Direct API publishing — OAuth2 flows, no middleman | Upload-Post (paid third-party) |
| **pytrends** | Google Trends scraping — free trend research | Paid trend APIs |
| **MediaPipe + YOLOv8** | Local face detection and object tracking — no cloud needed | Cloud vision APIs |
| **PySceneDetect** | Local scene boundary detection — video segmentation | Cloud video analysis |
| **FFmpeg + mcp-video** | Professional video editing — trim, merge, crop, effects, subtitles | CapCut, Descript |
| **Gallery system** | Unified content management — JSON persistence, CRUD, publish flow | No equivalent in competitors |

### Custom Features We Built

| Feature | What It Does |
|---------|-------------|
| **Engine System (17+ engines)** | Modular provider abstraction — every capability has primary + fallbacks |
| **Gallery-First Flow** | Every output goes to unified gallery before publishing |
| **Video Editor** | FFmpeg-powered editing tools in the dashboard |
| **Research Tab** | Trend scanning, keyword research, SEO scoring, AI idea generation |
| **Analytics Tab** | Platform performance tracking — YouTube, TikTok, Instagram |
| **Scheduler** | Content scheduling with cron-based recurring posts |
| **10-Language i18n** | Full internationalization — English, Spanish, French, German, Portuguese, Japanese, Chinese, Korean, Arabic, Hindi |
| **Accessibility** | WCAG-compliant UI with screen reader support |
| **Zero Stub Policy** | Every function does real work — no `b"\x00"` placeholders, no fake data |

### What We Fixed From Original

| Issue | Fix |
|-------|-----|
| Black screen on analytics tab | Fixed missing React import |
| Undefined `e` in catch blocks | Changed to `_` per ESLint rules |
| `getApiUrl` shadowing in components | Removed duplicate function definitions |
| Crop/crop-all blocking event loop | Changed from `async def` to `def` with `subprocess.run` |
| Factory runner missing error handling | Added try/except to all 13 API endpoints |
| Research stubs returning fake data | Replaced with real Google Trends HTML parsing |
| Scheduler repeating same time slots | Fixed to diversify based on stored analytics metrics |
| CosyVoice server writing null bytes | Replaced with real CosyVoice2 TTS inference |
| Wan server faking video generation | Replaced with real Wan 2.1 diffusers pipeline |
| MiniMax STT raising "not available" | Implemented real MiniMax ASR API calls |
| S3 storage get/delete not implemented | Added boto3 implementation via s3_uploader |

---

## 3 Tools in 1 Platform

### 1. Clip Generator
Turn long-form videos into viral-ready 9:16 shorts. Upload a video or paste a YouTube URL — Gemini detects viral moments, FFmpeg extracts clips, MediaPipe + YOLOv8 reframes vertically, faster-whisper adds subtitles.

### 2. AI Shorts (UGC Video Creator)
Generate marketing videos with AI actors for any product. Paste a URL or describe your product — the pipeline scrapes research, writes a script, generates an actor portrait, adds voiceover, creates a talking head video, composites b-roll, and publishes.

### 3. YouTube Studio
AI thumbnails, 10 viral title suggestions, auto-descriptions with chapter timestamps, direct YouTube publishing.

---

## Engine System

Every capability has a **primary engine** (best quality) and **free fallbacks** (zero cost). The engine picker in Settings lets you switch providers.

| Capability | Primary (paid) | Free Fallback |
|-----------|---------------|---------------|
| **LLM** | MiniMax M3 | Ollama (local), vLLM, Gemini free tier |
| **TTS** | MiniMax speech-2.8-hd | **edge-tts** (free, 400+ voices) |
| **STT** | MiniMax ASR | **faster-whisper** (free, local, 99 languages) |
| **Image Gen** | MiniMax image-01 | Flux 2 Pro (fal.ai), ComfyUI (local) |
| **Video Gen** | MiniMax S2V-01 | **Wan 2.1** (free, local) |
| **Music** | MiniMax Music-2.6 | AudioCraft (local), Riffusion |
| **Voice Clone** | MiniMax Voice Clone | **CosyVoice** (free, local) |
| **Storage** | AWS S3 | **Local filesystem** (free), SeaweedFS (self-hosted) |
| **Social** | Upload-Post (paid) | **Direct API** (free — YouTube, TikTok, Instagram) |
| **Research** | Gemini + Google Search | **pytrends** (free), web scraping |
| **Analytics** | Platform APIs | **Local JSON** tracking |
| **Video Editing** | — | **FFmpeg/mcp-video** (free, local) |

---

## Zero-Cost Setup

You can run Content Factory **completely free** with this combination:

```
Gemini (free tier) + faster-whisper (local) + edge-tts (free) + local storage
```

No API keys required beyond Gemini. No credit card. No watermarks. No upload limits. No data leaving your server.

---

## Gallery-First Flow

Every piece of content flows through a unified gallery:

```
Generate → Gallery → Edit → Publish → Track
```

- All clips, AI shorts, avatars, translations saved to one place
- Caption editing, metadata updates, status tracking
- One-click publish to TikTok, Instagram, YouTube
- Draft → Published → Archived lifecycle

---

## Dashboard

11 tabs, each a focused workspace:

| Tab | Purpose |
|-----|---------|
| **Dashboard** | Clip generator — upload video, get shorts |
| **SaaShorts** | AI shorts pipeline — paste URL, get marketing video |
| **Factory** | Template-based generation — 10 content templates |
| **Voice Lab** | Voice library — list, test, clone voices |
| **Avatar Studio** | AI actor generation — generate or upload |
| **Multilingual** | Video translation — 10+ languages |
| **Research** | Trend scanner, keyword research, SEO scoring, AI ideas |
| **Analytics** | Platform performance — connect channels, view stats |
| **Gallery** | Unified content store — browse, edit, publish |
| **Video Editor** | FFmpeg tools — trim, merge, crop, effects, subtitles |
| **Settings** | API keys, engine selection, system config |

---

## AI Shorts Pipeline (Full Flow)

```
RESEARCH → SCRIPT → ACTOR → VOICE → VIDEO → B-ROLL → SUBTITLES → COMPOSITE → GALLERY → PUBLISH → TRACK
```

| Step | Engine | Free Option |
|------|--------|-------------|
| Research | Gemini + Google Search | pytrends (free) |
| Script | MiniMax M3 / Gemini | Ollama (local, free) |
| Actor Image | MiniMax image-01 | Flux 2 Pro / ComfyUI (local) |
| Voiceover | MiniMax speech-2.8-hd | **edge-tts** (free) |
| Talking Head | MiniMax S2V-01 | **Wan 2.1** (local, free) |
| B-Roll | Flux 2 Pro + FFmpeg | Stable Diffusion (local) |
| Subtitles | **faster-whisper** (free) | — |
| Composite | **FFmpeg** (free) | — |
| Gallery | **Local JSON** (free) | — |
| Publish | **Direct API** (free) | — |
| Analytics | Platform APIs | **Local JSON** (free) |

---

## Clip Generator Pipeline

1. **Ingest** — Upload video or YouTube URL (yt-dlp)
2. **Transcribe** — faster-whisper, word-level timestamps, 99 languages
3. **Detect** — PySceneDetect scene boundaries
4. **Analyze** — Gemini identifies 3-15 viral moments
5. **Extract** — FFmpeg precise clip cutting
6. **Reframe** — MediaPipe + YOLOv8 AI vertical cropping
7. **Effects** — Subtitles, hooks, AI video effects
8. **Publish** — Storage backup + social distribution

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, httpx |
| Frontend | React 18, Vite 4, Tailwind CSS 3.4 |
| Video | FFmpeg, mcp-video, PySceneDetect, yt-dlp |
| Audio | faster-whisper (local STT), edge-tts (free TTS), CosyVoice (voice clone) |
| AI/ML | Gemini, MiniMax, MediaPipe, YOLOv8, Wan 2.1 |
| Storage | Local filesystem, SeaweedFS, AWS S3 |
| Publishing | YouTube Data API, TikTok Content Posting, Instagram Graph API |
| Infrastructure | Docker + Docker Compose |

---

## Getting Started

### 1. Clone
```bash
git clone https://github.com/Jahanzaib211/content-factory.git
cd content-factory
```

### 2. Launch
```bash
docker compose up --build
```

### 3. Open Dashboard
Navigate to **`http://localhost:5175`**

### 4. Configure (optional)
Go to **Settings** and enter any API keys you want. The platform works without most of them using free/local fallbacks.

---

## Requirements

- **Docker & Docker Compose**
- **Google Gemini API Key** ([Free](https://aistudio.google.com/app/apikey)) — only required key for clip generation

**Optional** (for enhanced features):
- MiniMax API Key — AI shorts, premium TTS, image gen
- fal.ai API Key — alternative image/video generation
- ElevenLabs API Key — alternative voiceover/dubbing

---

## Environment Variables

**Server-side (.env):**
| Variable | Description |
|----------|------------|
| `STORAGE_BACKEND` | `local` (free), `seaweedfs`, or `s3` |
| `WHISPER_MODEL` | faster-whisper model (default: `large-v3`) |
| `MAX_CONCURRENT_JOBS` | Processing limit (default: 5) |
| `COSYVOICE_MODEL_DIR` | Local CosyVoice model path |
| `LANGFUSE_HOST` | Langfuse observability (optional) |

**Client-side (encrypted in localStorage):**
| Key | Required? |
|-----|-----------|
| `GEMINI_API_KEY` | Yes |
| `MINIMAX_API_KEY` | Optional |
| `FAL_KEY` | Optional |
| `ELEVENLABS_API_KEY` | Optional |

---

## Content Factory vs Competitors

| Feature | Content Factory | Opus Clip | CapCut | Vizard | Klap | Descript |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Price** | **Free** | $15-29/mo | $8/mo | $15-20/mo | $23-63/mo | $24-65/mo |
| **Self-hosted** | **Yes** | No | No | No | No | No |
| **Open source** | **Yes** | No | No | No | No | No |
| **Watermark** | **Never** | Free tier | Some | Free tier | Free tier | Free tier |
| **AI clip detection** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Smart 9:16 reframing** | Yes | Yes | Yes | Yes | Yes | No |
| **Auto subtitles** | Yes | Yes | Yes | Yes | Yes | Yes |
| **Voice dubbing (30+ langs)** | Yes | No | Pro only | No | Pro only | Business only |
| **AI UGC actors** | **Yes** | No | No | No | No | No |
| **AI video effects** | Yes | No | Yes | No | No | No |
| **YouTube Studio** | **Yes** | No | No | No | No | No |
| **Social auto-publishing** | Yes | Pro only | TikTok only | Paid only | Paid only | No |
| **Schedule uploads** | Yes | Pro only | No | Paid only | Paid only | No |
| **Local TTS fallback** | **Yes** | No | No | No | No | No |
| **Unified gallery** | **Yes** | No | No | No | No | No |
| **Video editor** | **Yes** | No | Yes | No | No | Yes |
| **Zero-cost mode** | **Yes** | No | No | No | No | No |
| **Data privacy** | **Your server** | Their cloud | Their cloud | Their cloud | Their cloud | Their cloud |

---

## How Much Does It Cost?

| Mode | Cost | What You Get |
|------|------|-------------|
| **Zero-cost** | $0 | Clip generation, transcription, TTS, subtitles, publishing |
| **Budget** | ~$0.65/video | AI shorts with actors (MiniMax + fal.ai) |
| **Premium** | ~$2/video | Premium actors, voice cloning, music generation |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Content Factory                           │
├──────────────────────────────────────────────────────────────┤
│  Dashboard (React + Tailwind)     │  Backend (FastAPI)       │
│  ├─ Clip Generator                │  ├─ engines/ (17+)       │
│  ├─ AI Shorts (SaaShorts)        │  │   ├─ edge_tts (free)  │
│  ├─ YouTube Studio                │  │   ├─ stt (free)       │
│  ├─ Voice Lab                     │  │   ├─ gallery          │
│  ├─ Avatar Studio                 │  │   ├─ video_editor     │
│  ├─ Multilingual                  │  │   ├─ research         │
│  ├─ Research                      │  │   ├─ analytics        │
│  ├─ Analytics                     │  │   ├─ scheduler        │
│  ├─ Gallery                       │  │   ├─ social (direct)  │
│  ├─ Video Editor                  │  │   └─ storage (local)  │
│  └─ Settings                      │  ├─ saasshorts.py        │
│                                   │  ├─ main.py (clips)      │
│  10 languages (i18n)              │  └─ translate.py         │
│  WCAG accessible                  │                          │
│                                   │  Docker:                 │
│                                   │  ├─ backend              │
│                                   │  ├─ frontend             │
│                                   │  ├─ renderer             │
│                                   │  ├─ cf-cosyvoice (GPU)   │
│                                   │  └─ cf-wan-video (GPU)   │
└──────────────────────────────────────────────────────────────┘
```

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Jahanzaib211/content-factory&type=Date)](https://star-history.com/#Jahanzaib211/content-factory&Date)

## Credits

- Original project by [mutonby/OpenShorts](https://github.com/mutonby/openshorts)
- Expanded by [Jahanzaib211](https://github.com/Jahanzaib211) with free integrations and production features
- See [Contributors](https://github.com/Jahanzaib211/content-factory/graphs/contributors) for the full list

## Contributions

Contributions welcome. We are particularly interested in:
- More free/local engine implementations
- Additional language translations
- New content templates
- Pipeline optimizations
- Documentation improvements

## License

MIT License. Content Factory is yours to use, modify, and scale. No vendor lock-in. No hidden costs.

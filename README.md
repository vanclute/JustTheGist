# JustTheGist

> Feed it anything. Tell it what you want. Get the gist.

LLM-agnostic content analyzer and research assistant. Feed it any URL or file to analyze, or let it research a topic for you by finding and synthesizing relevant content. Works with YouTube, podcasts, articles, PDFs, local audio/video. No code—just instruction files for Claude Code, Gemini CLI, Cursor, and more.

## The Problem

You find an interesting-looking YouTube video, podcast, or article. It's 45 minutes long. You don't have time to watch/listen/read the whole thing just to find out if it has the information you need.

## The Solution

Give the URL (or file) to your AI coding assistant. Tell it what you're hoping to learn. Get a detailed, tailored analysis in moments—complete with key takeaways, resources mentioned, notable quotes, and an honest assessment of whether the full content is worth your time.

## Three Modes

**Analyze Mode** (passive)
Give it a URL or file, tell it what you're looking for, get a tailored analysis.

**Research Mode** (active)
Tell it what topic you want to learn about. It will search, curate, analyze, and synthesize findings from multiple sources.

**Recall Mode** (memory)
Query your personal knowledge base - everything you've previously analyzed, stored for semantic search and instant recall.

## Supported Content Types

| Type | Source | Requirements |
|------|--------|--------------|
| Online Videos | YouTube, Vimeo, Twitter/X, TikTok, Twitch, [1000+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) | yt-dlp |
| Podcasts | YouTube, SoundCloud, Spotify (some), many podcast platforms | yt-dlp |
| Web Articles | Any URL | None (built-in) |
| PDF Documents | Local files | None (built-in) |
| Local Audio | .mp3, .wav, .m4a, .ogg, .flac | openai-whisper, ffmpeg |
| Local Video | .mp4, .mkv, .avi, .mov, .webm | openai-whisper, ffmpeg |

## Supported AI Tools

This repo includes instruction files for multiple AI coding assistants:

| File | Tool |
|------|------|
| `CLAUDE.md` | [Claude Code](https://claude.ai/claude-code) |
| `GEMINI.md` | [Gemini CLI](https://github.com/google-gemini/gemini-cli) |
| `AGENTS.md` | [OpenAI Codex](https://openai.com/codex) |
| `.cursorrules` | [Cursor](https://cursor.sh) |
| `INSTRUCTIONS.md` | Generic (copy to your tool's expected file) |

**Using a different tool?** If your AI assistant reads from a project-level instruction file (like `YOURTOOL.md`), just copy any of the above and rename it. The instructions are tool-agnostic.

## Prerequisites

- Python 3.8+
- An AI coding assistant (Claude Code, Gemini CLI, Cursor, etc.)

## Quick Start

```bash
git clone https://github.com/vanclute/JustTheGist.git
cd JustTheGist
claude  # or gemini, cursor, etc.
```

**That's it.** Clone, open, use. Your AI assistant handles all setup automatically.

On first run, your AI assistant will:
1. Ask which content types you want to analyze
2. Automatically install only the dependencies you need
3. Save your preferences for next time

Then just give it a URL or file and say what you're looking for:

```
Here's a video about prompt engineering: https://youtube.com/watch?v=...
I want to learn practical tips I can use immediately.
```

## Output

You get two things:

1. **Immediate Summary** - Key takeaways, resources, notable quotes, and a "worth your time?" assessment shown right in your terminal

2. **Detailed Report** - A comprehensive markdown file saved to `docs/` with full analysis, all topics covered, and connections to your stated interests

## Example Use Cases

**Analyze Mode**
- "I found this 2-hour conference talk. Does it cover anything about testing strategies?"
- "Here's a podcast episode. Extract any book recommendations they mention."
- "I have this PDF whitepaper. Summarize the key findings relevant to distributed systems."
- "Here's a YouTube tutorial. I just need to know how they handle authentication."
- "I recorded a meeting. What action items were assigned to the engineering team?"

**Research Mode**
- "Research the current state of AI coding assistants - find me 10 videos and tell me what the consensus is"
- "I want to learn about home automation. Find beginner-friendly content and summarize the key concepts."

**Recall Mode**
- "What did I learn about authentication patterns?" (searches your knowledge base)
- "Show me everything I've saved about React performance"

## How It Works

No magic, no custom code. Just well-crafted instructions that tell your AI assistant:

1. Ask what you're hoping to learn
2. Detect the content type
3. Extract text (via yt-dlp for online video, Whisper for local audio/video, or direct fetch for articles/PDFs)
4. Analyze with your goals in mind
5. Generate a tailored report
6. Clean up temporary files

The AI does all the work. The instruction files just tell it how.

## Cost Optimization

JustTheGist automatically optimizes for cost and speed by delegating tasks appropriately:

| Task | Model Tier | Why |
|------|------------|-----|
| Extraction (transcripts, metadata) | Light (Haiku/Flash/GPT-4o-mini) | Mechanical work, no reasoning needed |
| Analysis & report writing | Standard (Sonnet/Pro/GPT-4o) | Requires judgment and synthesis |

This can reduce costs by 10-20x for extraction tasks while maintaining analysis quality. Tools that don't support model switching simply use the default model for everything.

## Knowledge Base

JustTheGist can build a persistent "brain" from everything you analyze:

- **Store** - After any analysis, optionally save insights to your local vector database
- **Recall** - Semantically search your accumulated knowledge anytime
- **Cite** - Results include source attribution ("According to [Video] by [Channel]...")

Built on ChromaDB + sentence-transformers. Runs locally, no cloud required, works on CPU.

**Additional dependencies** (installed automatically if you enable this feature):
```bash
pip install chromadb sentence-transformers
```

### The Knowledge Flywheel

The Knowledge Base creates a compounding effect similar to human learning:

```
New Content → Analyzed with prior context → Enriched synthesis stored → Informs next analysis
     ↑                                                                          │
     └──────────────────────────────────────────────────────────────────────────┘
```

**What gets stored isn't raw transcripts** - it's your interpreted understanding in context of everything already known. Over time:

- Connections between topics emerge organically
- Contradictions surface ("Source A says X, but Source B says Y")
- Consensus solidifies across multiple sources
- Understanding deepens with each piece of content analyzed

The more you learn, the better you learn. Each analysis is richer than the last.

## Privacy

- All processing happens locally (except AI API calls to your chosen provider)
- Transcripts and reports stay on your machine
- No data sent anywhere except to the AI service you're already using

## Contributing

Found a bug? Have a suggestion? PRs and issues welcome.

Ideas for contribution:
- Instruction files for additional AI tools
- Improved prompts for specific content types
- Better handling of edge cases

## What Gets Installed (Automatically)

Curious what dependencies your AI assistant installs? Only what you need:

| Capability | Package | Notes |
|------------|---------|-------|
| YouTube videos | `youtube-transcript-api` + `yt-dlp` | Instant transcript fetch; yt-dlp for metadata |
| Other online video | `yt-dlp` | Supports [1000+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| Local audio/video | `openai-whisper` | Also requires ffmpeg (install via system package manager) |
| Web articles & PDFs | None | Built into your AI tool |
| Knowledge Base | `chromadb`, `sentence-transformers` | Local vector DB + embeddings |

For local audio/video, you'll also need [ffmpeg](https://ffmpeg.org/download.html):
- **Windows**: `winget install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Linux**: `apt install ffmpeg`

## License

MIT - Do whatever you want, just keep the license.

---

*Stop watching. Start knowing.*

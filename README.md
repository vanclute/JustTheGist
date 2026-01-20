# JustTheGist

> Feed it anything. Tell it what you want. Get the gist.

LLM-agnostic content analyzer. Feed it any URL or file (YouTube, podcasts, articles, PDFs, local audio/video), tell it what you're looking for, get a tailored gist. No code—just instruction files for Claude Code, Gemini CLI, Cursor, and more.

## The Problem

You find an interesting-looking YouTube video, podcast, or article. It's 45 minutes long. You don't have time to watch/listen/read the whole thing just to find out if it has the information you need.

## The Solution

Give the URL (or file) to your AI coding assistant. Tell it what you're hoping to learn. Get a detailed, tailored analysis in moments—complete with key takeaways, resources mentioned, notable quotes, and an honest assessment of whether the full content is worth your time.

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

## Quick Start

### 1. Clone or Download

```bash
git clone https://github.com/vanclute/JustTheGist.git
cd JustTheGist
```

### 2. Open with Your AI Tool

```bash
# Claude Code
claude

# Gemini CLI
gemini

# Or open the folder in Cursor, Windsurf, etc.
```

### 3. First Run

On first use, your AI assistant will:
1. Ask which content types you want to analyze
2. Install only the dependencies you need
3. Save your preferences

### 4. Analyze Content

Just provide a URL or file path and say what you're looking for:

```
Here's a video about prompt engineering: https://youtube.com/watch?v=...
I want to learn practical tips I can use immediately.
```

## Dependencies

Installed automatically based on your needs during first-run setup:

### For YouTube/Online Video
```bash
pip install yt-dlp
```

### For Local Audio/Video Transcription
```bash
pip install openai-whisper
```

Plus [ffmpeg](https://ffmpeg.org/download.html) (install via your system package manager):
- **Windows**: `winget install ffmpeg` or download from ffmpeg.org
- **macOS**: `brew install ffmpeg`
- **Linux**: `apt install ffmpeg` or `dnf install ffmpeg`

## Output

You get two things:

1. **Immediate Summary** - Key takeaways, resources, notable quotes, and a "worth your time?" assessment shown right in your terminal

2. **Detailed Report** - A comprehensive markdown file saved to `docs/` with full analysis, all topics covered, and connections to your stated interests

## Example Use Cases

- "I found this 2-hour conference talk. Does it cover anything about testing strategies?"
- "Here's a podcast episode. Extract any book recommendations they mention."
- "I have this PDF whitepaper. Summarize the key findings relevant to distributed systems."
- "Here's a YouTube tutorial. I just need to know how they handle authentication."
- "I recorded a meeting. What action items were assigned to the engineering team?"

## How It Works

No magic, no custom code. Just well-crafted instructions that tell your AI assistant:

1. Ask what you're hoping to learn
2. Detect the content type
3. Extract text (via yt-dlp for online video, Whisper for local audio/video, or direct fetch for articles/PDFs)
4. Analyze with your goals in mind
5. Generate a tailored report
6. Clean up temporary files

The AI does all the work. The instruction files just tell it how.

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

## License

MIT - Do whatever you want, just keep the license.

---

*Stop watching. Start knowing.*

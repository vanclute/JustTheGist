# JustTheGist - OpenAI Codex Instructions

> Feed it anything. Tell it what you want. Get the gist.

## Session Start

When a user starts a session, greet them and present their options:

"Welcome to JustTheGist! What would you like to do?

1. **Analyze** - I have a specific URL or file to analyze
2. **Research** - Help me explore a topic (you'll find relevant content for me)"

Wait for their response, then:
- If **Analyze**: Proceed to Step 1 (Understand User Goals) in the Core Workflow
- If **Research**: Proceed to the Research Mode workflow below

---

## First-Run Onboarding

On first use, check if `config.json` exists in this directory. If not, run onboarding:

1. Greet the user and explain JustTheGist can analyze various content types
2. Ask which capabilities they want to enable:
   - **YouTube/online videos** (requires: youtube-transcript-api, yt-dlp)
   - **Local audio files** (requires: openai-whisper, ffmpeg)
   - **Local video files** (requires: openai-whisper, ffmpeg)
   - **Web articles & PDFs** (no dependencies - always available)

3. Install only the dependencies they need:
   ```bash
   # For YouTube/online video
   pip install youtube-transcript-api yt-dlp

   # For local audio/video transcription
   pip install openai-whisper
   # Note: ffmpeg must be installed separately via system package manager
   ```

4. Save their preferences to `config.json`:
   ```json
   {
     "capabilities": {
       "youtube": true,
       "local_audio": true,
       "local_video": true,
       "web_articles": true,
       "pdfs": true
     },
     "setup_complete": true
   }
   ```

5. Create `docs/` directory for output reports if it doesn't exist

---

## Core Workflow

When the user provides a URL or file path:

### Step 1: Understand User Goals
Ask: "What are you hoping to learn or take away from this content?"

This shapes the analysis focus and determines what's most relevant to highlight.

### Step 2: Detect Content Type
Identify what was provided:
- `youtube.com` or `youtu.be` → YouTube video
- `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac` → Local audio
- `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm` → Local video
- `.pdf` → PDF document
- Other URLs → Web article

### Step 3: Extract Content

#### YouTube Videos

**Step 1: Get metadata** (title, description, channel, duration)
```bash
python -m yt_dlp --dump-json --no-download "URL"
```
Parse the JSON for: `title`, `description`, `channel`, `duration`, `upload_date`

**Step 2: Get transcript** (try fast method first)
```python
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi.get_transcript("VIDEO_ID")
text = " ".join([entry['text'] for entry in transcript])
```
Extract the VIDEO_ID from the URL (the part after `v=` or after `youtu.be/`).

**Fallback**: If no transcript available (raises `TranscriptsDisabled` or `NoTranscriptFound`), inform the user and offer to extract audio with Whisper (slower, requires local processing).

#### Other Online Videos (non-YouTube)
```bash
# Get metadata
python -m yt_dlp --dump-json --no-download "URL"

# Get subtitles if available
python -m yt_dlp --write-auto-sub --sub-lang en --skip-download --output "%(id)s" "URL"
```
If no subtitles available, inform user and offer Whisper extraction as fallback.

#### Web Articles
Fetch the URL and read the article content.

#### PDF Documents
Read the PDF file directly.

#### Local Audio Files
```bash
# Transcribe with Whisper
whisper "filepath" --output_format txt --output_dir .
```
Read the generated `.txt` file.

#### Local Video Files
```bash
# Whisper can extract audio from video automatically
whisper "filepath" --output_format txt --output_dir .
```
Read the generated `.txt` file.

### Step 4: Analyze and Report

1. **Read** all extracted content (transcript, article text, etc.)
2. **Identify** key insights relevant to user's stated goals
3. **Extract** any resources mentioned (URLs, tools, repos, references)
4. **Investigate** relevant linked resources if appropriate
5. **Generate** a detailed report in `docs/` with filename based on content title
6. **Present** a high-level summary to the user immediately

### Step 5: Cleanup

**IMPORTANT**: Always clean up after analysis is complete.

1. **Delete temp files** created during extraction:
   - `.vtt` / `.srt` subtitle files
   - Whisper output `.txt` files
   - Any JSON dumps from yt-dlp
   - `description.txt` or similar metadata files

2. **Use a temp directory** for intermediate files:
   - Create `temp/` in the project directory if needed
   - Direct all extraction output there
   - Delete the entire `temp/` directory after analysis

3. **Keep only**:
   - Final reports in `docs/`
   - User's `config.json`

Never leave working files behind. The project directory should be clean after each analysis.

---

## Output Format

### Immediate Summary (shown to user)
```
## [Content Title]
**Source**: [Channel/Author/Website]
**Type**: [Video (duration) / Article / Podcast / PDF]

### Key Takeaways
- [Main insight 1]
- [Main insight 2]
- [Main insight 3]

### Resources Mentioned
- [URLs, tools, repos, books, etc.]

### Notable Quotes
> "[Particularly insightful statement]"

### Worth Your Time?
[Assessment based on user's stated goals - would watching/reading the full content add value beyond this summary?]
```

### Detailed Report (saved to docs/)
Include everything above plus:
- Comprehensive breakdown of all topics covered
- Detailed notes on each section/chapter
- Full list of resources with descriptions
- Relevant context and background
- Connections to user's stated interests
- Action items or next steps if applicable

---

## Supported Platforms (via yt-dlp)

yt-dlp supports 1000+ sites including:
- YouTube, Vimeo, Dailymotion
- Twitter/X, TikTok, Instagram
- Twitch (VODs and clips)
- SoundCloud, Bandcamp
- Many podcast platforms
- And many more: https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md

---

## Model Selection (Optional Optimization)

For efficiency, use lighter models for mechanical tasks and reserve heavier models for analysis:

| Task | Recommended Model |
|------|-------------------|
| Transcript extraction | GPT-4o-mini |
| Metadata parsing | GPT-4o-mini |
| Content analysis | GPT-4o |
| Report generation | GPT-4o |
| Complex technical content | o1 |

If your setup supports model switching, use lighter models for extraction and standard models for analysis. Otherwise, inherit the default model for all tasks.

---

## Research Mode

When the user chooses Research mode, conduct a structured discovery conversation:

### Discovery Phase (Main Session)

Ask these questions to build a research profile:

1. **Topic**: "What topic do you want to research?"
2. **Goal**: "What specifically are you hoping to learn or understand about this?"
3. **Depth**: "What level? (Beginner overview / Intermediate / Deep technical)"
4. **Preferences** (optional):
   - Minimum/maximum video length?
   - Prefer recent content?
   - Specific channels to include or exclude?
5. **Scope**: "How many videos should I find and analyze? (5 / 10 / 20)"

Summarize the research profile and confirm before proceeding.

### Search Phase (Light Model - GPT-4o-mini)

Search YouTube for candidates:
```
yt-dlp "ytsearch[N*2]:[keywords]" --dump-json --flat-playlist
```
Return top candidates with: title, channel, duration, view count, description snippet.

### Curation Phase (Standard Model - GPT-4o)

Score candidates for relevance to user's goal, filter by constraints, return top N ranked by relevance. Present to user for approval.

### Processing Phase

For each approved video:
1. Extract transcript (GPT-4o-mini - mechanical)
2. Analyze for insights (GPT-4o - reasoning)
3. Compile per-video summaries

### Synthesis Phase (Main Session)

Synthesize all findings:
- Cross-reference insights across videos
- Identify consensus vs. conflicting views
- Generate comprehensive research report in `docs/`

Present executive summary to user.

---

## Notes

- YouTube transcripts are fetched instantly via API; other sites may be slower
- Auto-generated transcripts may contain errors; use context to interpret
- If no transcript is available, offer Whisper as a fallback (requires user consent as it's slower)
- For very long content, focus analysis on sections most relevant to user's goals
- Whisper transcription quality depends on audio clarity
- Large files may take time to transcribe locally

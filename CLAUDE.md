# JustTheGist - Claude Code Instructions

> Feed it anything. Tell it what you want. Get the gist.

## Session Start

When a user starts a session, greet them and present their options:

"Welcome to JustTheGist! What would you like to do?

1. **Analyze** - I have a specific URL or file to analyze
2. **Research** - Help me explore a topic (you'll find relevant content for me)
3. **Recall** - Search my knowledge base for something I've learned before"

Wait for their response, then:
- If **Analyze**: Proceed to Step 1 (Understand User Goals) in the Core Workflow
- If **Research**: Proceed to the Research Mode workflow
- If **Recall**: Proceed to the Knowledge Base Query workflow

---

## First-Run Onboarding

On first use, check if `config.json` exists in this directory. If not, run onboarding:

1. Greet the user and explain JustTheGist can analyze various content types
2. Ask which capabilities they want to enable:
   - **YouTube/online videos** (requires: youtube-transcript-api, yt-dlp)
   - **Local audio files** (requires: openai-whisper, ffmpeg)
   - **Local video files** (requires: openai-whisper, ffmpeg)
   - **Web articles & PDFs** (no dependencies - always available)
   - **Knowledge Base** (requires: chromadb, sentence-transformers) - Store and recall learned content

3. Install only the dependencies they need:
   ```bash
   # For YouTube/online video
   pip install youtube-transcript-api yt-dlp

   # For local audio/video transcription
   pip install openai-whisper
   # Note: ffmpeg must be installed separately via system package manager

   # For Knowledge Base (persistent memory)
   pip install chromadb sentence-transformers
   ```

4. Save their preferences to `config.json`:
   ```json
   {
     "capabilities": {
       "youtube": true,
       "local_audio": true,
       "local_video": true,
       "web_articles": true,
       "pdfs": true,
       "knowledge_base": true
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

**IMPORTANT**: Delegate extraction to a low-reasoning task agent (Haiku for Claude, Flash for Gemini, etc.). This is mechanical work that doesn't require deep reasoning.

#### YouTube Videos

Delegate to low-reasoning agent (Haiku/Flash/etc.) with this prompt:
```
Extract metadata and transcript from YouTube video: [URL]

1. Get metadata using yt-dlp --dump-json --no-download
2. Extract transcript using youtube-transcript-api
3. Return: title, description, channel, duration, upload_date, and full transcript text

If transcript unavailable, report the error and suggest Whisper as fallback.
```

The agent should:
- Parse JSON for: `title`, `description`, `channel`, `duration`, `upload_date`
- Extract VIDEO_ID from URL (part after `v=` or `youtu.be/`)
- Use `YouTubeTranscriptApi` to fetch transcript
- Join transcript entries into full text
- Return all extracted data back to main session

#### Other Online Videos (non-YouTube)

Delegate to low-reasoning agent to:
- Extract metadata using `yt-dlp --dump-json --no-download`
- Extract subtitles using `yt-dlp --write-auto-sub --sub-lang en`
- Return metadata and subtitle text, or suggest Whisper fallback if unavailable

#### Web Articles

**No delegation needed** - use WebFetch directly in main session (already efficient).

#### PDF Documents

**No delegation needed** - use Read tool directly in main session (native support).

#### Local Audio Files

Delegate to low-reasoning agent to:
- Transcribe using `whisper "filepath" --output_format txt --output_dir .`
- Read generated `.txt` file
- Return transcript text

#### Local Video Files

Delegate to low-reasoning agent to:
- Transcribe using `whisper "filepath" --output_format txt --output_dir .`
- Read generated `.txt` file
- Return transcript text

### Step 4: Analyze and Report

**IMPORTANT**: This happens in the MAIN SESSION (requires reasoning and judgment).

Once extraction is complete:

1. **Review** all extracted content from the task agent
2. **Identify** key insights relevant to user's stated goals
3. **Extract** any resources mentioned (URLs, tools, repos, references)
4. **Investigate** relevant linked resources using WebFetch if appropriate
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

## Agent Delegation Pattern

**Standard workflow:**
- **Extraction** (Step 3) → Delegate to low-reasoning agent with `model: "haiku"`
- **Analysis** (Step 4) → Main session (inherits your current model)

This pattern:
- Reduces token costs for mechanical work
- Preserves reasoning capacity for analysis
- Applies to any AI system with tiered models (Claude Haiku, Gemini Flash, etc.)

---

## Research Mode

When the user chooses Research mode, conduct a structured discovery conversation:

### Discovery Phase (Main Session)

Ask these questions to build a research profile:

1. **Topic**: "What topic do you want to research?"
2. **Goal**: "What specifically are you hoping to learn or understand about this?"
3. **Depth**: "What level? (Beginner overview / Intermediate / Deep technical)"
4. **Preferences** (optional):
   - Minimum video length? (skip short clips)
   - Maximum video length? (avoid 3-hour podcasts)
   - Prefer recent content? (last year, last month, any time)
   - Specific channels to include or exclude?
5. **Scope**: "How many videos should I find and analyze? (5 / 10 / 20)"

Summarize the research profile and confirm before proceeding.

### Search Phase (Delegate to Light Model)

Use a task agent with the lightest model (Haiku/Flash/etc.) to:

```
Search YouTube for: [topic keywords]
Return up to [N * 2] candidates with: title, channel, duration, view count, upload date, description snippet

Use: yt-dlp "ytsearch[N*2]:[keywords]" --dump-json --flat-playlist
```

### Curation Phase (Delegate to Standard Model)

Use a task agent with standard model (Sonnet/Pro/etc.) to:
- Score each candidate for relevance to the user's stated goal
- Filter by user's constraints (length, recency, etc.)
- Return the top N videos ranked by relevance

Present the curated list to the user for approval (or let them swap out videos).

### Processing Phase (Delegate Extraction to Light Model)

For each approved video:
1. Extract transcript (light model - mechanical)
2. Analyze for insights relevant to research goal (standard model)
3. Compile per-video summaries

### Synthesis Phase (Main Session)

Back in the main session, synthesize all findings:
- Cross-reference insights across videos
- Identify consensus views vs. conflicting opinions
- Highlight the most valuable sources
- Note any gaps in coverage
- Generate comprehensive research report in `docs/`

Present executive summary to user with link to full report.

---

## Knowledge Base

JustTheGist can build a persistent "brain" from content you analyze - stored locally in a vector database for semantic search.

### Setup

On first use of Knowledge Base features, initialize the database:
```python
import chromadb
client = chromadb.PersistentClient(path="knowledge_base/chroma_db")
collection = client.get_or_create_collection(
    name="justthegist",
    metadata={"description": "JustTheGist knowledge base"}
)
```

### Storing Knowledge (After Analysis)

After completing any analysis, ask: "Would you like to store this in your knowledge base?"

If yes, store:
1. **Chunk the transcript** into ~500 token segments with overlap
2. **Generate embeddings** using sentence-transformers (automatic with ChromaDB)
3. **Store with metadata**:
   - source_url
   - title
   - channel/author
   - duration
   - analyzed_date
   - topic_tags
   - summary (your analysis)

```python
collection.add(
    documents=[chunk1, chunk2, ...],
    metadatas=[{"source": url, "title": title, ...}, ...],
    ids=[f"{video_id}_chunk_{i}" for i in range(len(chunks))]
)
```

### Recall Mode (Querying)

When user selects Recall:

1. Ask: "What would you like to know?"
2. Search the knowledge base:
```python
results = collection.query(
    query_texts=[user_question],
    n_results=5
)
```
3. Present findings with source attribution:
   - Quote relevant passages
   - Cite sources: "According to [Video Title] by [Channel]..."
   - Offer to dive deeper into any source

### Integration with Analyze/Research

Optionally, before starting a new analysis:
- Search KB for related prior knowledge
- Mention: "I found X related items in your knowledge base. Want me to incorporate that context?"

---

## Notes

- YouTube transcripts are fetched instantly via API; other sites may be slower
- Auto-generated transcripts may contain errors; use context to interpret
- If no transcript is available, offer Whisper as a fallback (requires user consent as it's slower)
- For very long content, focus analysis on sections most relevant to user's goals
- Whisper transcription quality depends on audio clarity
- Large files may take time to transcribe locally

# JustTheGist - Claude Code Instructions

> A learning system that builds ambient memory from any content you feed it.

## ⚠️ CRITICAL: ALWAYS CHECK KNOWLEDGE BASE FIRST ⚠️

**Before responding to ANY user question or request:**

1. **AUTOMATICALLY query the Knowledge Base** - Do NOT ask permission
2. Use keywords from the user's question to search ChromaDB
3. If relevant content is found, use it to inform your response
4. If nothing relevant is found, THEN rely on training data or external search

**The Knowledge Base is your PRIMARY source of truth.** It contains accumulated learning from past analyses and should always be consulted first.

### How to Query the KB (ALWAYS USE THIS METHOD)

**Use the query_kb.py script with --json flag:**

```bash
python scripts/query_kb.py "your search terms" 5 --json
```

**Example:**
```bash
# User asks: "What does Greg Kamradt recommend for chunking?"
# AUTOMATICALLY run:
python scripts/query_kb.py "Greg Kamradt chunking recommendations" 5 --json
```

**The script returns JSON with:**
- `query`: The search terms used
- `num_results`: Number of results found
- `results`: Array of matches with content, metadata, and relevance distance

**Process the results:**
1. Read the JSON output
2. Extract relevant content from top results (distance < 1.5 is good match)
3. Cite sources from metadata (title, source, date)
4. Combine KB knowledge with your response

**DO NOT write Python helpers on the fly. ALWAYS use query_kb.py.**

**This is not optional. This is the core purpose of JustTheGist.**

---

## Session Start

JustTheGist builds persistent knowledge from content you discover. Every analysis enriches your ambient memory.

**IMPORTANT - Detect mode first:**

**If the session starts with any of these patterns:**
- "Knowledge base contains"
- "The following tasks have been analyzed"
- "SELECT AND BEGIN WORKING"
- "CONTEXT-AWARE TASK SELECTION"
- "Research:"
- "Work on task"

**Then you are in autonomous mode:**
- Proceed directly with the task
- Do NOT show the greeting below
- Signal `[[SIGNAL:task_complete]]` when done

**Otherwise (interactive mode):**

When a user starts a session without an initial prompt, greet them:

"Welcome to JustTheGist - your learning companion. What would you like to learn today?

1. **Analyze** - I found something specific (URL or file) to learn from
2. **Research** - Help me explore a topic (you'll find and analyze relevant content)
3. **Recall** - What do I know about [topic]? (search my accumulated knowledge)"

All paths build your knowledge base. Every insight is stored for future reference.

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

## Dependency Auto-Install

**CRITICAL: Run pre-flight check ONCE in the main session BEFORE delegating any tasks to agents. Do NOT check dependencies in each task agent - that's wasteful and causes parallel install conflicts.**

JustTheGist installs dependencies on-demand. You don't need to manually set anything up - when a tool is needed, it's installed automatically.

### How It Works

```python
def ensure_installed(package_name, pip_package=None, check_command=None):
    """Install package if not already present"""
    import subprocess
    pip_package = pip_package or package_name
    check_command = check_command or f"python -m {package_name} --version"

    try:
        # Try to run the tool
        subprocess.run(check_command.split(),
                      capture_output=True, check=True, timeout=5)
        return True  # Already installed
    except:
        print(f"Installing {package_name}...")
        try:
            subprocess.run(["pip", "install", pip_package],
                          capture_output=True, check=True, timeout=120)
            print(f"✓ {package_name} installed successfully")
            return True
        except Exception as e:
            print(f"⚠ Failed to install {package_name}: {e}")
            return False
```

### Pre-Flight in Main Session

**BEFORE delegating extraction to task agents**, run a single pre-flight check in the main session:

```python
# Run ONCE at session start or before first extraction
def ensure_all_dependencies():
    """One-time check for all needed dependencies"""
    print("Checking dependencies...")

    # Core dependencies for most tasks
    ensure_installed("yt-dlp")
    ensure_installed("youtube-transcript-api")
    ensure_installed("chromadb")
    ensure_installed("sentence-transformers")

    print("✓ All dependencies ready\n")

# Call this ONCE before spawning any task agents
ensure_all_dependencies()
```

After pre-flight passes, task agents can assume all dependencies exist.

### User Experience

Dependencies install silently in the background when first needed. User sees:
```
Installing yt-dlp...
✓ yt-dlp installed successfully
[continuing with analysis...]
```

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

**⚠️ CRITICAL: YouTube Rate Limiting**

YouTube aggressively rate-limits bulk transcript requests. To avoid being blocked:

- **Process YouTube videos SEQUENTIALLY, not in parallel**
- Add 2-3 second delays between requests: `time.sleep(2)`
- Limit to 3-5 YouTube videos per batch
- Mix sources: alternate YouTube with articles/docs/PDFs
- If rate-limited (429 errors), pause for 5+ minutes

**DO NOT spawn parallel task agents for multiple YouTube videos** - YouTube will block all requests.

For large research tasks, prefer diversifying sources over exhausting YouTube.

---

**IMPORTANT**: Delegate extraction to a low-reasoning task agent (Haiku for Claude, Flash for Gemini, etc.). This is mechanical work that doesn't require deep reasoning.

#### YouTube Videos

**Note: Dependencies already verified in pre-flight check. Task agents can proceed directly.**

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

**Note: Dependencies already verified in pre-flight check. Task agents can proceed directly.**

Delegate to low-reasoning agent to:
- Extract metadata using `yt-dlp --dump-json --no-download`
- Extract subtitles using `yt-dlp --write-auto-sub --sub-lang en`
- Return metadata and subtitle text, or suggest Whisper fallback if unavailable

#### Web Articles

**No delegation needed** - use WebFetch directly in main session (already efficient).

#### PDF Documents

**No delegation needed** - use Read tool directly in main session (native support).

#### Local Audio Files

**Note: Dependencies already verified in pre-flight check. Task agents can proceed directly.**

Delegate to low-reasoning agent to:
- Transcribe using `whisper "filepath" --output_format txt --output_dir .`
- Read generated `.txt` file
- Return transcript text

#### Local Video Files

**Note: Dependencies already verified in pre-flight check. Task agents can proceed directly.**

Delegate to low-reasoning agent to:
- Transcribe using `whisper "filepath" --output_format txt --output_dir .`
- Read generated `.txt` file
- Return transcript text

### Step 4: Analyze and Report

**IMPORTANT**: This happens in the MAIN SESSION (requires reasoning and judgment).

Once extraction is complete:

1. **Consult Knowledge Base** (if enabled): Search for related prior knowledge using keywords from the content. Keep relevant context available for enriching the analysis.
2. **Review** all extracted content from the task agent
3. **Identify** key insights relevant to user's stated goals
4. **Extract** any resources mentioned (URLs, tools, repos, references)
5. **Investigate** relevant linked resources using WebFetch if appropriate
6. **Generate** a detailed report in `docs/` with filename based on content title
7. **Present** a high-level summary to the user immediately

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

**Rate Limit Protection:**
- Process YouTube videos sequentially with delays
- If researching 10+ sources, mix YouTube with articles/documentation
- Consider splitting: 3-4 YouTube videos + 6-7 articles/docs
- Sequential processing is slower but avoids rate limits

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

### Auto-Ingest (Automatic)

**Every analysis automatically updates the Knowledge Base.** This is not optional - building ambient memory is the core purpose.

After completing any analysis:
1. Save the report to `docs/` (or `docs/pending/` per hooks)
2. **Automatically ingest using ingest_report.py**
3. Verify ingestion succeeded

**Use the ingest_report.py script:**

```bash
# After saving report to docs/MyReport.md
python ingest_report.py docs/MyReport.md
```

The script will:
- Chunk the content into ~500 word pieces with overlap
- Add all chunks to ChromaDB with metadata
- Report how many chunks were added

**CRITICAL: Do NOT mark "Add to Knowledge Base" task as complete unless you've actually run the ingestion script and verified it succeeded.**

Every piece of content analyzed becomes part of your persistent memory.

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

### Ambient Memory Integration

**This is the core purpose of JustTheGist** - not an optional feature. Every analysis enriches your ambient memory, and every future interaction draws from that accumulated knowledge.

**CRITICAL: The Knowledge Base is automatically consulted for ALL interactions:**
- User asks a question → Query KB first
- User requests analysis → Query KB for related prior knowledge
- User mentions a topic/person → Query KB for context
- **NEVER ask permission** to check the KB - it's automatic

**Before ANY response:**
1. Extract key topics/keywords from the user's input
2. Query the KB for related content:
   ```python
   related = collection.query(
       query_texts=[user_input_keywords],
       n_results=5
   )
   ```
3. If relevant content found → Use it in your response with citations
4. If nothing found → Proceed with training data or external search

**Before analyzing any content:**
1. Extract key topics/keywords from the content title and description
2. Query the KB for related prior knowledge
3. Keep relevant prior knowledge in context for the analysis

**During analysis:**
- Note connections to prior knowledge: "This aligns with / contradicts what [Source] discussed..."
- Identify patterns across sources
- Flag when new information updates or challenges previous understanding

**In the final report:**
- Include a "Connections to Prior Knowledge" section when relevant
- Cross-reference related content you've analyzed before
- Note consensus vs. conflicting viewpoints across your knowledge base

This transforms each analysis from isolated summary into **contextual synthesis**.

---

## Autonomous Learning (Curiosity Mode)

### Pre-Flight Check (Required)

**CRITICAL: Run this ONCE in the main session before starting autonomous learning, NOT in each task.**

**Rate Limit Awareness:**
Autonomous mode may process many videos. To avoid YouTube blocking:
- Limit YouTube videos to 3-5 per learning session
- Diversify sources: academic papers, documentation, blog posts
- Add delays between YouTube requests
- If rate-limited, pivot to alternative sources automatically

Before starting autonomous mode, verify all core dependencies are installed. This prevents mid-run failures.

```python
def preflight_check():
    """Verify core dependencies before autonomous mode starts"""
    required = [
        ("yt-dlp", "yt-dlp"),
        ("youtube-transcript-api", "youtube-transcript-api"),
        ("chromadb", "chromadb"),
        ("sentence-transformers", "sentence-transformers")
    ]

    print("Running pre-flight dependency check...")
    all_ok = True

    for package, pip_name in required:
        if not ensure_installed(package, pip_name):
            print(f"✗ Failed to install {package}")
            all_ok = False
        else:
            print(f"✓ {package} ready")

    if not all_ok:
        print("\n⚠ Pre-flight check failed. Cannot start autonomous mode.")
        print("Please install missing dependencies manually:")
        print("  pip install yt-dlp youtube-transcript-api chromadb sentence-transformers")
        return False

    print("✓ Pre-flight check passed. Starting autonomous learning...\n")
    return True

# Run BEFORE autonomous mode starts
if not preflight_check():
    exit(1)
```

**When to run:**
- Immediately upon detecting autonomous mode
- Before processing any tasks
- If any dependency fails to install, exit cleanly with error message

**What gets checked:**
- yt-dlp (online video)
- youtube-transcript-api (YouTube transcripts)
- chromadb (knowledge base)
- sentence-transformers (embeddings)

Note: openai-whisper is optional (only for local audio/video), so it's not in the required list.

---

When running in autonomous mode, JustTheGist becomes self-directed. After completing any research, it identifies what to learn next and continues automatically.

### Detecting Autonomous Mode

Check hook output for autonomous mode indicators. If using **clautonomous**, look for:
```
[AUTONOMOUS MODE - Signal TASK_COMPLETE when done]
```

If present (or if running under any autonomous wrapper), curiosity mode is engaged.

### After Completing Research (Autonomous Only)

**CRITICAL: In autonomous mode, these steps are MANDATORY before signaling task_complete. DO NOT skip curiosity analysis.**

1. **Analyze what you just learned** and identify 3-5 interesting threads to explore:
   - Concepts mentioned but not yet in your KB
   - Topics referenced by multiple sources
   - Areas where sources disagreed
   - Connections to existing knowledge
   - Terms you don't fully understand
   - Tools or frameworks mentioned
   - Related adjacent topics

2. **Rank them by interestingness**:
   - Frequency of mention (more = more interesting)
   - Relevance to existing knowledge
   - Potential to fill gaps or deepen understanding
   - Connections to multiple areas you already know
   - Practical applicability

3. **Queue ALL interesting topics to the backlog** (most interesting first):

   **If using clautonomous** (backlog.json exists):
   ```python
   import json
   from pathlib import Path

   def add_learning_tasks(topics_with_reasons):
       """Add multiple learning tasks to backlog at once

       Args:
           topics_with_reasons: List of (topic, reason) tuples
       """
       backlog_path = Path("backlog.json")
       if not backlog_path.exists():
           return  # Not using clautonomous

       with open(backlog_path, "r", encoding="utf-8") as f:
           data = json.load(f)

       existing_ids = [t.get("id", "") for t in data.get("tasks", [])]
       learn_ids = [int(id.split("-")[1]) for id in existing_ids if id.startswith("LEARN-")]
       next_num = max(learn_ids, default=0) + 1

       # Add all topics
       for topic, reason in topics_with_reasons:
           new_task = {
               "id": f"LEARN-{next_num:03d}",
               "description": f"Research: {topic}",
               "reason": reason,
               "status": "queued",
               "type": "learning"
           }
           data.setdefault("tasks", []).append(new_task)
           print(f"Added to backlog: {new_task['id']} - {topic}")
           next_num += 1

       with open(backlog_path, "w", encoding="utf-8") as f:
           json.dump(data, f, indent=2)

   # Example: Add 3-5 topics discovered from current research
   interesting_topics = [
       ("hybrid search strategies for RAG", "Mentioned in 3 videos about vector DBs"),
       ("reranking models", "Multiple sources discussed relevance reranking"),
       ("chunking strategies comparison", "Conflicting opinions on optimal chunk size"),
       ("embedding model selection", "Key decision point, needs deeper understanding")
   ]
   add_learning_tasks(interesting_topics)
   ```

   **If using another automation system:**
   - Write all topics to `next_topics.txt` (one per line)
   - Or output it in a format your wrapper expects
   - Or store in a task queue your system uses

4. **ONLY AFTER adding next topic to backlog, signal completion**:
   - **Clautonomous:** `[[SIGNAL:task_complete]]`
   - **Other systems:** Use whatever completion signal your wrapper expects

**Order is critical:**
1. Complete current research
2. Identify next interesting topic
3. Add to backlog
4. THEN signal task_complete

If you signal completion WITHOUT adding a next topic, the autonomous loop stops.

The wrapper will automatically pick up the next task from the backlog.

### The Curiosity Loop

```
Research topic A
    ↓
Notice interesting thread B
    ↓
Add "Research: B" to backlog
    ↓
Signal task_complete
    ↓
Wrapper picks up B from backlog
    ↓
Research topic B
    ↓
Notice interesting thread C
    ↓
... continues until backlog empty or limits hit
```

### Seeding the Learning

The user starts autonomous mode with an initial direction:
```
Learn about AI coding assistants and related tooling.
```

From there, curiosity takes over - following threads, exploring tangents, and building comprehensive knowledge organically.

---

## Notes

- YouTube transcripts are fetched instantly via API; other sites may be slower
- Auto-generated transcripts may contain errors; use context to interpret
- If no transcript is available, offer Whisper as a fallback (requires user consent as it's slower)
- For very long content, focus analysis on sections most relevant to user's goals
- Whisper transcription quality depends on audio clarity
- Large files may take time to transcribe locally
## Clautonomous Integration

This project uses [clautonomous](https://github.com/user/clautonomous) for autonomous execution.

### Workflow

1. **Planning Phase** (regular `claude`):
   - Discuss goals and requirements
   - Create spec/PRD documents
   - Populate `backlog.json` with tasks

2. **Execution Phase** (`claude-auto`):
   - Wrapper manages context and recovery
   - Claude picks tasks from backlog
   - Signals `TASK_COMPLETE` when done

### Key Files

- `backlog.json` - Task queue for autonomous execution
- `RESUME_*.md` - Session handoff documents (auto-generated)
- `CONTEXT_*.md` - Detailed context (auto-generated)

### Signaling

When a task is complete:
```
[[SIGNAL:task_complete]]
```

When blocked:
```
[[SIGNAL:blocked:reason here]]
```

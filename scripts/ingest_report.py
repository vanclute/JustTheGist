#!/usr/bin/env python3
"""
Ingest a document into the JustTheGist Knowledge Base

Usage:
    python ingest_report.py <file_path> [--force]

Examples:
    python ingest_report.py docs/my_report.md
    python ingest_report.py docs/analysis.txt --force
"""

import sys
from pathlib import Path

def chunk_text(text, chunk_size=1500, overlap=200):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at paragraph or sentence
        if end < len(text):
            # Look for paragraph break
            last_para = chunk.rfind("\n\n")
            if last_para > chunk_size // 2:
                end = start + last_para
                chunk = text[start:end]
            else:
                # Look for sentence break
                last_period = chunk.rfind(". ")
                if last_period > chunk_size // 2:
                    end = start + last_period + 1
                    chunk = text[start:end]

        chunks.append(chunk.strip())
        start = end - overlap

    return chunks

def extract_metadata(content, filename):
    """Extract metadata from document header"""
    metadata = {
        "filename": filename,
        "title": filename.replace("-", " ").replace("_", " ").replace(".md", "").replace(".txt", ""),
        "source_url": "",
        "channel": "",
        "upload_date": "",
    }

    # Try to extract structured metadata
    lines = content.split("\n")[:20]  # Check first 20 lines
    for line in lines:
        if line.startswith("**Video**:") or line.startswith("# "):
            metadata["title"] = line.replace("**Video**:", "").replace("# ", "").strip()
        elif line.startswith("**Channel**:"):
            metadata["channel"] = line.replace("**Channel**:", "").strip()
        elif line.startswith("**Source**:"):
            metadata["source_url"] = line.replace("**Source**:", "").strip()
        elif line.startswith("**Upload Date**:") or line.startswith("**Date**:"):
            metadata["upload_date"] = line.replace("**Upload Date**:", "").replace("**Date**:", "").strip()

    return metadata

def ingest_document(file_path, force=False):
    """Ingest a document into the knowledge base"""
    try:
        import chromadb
    except ImportError:
        print("Error: chromadb not installed. Run: pip install chromadb", file=sys.stderr)
        sys.exit(1)

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Read content
    content = file_path.read_text(encoding="utf-8")
    metadata = extract_metadata(content, file_path.name)

    # Initialize ChromaDB (use project root's knowledge_base/)
    project_root = Path(__file__).parent.parent
    kb_path = project_root / "knowledge_base" / "chroma_db"
    kb_path.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(kb_path))
    collection = client.get_or_create_collection(
        name="justthegist",
        metadata={"description": "JustTheGist knowledge base"}
    )

    # Chunk the document
    chunks = chunk_text(content)
    print(f"Processing: {file_path.name}")
    print(f"  - {len(chunks)} chunks")

    # Generate IDs
    doc_id = file_path.stem.replace(" ", "_").replace("-", "_")[:50]
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

    # Check if already exists
    existing = collection.get(ids=ids)
    if existing and existing['ids'] and not force:
        print(f"  - Already in KB (use --force to overwrite)")
        return

    # Prepare metadata for each chunk
    metadatas = [{
        "title": metadata["title"],
        "source_url": metadata["source_url"],
        "channel": metadata["channel"],
        "upload_date": metadata["upload_date"],
        "filename": metadata["filename"],
        "chunk_index": i,
        "total_chunks": len(chunks)
    } for i in range(len(chunks))]

    # Add to collection
    if existing and existing['ids']:
        # Update existing
        collection.update(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"  - Updated in knowledge base")
    else:
        # Add new
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        print(f"  - Added to knowledge base")

    print(f"[OK] Ingestion complete")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    file_path = sys.argv[1]
    force = "--force" in sys.argv

    ingest_document(file_path, force)

#!/usr/bin/env python3
"""Ingest RAG research report into Knowledge Base"""

import chromadb
from pathlib import Path
import hashlib

def chunk_text(text, chunk_size=500, overlap=100):
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks

def ingest_report(report_path):
    """Ingest report into ChromaDB knowledge base"""

    # Initialize ChromaDB
    client = chromadb.PersistentClient(path="knowledge_base/chroma_db")
    collection = client.get_or_create_collection(
        name="justthegist",
        metadata={"description": "JustTheGist knowledge base"}
    )

    # Read report
    content = Path(report_path).read_text(encoding="utf-8")

    # Extract metadata from report
    lines = content.split('\n')
    title = lines[0].replace('#', '').strip() if lines else "Unknown"

    metadata = {
        "source": str(report_path),
        "title": title,
        "type": "research_report",
        "topic": "RAG best practices",
        "date": "2026-01-20"
    }

    # Chunk the content
    chunks = chunk_text(content, chunk_size=500, overlap=100)

    # Generate document ID from filename
    doc_id = Path(report_path).stem[:50]

    # Prepare documents with metadata
    documents = chunks
    metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]
    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]

    # Add to collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"[SUCCESS] Ingested {len(chunks)} chunks from {Path(report_path).name}")
    print(f"   Document ID: {doc_id}")
    print(f"   Collection: justthegist")
    print(f"   Total documents in KB: {collection.count()}")

    return len(chunks)

if __name__ == "__main__":
    report_path = "docs/RAG_Best_Practices_Research_Report.md"

    if not Path(report_path).exists():
        print(f"[ERROR] Report not found: {report_path}")
        exit(1)

    ingest_report(report_path)

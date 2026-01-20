#!/usr/bin/env python3
"""
Query the JustTheGist Knowledge Base

Usage:
    python query_kb.py "search query" [num_results] [--json]

Examples:
    python query_kb.py "RAG best practices" 5
    python query_kb.py "Claude Code hooks" 3 --json
"""

import sys
import json
from pathlib import Path

def query_kb(query_text, n_results=5, json_output=False):
    """Query the knowledge base and return results"""
    try:
        import chromadb
    except ImportError:
        print("Error: chromadb not installed. Run: pip install chromadb", file=sys.stderr)
        sys.exit(1)

    # Use project root's knowledge_base/
    project_root = Path(__file__).parent.parent
    kb_path = project_root / "knowledge_base" / "chroma_db"
    if not kb_path.exists():
        print(f"Error: Knowledge base not found at {kb_path}", file=sys.stderr)
        print("Run some analyses first to populate the knowledge base.", file=sys.stderr)
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(kb_path))

    try:
        collection = client.get_collection(name="justthegist")
    except Exception as e:
        print(f"Error: Could not access knowledge base: {e}", file=sys.stderr)
        sys.exit(1)

    # Query the collection
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )

    if json_output:
        # Return structured JSON
        output = {
            "query": query_text,
            "num_results": len(results['documents'][0]) if results['documents'] else 0,
            "results": []
        }

        if results['documents'] and results['documents'][0]:
            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                output['results'].append({
                    "rank": i + 1,
                    "content": doc,
                    "metadata": meta,
                    "distance": dist
                })

        print(json.dumps(output, indent=2))
    else:
        # Human-readable output
        if not results['documents'] or not results['documents'][0]:
            print(f"No results found for: {query_text}")
            return

        print(f"Query: {query_text}")
        print(f"Found {len(results['documents'][0])} results:\n")

        for i, (doc, meta, dist) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"{'='*60}")
            print(f"Result {i+1} (distance: {dist:.3f})")
            print(f"Source: {meta.get('title', 'Unknown')}")
            if meta.get('source_url'):
                print(f"URL: {meta['source_url']}")
            if meta.get('channel'):
                print(f"Channel: {meta['channel']}")
            print(f"\nContent preview:")
            print(doc[:300] + "..." if len(doc) > 300 else doc)
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    query = sys.argv[1]
    n_results = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "--json" else 5
    json_mode = "--json" in sys.argv

    query_kb(query, n_results, json_mode)

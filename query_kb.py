#!/usr/bin/env python3
"""Query JustTheGist Knowledge Base from command line"""

import sys
import json
import chromadb
from pathlib import Path

# Force UTF-8 output encoding
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def query_kb(query_text, n_results=5):
    """Query ChromaDB knowledge base"""

    kb_path = Path("knowledge_base/chroma_db")
    if not kb_path.exists():
        print("ERROR: Knowledge base not found at knowledge_base/chroma_db")
        return []

    try:
        client = chromadb.PersistentClient(path=str(kb_path))
        collection = client.get_or_create_collection(name="justthegist")

        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )

        # Format results
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        distances = results['distances'][0] if results['distances'] else []

        output = []
        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            output.append({
                'rank': i + 1,
                'content': doc,
                'metadata': meta,
                'distance': dist
            })

        return output

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python query_kb.py 'your query here' [num_results] [--json]")
        print("Example: python query_kb.py 'Greg Kamradt chunking' 5")
        print("Example: python query_kb.py 'James Briggs' 3 --json")
        sys.exit(1)

    query = sys.argv[1]
    use_json = '--json' in sys.argv
    n_results = 5

    # Parse num_results (could be before or after --json)
    for arg in sys.argv[2:]:
        if arg != '--json' and arg.isdigit():
            n_results = int(arg)

    results = query_kb(query, n_results)

    if use_json:
        # JSON output for easy parsing
        print(json.dumps({
            'query': query,
            'num_results': len(results),
            'results': results
        }, indent=2, ensure_ascii=False))
    else:
        # Human-readable output
        print(f"Querying KB: '{query}'\n")
        if not results:
            print("No results found.")
        else:
            print(f"Found {len(results)} results:\n")
            for result in results:
                print(f"--- Result {result['rank']} (distance: {result['distance']:.3f}) ---")
                print(f"Source: {result['metadata'].get('source', 'Unknown')}")
                print(f"Title: {result['metadata'].get('title', 'Unknown')}")
                content_preview = result['content'][:500].replace('\n', ' ')
                print(f"Content: {content_preview}...")
                print()

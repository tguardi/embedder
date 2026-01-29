#!/usr/bin/env python3
"""
Simple workflow: text file → embeddings → Solr 9

Usage:
  python simple_to_solr.py input.txt \
    --api-url "YOUR_API_URL" \
    --solr-url "http://localhost:8983/solr" \
    --collection "vectors"
"""

import argparse
import json
import time
import requests
from tqdm import tqdm


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def get_embedding(text: str, api_url: str) -> list[float]:
    """Get embedding for a single text."""
    resp = requests.post(
        api_url,
        headers={"Content-Type": "application/json"},
        json={"inputs": text},
        timeout=30,
    )
    resp.raise_for_status()

    result = resp.json()
    if isinstance(result, list):
        return result
    elif isinstance(result, dict):
        return result.get("data", result.get("embeddings", result))
    return result


def index_to_solr(solr_url: str, collection: str, docs: list[dict]) -> None:
    """Index documents to Solr."""
    url = f"{solr_url}/{collection}/update/json/docs?commit=false"
    resp = requests.post(url, json=docs, timeout=60)
    resp.raise_for_status()


def commit_solr(solr_url: str, collection: str) -> None:
    """Commit Solr collection."""
    url = f"{solr_url}/{collection}/update?commit=true"
    requests.get(url, timeout=60).raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Simple text embedder → Solr")
    parser.add_argument("input", help="Input text file")
    parser.add_argument("--api-url", required=True, help="Embedding API URL")
    parser.add_argument("--solr-url", default="http://localhost:8983/solr", help="Solr URL")
    parser.add_argument("--collection", default="vectors", help="Solr collection name")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size")
    parser.add_argument("--overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--batch-size", type=int, default=100, help="Solr batch size")
    parser.add_argument("--doc-id", help="Document ID (default: filename)")
    args = parser.parse_args()

    doc_id = args.doc_id or args.input.replace("/", "_").replace("\\", "_")

    print(f"Input: {args.input}")
    print(f"API: {args.api_url}")
    print(f"Solr: {args.solr_url}/{args.collection}")
    print(f"Document ID: {doc_id}")

    # Read input
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Input: {len(text):,} characters")

    # Chunk
    chunks = chunk_text(text, args.chunk_size, args.overlap)
    print(f"Chunks: {len(chunks)}")

    # Get embeddings and build Solr docs
    start_time = time.perf_counter()
    docs = []

    for idx, chunk in enumerate(tqdm(chunks, desc="Embedding & indexing")):
        # Get embedding
        vector = get_embedding(chunk, args.api_url)

        # Create Solr document
        doc = {
            "id": f"{doc_id}_chunk_{idx}",
            "doc_id": doc_id,
            "chunk_index": idx,
            "chunk_text": chunk,
            "vector": vector,
        }
        docs.append(doc)

        # Batch index to Solr
        if len(docs) >= args.batch_size:
            index_to_solr(args.solr_url, args.collection, docs)
            docs = []

    # Index remaining
    if docs:
        index_to_solr(args.solr_url, args.collection, docs)

    # Commit
    print("Committing...")
    commit_solr(args.solr_url, args.collection)

    elapsed = time.perf_counter() - start_time
    print(f"\nDone in {elapsed:.1f}s")
    print(f"Throughput: {len(chunks) / elapsed:.0f} chunks/sec")
    print(f"Indexed {len(chunks)} chunks to {args.collection}")


if __name__ == "__main__":
    main()

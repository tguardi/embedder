#!/usr/bin/env python3
"""
Simple embedding script: read texts, chunk, get embeddings from custom API.

Usage:
  python simple_embedder.py input.txt output.json
  python simple_embedder.py input.txt output.json --chunk-size 1000
"""

import argparse
import json
import time
from typing import Generator
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


def get_embeddings(chunks: list[str], api_url: str, batch_size: int) -> list[dict]:
    """Send chunks to API and get embeddings."""
    results = []

    for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
        batch = chunks[i : i + batch_size]

        # Single text per request (adjust if your API supports batches)
        for chunk in batch:
            resp = requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json={"inputs": chunk},
                timeout=30,
            )
            resp.raise_for_status()

            # Assuming API returns vector or {data: vector}
            result = resp.json()
            if isinstance(result, list):
                vector = result
            elif isinstance(result, dict):
                vector = result.get("data", result.get("embeddings", result))
            else:
                vector = result

            results.append({
                "text": chunk,
                "vector": vector,
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Simple text embedder")
    parser.add_argument("input", help="Input text file")
    parser.add_argument("output", help="Output JSON file")
    parser.add_argument("--api-url", required=True, help="Embedding API URL")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    args = parser.parse_args()

    print(f"Reading from: {args.input}")
    print(f"API URL: {args.api_url}")
    print(f"Chunk size: {args.chunk_size}, overlap: {args.overlap}")

    # Read input
    with open(args.input, 'r', encoding='utf-8') as f:
        text = f.read()

    print(f"Input length: {len(text):,} characters")

    # Chunk
    start_time = time.perf_counter()
    chunks = chunk_text(text, args.chunk_size, args.overlap)
    print(f"Generated {len(chunks)} chunks")

    # Get embeddings
    results = get_embeddings(chunks, args.api_url, args.batch_size)

    # Save
    output = {
        "metadata": {
            "input_file": args.input,
            "api_url": args.api_url,
            "chunk_size": args.chunk_size,
            "overlap": args.overlap,
            "num_chunks": len(chunks),
            "vector_dim": len(results[0]["vector"]) if results else 0,
        },
        "chunks": results,
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    elapsed = time.perf_counter() - start_time
    print(f"\nDone in {elapsed:.1f}s")
    print(f"Throughput: {len(chunks) / elapsed:.0f} chunks/sec")
    print(f"Output: {args.output}")
    print(f"Vector dimension: {output['metadata']['vector_dim']}")


if __name__ == "__main__":
    main()

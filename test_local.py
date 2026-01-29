#!/usr/bin/env python3
"""
Local test script - tests embeddings without Solr.

Usage:
  python test_local.py           # Test with DJL container
  python test_local.py --local   # Test with local sentence-transformers
"""

import argparse
import requests
from dotenv import load_dotenv
import os

load_dotenv("config.env")

DJL_URL = os.environ.get("DJL_URL", "")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "64"))


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


# ---------------------------------------------------------------------------
# Embedder backends (same as main pipeline)
# ---------------------------------------------------------------------------

class DJLEmbedder:
    def __init__(self, djl_url: str, batch_size: int):
        self.djl_url = djl_url
        self.batch_size = batch_size

    def encode(self, texts: list[str]) -> list[list[float]]:
        all_vectors = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            resp = requests.post(self.djl_url, json={"inputs": batch}, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            vectors = result if isinstance(result, list) else result.get("data", result.get("embeddings", []))
            all_vectors.extend(vectors)
        return all_vectors

    def ping(self) -> bool:
        try:
            ping_url = self.djl_url.replace("/predictions/all-MiniLM-L6-v2", "/ping")
            resp = requests.get(ping_url, timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


class LocalEmbedder:
    def __init__(self, model_name: str, batch_size: int):
        from sentence_transformers import SentenceTransformer
        import torch

        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

        print(f"  Loading model {model_name} on device: {device}")
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size
        self.device = device

    def encode(self, texts: list[str]) -> list[list[float]]:
        import torch
        embeddings = self.model.encode(texts, batch_size=self.batch_size, show_progress_bar=False, convert_to_numpy=True)
        if self.device == "mps":
            torch.mps.synchronize()
        return embeddings.tolist()

    def ping(self) -> bool:
        return True  # Always available once loaded


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_connection(embedder) -> bool:
    """Test that embedder is reachable."""
    print(f"Testing connection...")
    result = embedder.ping()
    print(f"  Ping: {'OK' if result else 'FAILED'}")
    return result


def test_embeddings(embedder) -> bool:
    """Test embedding generation."""
    test_texts = [
        "This is a test sentence for embedding.",
        "Another sentence to verify batch processing works.",
        "The quick brown fox jumps over the lazy dog.",
    ]

    print(f"\nEmbedding {len(test_texts)} texts...")
    vectors = embedder.encode(test_texts)

    print(f"  Received {len(vectors)} vectors")
    if vectors:
        print(f"  Vector dimension: {len(vectors[0])}")
        print(f"  First vector (truncated): {vectors[0][:5]}...")

    return len(vectors) == len(test_texts)


def test_chunking() -> bool:
    """Test chunking logic."""
    sample_doc = "This is a sample document. " * 100  # ~2700 chars

    chunks = chunk_text(sample_doc, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"\nChunking test:")
    print(f"  Input length: {len(sample_doc)} chars")
    print(f"  Chunk size: {CHUNK_SIZE}, overlap: {CHUNK_OVERLAP}")
    print(f"  Generated {len(chunks)} chunks")
    print(f"  Chunk lengths: {[len(c) for c in chunks[:3]]}...")

    return len(chunks) > 0


def test_full_pipeline(embedder) -> bool:
    """Test chunking + embedding together."""
    sample_doc = "This is a sample document that simulates content from Solr 7. " * 50

    print(f"\nFull pipeline test:")
    chunks = chunk_text(sample_doc, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"  Chunked into {len(chunks)} pieces")

    import time
    start = time.perf_counter()
    all_vectors = embedder.encode(chunks)
    elapsed = time.perf_counter() - start

    print(f"  Generated {len(all_vectors)} embeddings in {elapsed:.2f}s")
    print(f"  Vector dimension: {len(all_vectors[0]) if all_vectors else 'N/A'}")
    print(f"  Throughput: {len(chunks) / elapsed:.0f} chunks/sec")

    return len(all_vectors) == len(chunks)


def test_large_batch(embedder) -> bool:
    """Test with a larger batch to measure throughput."""
    sample_doc = "This is a longer sample document for throughput testing. " * 200
    chunks = chunk_text(sample_doc, CHUNK_SIZE, CHUNK_OVERLAP)

    print(f"\nLarge batch test ({len(chunks)} chunks):")

    import time
    start = time.perf_counter()
    all_vectors = embedder.encode(chunks)
    elapsed = time.perf_counter() - start

    print(f"  Generated {len(all_vectors)} embeddings in {elapsed:.2f}s")
    print(f"  Throughput: {len(chunks) / elapsed:.0f} chunks/sec")

    return len(all_vectors) == len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test embedding pipeline")
    parser.add_argument("--local", action="store_true", help="Use local sentence-transformers instead of DJL")
    args = parser.parse_args()

    print("=" * 50)
    print("Embed Pipeline - Local Tests")
    print(f"Mode: {'LOCAL (sentence-transformers)' if args.local else 'DJL container'}")
    print("=" * 50)

    # Create embedder
    if args.local:
        embedder = LocalEmbedder(MODEL_NAME, BATCH_SIZE)
    else:
        if not DJL_URL:
            print("\nERROR: DJL_URL not set. Use --local or set DJL_URL in config.env")
            exit(1)
        print(f"DJL URL: {DJL_URL}")
        embedder = DJLEmbedder(DJL_URL, BATCH_SIZE)

    if not test_connection(embedder):
        if args.local:
            print("\nLocal embedder failed to initialize")
        else:
            print("\nDJL not available. Start it with: docker-compose up -d")
            print("Or use --local to test with sentence-transformers")
        exit(1)

    tests = [
        ("Chunking", lambda: test_chunking()),
        ("Embeddings", lambda: test_embeddings(embedder)),
        ("Full Pipeline", lambda: test_full_pipeline(embedder)),
        ("Large Batch", lambda: test_large_batch(embedder)),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append((name, False))

    print("\n" + "=" * 50)
    print("Results:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

#!/usr/bin/env python3
"""
Batch document embedder with parent/child structure and comprehensive analytics.

Reads multiple documents, chunks each, embeds, and indexes to Solr with:
- Parent collection: document metadata
- Child collection: chunks with vectors
- Detailed logging and analytics

Usage:
  python batch_embedder.py documents/ \
    --api-url "YOUR_API_URL" \
    --solr-url "http://localhost:8983/solr"
"""

import argparse
import json
import logging
import os
import time
from pathlib import Path
from collections import defaultdict
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)


class Analytics:
    """Track detailed analytics during processing."""

    def __init__(self):
        self.total_docs = 0
        self.total_chunks = 0
        self.total_chars = 0
        self.total_api_calls = 0
        self.total_api_time = 0
        self.total_solr_time = 0
        self.chunk_size_dist = defaultdict(int)  # histogram of chunk sizes
        self.doc_stats = []  # per-document stats
        self.errors = []
        self.start_time = time.perf_counter()

    def add_document(self, doc_stat: dict):
        """Add stats for a processed document."""
        self.total_docs += 1
        self.total_chunks += doc_stat["num_chunks"]
        self.total_chars += doc_stat["doc_size"]
        self.total_api_calls += doc_stat["api_calls"]
        self.total_api_time += doc_stat["api_time"]
        self.total_solr_time += doc_stat["solr_time"]
        self.doc_stats.append(doc_stat)

        # Track chunk size distribution
        for size in doc_stat["chunk_sizes"]:
            bucket = (size // 100) * 100  # Round to nearest 100
            self.chunk_size_dist[bucket] += 1

    def add_error(self, doc_id: str, error: str):
        """Record an error."""
        self.errors.append({"doc_id": doc_id, "error": error})

    def elapsed(self) -> float:
        """Total elapsed time."""
        return time.perf_counter() - self.start_time

    def print_summary(self):
        """Print comprehensive analytics summary."""
        elapsed = self.elapsed()

        log.info("=" * 70)
        log.info("ANALYTICS SUMMARY")
        log.info("=" * 70)

        # Overall stats
        log.info("DOCUMENTS:")
        log.info(f"  Total processed: {self.total_docs}")
        log.info(f"  Total characters: {self.total_chars:,}")
        log.info(f"  Average doc size: {self.total_chars // self.total_docs if self.total_docs else 0:,} chars")

        # Chunking stats
        log.info("")
        log.info("CHUNKS:")
        log.info(f"  Total chunks: {self.total_chunks:,}")
        log.info(f"  Average chunks/doc: {self.total_chunks / self.total_docs if self.total_docs else 0:.1f}")
        log.info(f"  Average chunk size: {self.total_chars // self.total_chunks if self.total_chunks else 0:,} chars")

        # Chunk size distribution
        if self.chunk_size_dist:
            log.info("")
            log.info("CHUNK SIZE DISTRIBUTION:")
            for bucket in sorted(self.chunk_size_dist.keys()):
                count = self.chunk_size_dist[bucket]
                pct = (count / self.total_chunks) * 100
                bar = "█" * int(pct / 2)
                log.info(f"  {bucket:4d}-{bucket+99:4d} chars: {count:4d} ({pct:5.1f}%) {bar}")

        # API performance
        log.info("")
        log.info("API PERFORMANCE:")
        log.info(f"  Total API calls: {self.total_api_calls:,}")
        log.info(f"  Total API time: {self.total_api_time:.2f}s")
        log.info(f"  Average API latency: {(self.total_api_time / self.total_api_calls * 1000) if self.total_api_calls else 0:.0f}ms")
        log.info(f"  API throughput: {self.total_api_calls / self.total_api_time if self.total_api_time else 0:.1f} calls/sec")

        # Solr performance
        log.info("")
        log.info("SOLR PERFORMANCE:")
        log.info(f"  Total Solr time: {self.total_solr_time:.2f}s")
        log.info(f"  Average Solr batch time: {(self.total_solr_time / self.total_docs * 1000) if self.total_docs else 0:.0f}ms")

        # Overall throughput
        log.info("")
        log.info("OVERALL:")
        log.info(f"  Total time: {elapsed:.2f}s")
        log.info(f"  Documents/sec: {self.total_docs / elapsed:.1f}")
        log.info(f"  Chunks/sec: {self.total_chunks / elapsed:.1f}")
        log.info(f"  Characters/sec: {self.total_chars / elapsed:,.0f}")

        # Time breakdown
        other_time = elapsed - self.total_api_time - self.total_solr_time
        log.info("")
        log.info("TIME BREAKDOWN:")
        log.info(f"  API calls: {self.total_api_time:.1f}s ({self.total_api_time/elapsed*100:.1f}%)")
        log.info(f"  Solr writes: {self.total_solr_time:.1f}s ({self.total_solr_time/elapsed*100:.1f}%)")
        log.info(f"  Other (I/O, chunking): {other_time:.1f}s ({other_time/elapsed*100:.1f}%)")

        # Top/bottom documents
        if len(self.doc_stats) >= 3:
            log.info("")
            log.info("TOP 3 LARGEST DOCUMENTS:")
            for stat in sorted(self.doc_stats, key=lambda x: x["doc_size"], reverse=True)[:3]:
                log.info(f"  {stat['doc_id']:20s} {stat['doc_size']:6,} chars → {stat['num_chunks']:3d} chunks")

            log.info("")
            log.info("TOP 3 MOST CHUNKS:")
            for stat in sorted(self.doc_stats, key=lambda x: x["num_chunks"], reverse=True)[:3]:
                log.info(f"  {stat['doc_id']:20s} {stat['num_chunks']:3d} chunks ({stat['doc_size']:6,} chars)")

        # Errors
        if self.errors:
            log.info("")
            log.info(f"ERRORS ({len(self.errors)}):")
            for err in self.errors[:10]:  # Show first 10
                log.info(f"  {err['doc_id']}: {err['error']}")
            if len(self.errors) > 10:
                log.info(f"  ... and {len(self.errors) - 10} more")


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


def get_embedding(text: str, api_url: str, verify_ssl: bool = True) -> tuple[list[float], float]:
    """Get embedding for a single text. Returns (vector, elapsed_time)."""
    start = time.perf_counter()
    resp = requests.post(
        api_url,
        headers={"Content-Type": "application/json"},
        json={"inputs": text},
        timeout=30,
        verify=verify_ssl,
    )
    resp.raise_for_status()
    elapsed = time.perf_counter() - start

    result = resp.json()
    if isinstance(result, list):
        vector = result
    elif isinstance(result, dict):
        vector = result.get("data", result.get("embeddings", result))
    else:
        vector = result

    return vector, elapsed


def index_parent(solr_url: str, collection: str, doc: dict) -> float:
    """Index parent document. Returns elapsed time."""
    start = time.perf_counter()
    url = f"{solr_url}/{collection}/update/json/docs?commit=false"
    resp = requests.post(url, json=doc, timeout=30)
    resp.raise_for_status()
    return time.perf_counter() - start


def index_chunks(solr_url: str, collection: str, docs: list[dict]) -> float:
    """Batch index chunk documents. Returns elapsed time."""
    start = time.perf_counter()
    url = f"{solr_url}/{collection}/update/json/docs?commit=false"
    resp = requests.post(url, json=docs, timeout=60)
    resp.raise_for_status()
    return time.perf_counter() - start


def commit(solr_url: str, collection: str) -> None:
    """Commit Solr collection."""
    url = f"{solr_url}/{collection}/update?commit=true"
    requests.get(url, timeout=60).raise_for_status()


def process_document(
    doc_path: Path,
    api_url: str,
    solr_url: str,
    parent_collection: str,
    chunk_collection: str,
    chunk_size: int,
    overlap: int,
    verify_ssl: bool = True,
    vector_field: str = "vector",
) -> dict:
    """Process a single document: chunk, embed, index. Returns stats."""

    doc_id = doc_path.stem
    doc_start = time.perf_counter()

    log.info(f"┌─ Processing: {doc_id}")
    log.info(f"│  File: {doc_path.name}")

    # Read document
    with open(doc_path, 'r', encoding='utf-8') as f:
        text = f.read()

    doc_size = len(text)
    log.info(f"│  Size: {doc_size:,} characters")

    # Chunk
    chunks = chunk_text(text, chunk_size, overlap)
    num_chunks = len(chunks)
    chunk_sizes = [len(c) for c in chunks]

    log.info(f"│  Chunks: {num_chunks}")
    log.info(f"│    Min/Avg/Max size: {min(chunk_sizes)}/{sum(chunk_sizes)//len(chunk_sizes)}/{max(chunk_sizes)} chars")

    if not chunks:
        log.warning(f"│  ⚠ No chunks generated")
        return {
            "doc_id": doc_id,
            "doc_size": doc_size,
            "num_chunks": 0,
            "chunk_sizes": [],
            "api_calls": 0,
            "api_time": 0,
            "solr_time": 0,
            "total_time": time.perf_counter() - doc_start,
            "success": False
        }

    # Index parent document
    parent_doc = {
        "id": doc_id,
        "filename": doc_path.name,
        "size": doc_size,
        "num_chunks": num_chunks,
        "min_chunk_size": min(chunk_sizes),
        "max_chunk_size": max(chunk_sizes),
        "avg_chunk_size": sum(chunk_sizes) // len(chunk_sizes),
    }
    parent_time = index_parent(solr_url, parent_collection, parent_doc)
    log.info(f"│  ✓ Parent indexed ({parent_time*1000:.0f}ms)")

    # Embed chunks and index
    chunk_docs = []
    total_api_time = 0

    log.info(f"│  Embedding {num_chunks} chunks...")
    for idx, chunk in enumerate(chunks):
        vector, api_time = get_embedding(chunk, api_url, verify_ssl)
        total_api_time += api_time

        chunk_doc = {
            "id": f"{doc_id}_chunk_{idx}",
            "parent_id": doc_id,
            "chunk_index": idx,
            "chunk_text": chunk,
            "chunk_size": len(chunk),
            vector_field: vector,
        }
        chunk_docs.append(chunk_doc)

        # Log progress for large documents
        if num_chunks > 20 and (idx + 1) % 10 == 0:
            log.info(f"│    {idx+1}/{num_chunks} chunks embedded...")

    chunk_time = index_chunks(solr_url, chunk_collection, chunk_docs)

    total_time = time.perf_counter() - doc_start

    log.info(f"│  ✓ {num_chunks} chunks indexed ({chunk_time*1000:.0f}ms)")
    log.info(f"│  API time: {total_api_time:.2f}s ({total_api_time/num_chunks*1000:.0f}ms avg)")
    log.info(f"│  Total time: {total_time:.2f}s ({num_chunks/total_time:.1f} chunks/sec)")
    log.info(f"└─ ✓ {doc_id}")
    log.info("")

    return {
        "doc_id": doc_id,
        "doc_size": doc_size,
        "num_chunks": num_chunks,
        "chunk_sizes": chunk_sizes,
        "api_calls": num_chunks,
        "api_time": total_api_time,
        "solr_time": parent_time + chunk_time,
        "total_time": total_time,
        "success": True
    }


def main():
    parser = argparse.ArgumentParser(description="Batch document embedder with analytics")
    parser.add_argument("input_dir", help="Directory containing text files")
    parser.add_argument("--api-url", required=True, help="Embedding API URL")
    parser.add_argument("--solr-url", default="http://localhost:8983/solr", help="Solr URL")
    parser.add_argument("--parent-collection", default="documents", help="Parent collection")
    parser.add_argument("--chunk-collection", default="vectors", help="Chunk collection")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size")
    parser.add_argument("--overlap", type=int, default=50, help="Chunk overlap")
    parser.add_argument("--pattern", default="*.txt", help="File pattern to match")
    parser.add_argument("--vector-field", default="vector", help="Name of vector field in Solr")
    parser.add_argument("--vector-dims", type=int, help="Vector dimensions (for logging)")
    parser.add_argument("--similarity", default="cosine", choices=["cosine", "dot_product", "euclidean"], help="Similarity function")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification for API calls")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers (default: 1 for sequential)")
    args = parser.parse_args()

    verify_ssl = not args.no_verify_ssl

    # Suppress SSL warnings if verification is disabled
    if not verify_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    log.info("=" * 70)
    log.info("BATCH DOCUMENT EMBEDDER")
    log.info("=" * 70)
    log.info(f"Input directory: {args.input_dir}")
    log.info(f"API URL: {args.api_url}")
    log.info(f"Solr: {args.solr_url}")
    log.info(f"  Parent collection: {args.parent_collection}")
    log.info(f"  Chunk collection: {args.chunk_collection}")
    log.info(f"  Vector field: {args.vector_field}")
    if args.vector_dims:
        log.info(f"  Vector dimensions: {args.vector_dims}")
    log.info(f"  Similarity function: {args.similarity}")
    log.info(f"Chunk size: {args.chunk_size}, overlap: {args.overlap}")
    log.info(f"File pattern: {args.pattern}")
    log.info("=" * 70)
    log.info("")

    # Find all documents
    input_path = Path(args.input_dir)
    doc_files = sorted(input_path.glob(args.pattern))

    if not doc_files:
        log.error(f"No files matching '{args.pattern}' found in {args.input_dir}")
        return

    log.info(f"Found {len(doc_files)} documents to process")
    if args.workers > 1:
        log.info(f"Using {args.workers} parallel workers")
    log.info("")

    # Initialize analytics
    analytics = Analytics()
    analytics_lock = threading.Lock()

    # Process documents
    if args.workers > 1:
        # Parallel processing
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            # Submit all tasks
            future_to_doc = {
                executor.submit(
                    process_document,
                    doc_path,
                    args.api_url,
                    args.solr_url,
                    args.parent_collection,
                    args.chunk_collection,
                    args.chunk_size,
                    args.overlap,
                    verify_ssl,
                    args.vector_field,
                ): doc_path for doc_path in doc_files
            }

            # Process completed tasks
            for future in as_completed(future_to_doc):
                doc_path = future_to_doc[future]
                try:
                    stats = future.result()
                    with analytics_lock:
                        if stats["success"]:
                            analytics.add_document(stats)
                        else:
                            analytics.add_error(stats["doc_id"], "No chunks generated")
                except Exception as e:
                    log.error(f"✗ Error processing {doc_path.name}: {e}")
                    log.info("")
                    with analytics_lock:
                        analytics.add_error(doc_path.stem, str(e))
    else:
        # Sequential processing (original behavior)
        for doc_path in doc_files:
            try:
                stats = process_document(
                    doc_path,
                    args.api_url,
                    args.solr_url,
                    args.parent_collection,
                    args.chunk_collection,
                    args.chunk_size,
                    args.overlap,
                    verify_ssl,
                    args.vector_field,
                )
                if stats["success"]:
                    analytics.add_document(stats)
                else:
                    analytics.add_error(stats["doc_id"], "No chunks generated")

            except Exception as e:
                log.error(f"✗ Error processing {doc_path.name}: {e}")
                log.info("")
                analytics.add_error(doc_path.stem, str(e))

    # Commit both collections
    log.info("Committing Solr collections...")
    commit(args.solr_url, args.parent_collection)
    commit(args.solr_url, args.chunk_collection)
    log.info("")

    # Print comprehensive analytics
    analytics.print_summary()


if __name__ == "__main__":
    main()

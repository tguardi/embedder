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


def chunk_text_fixed(text: str, chunk_size: int, overlap: int) -> list[str]:
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


def chunk_text_paragraph(text: str, max_tokens: int = 8000, overlap_tokens: int = 100) -> list[str]:
    """
    Split text into paragraph-based chunks for large models like BGE-M3.

    Attempts to keep paragraphs together but splits if they exceed max_tokens.
    Uses rough estimation: 1 token ≈ 4 characters for English text.

    Args:
        text: Input text to chunk
        max_tokens: Maximum tokens per chunk (default 8000 for BGE-M3)
        overlap_tokens: Overlap in tokens between chunks

    Returns:
        List of text chunks
    """
    if not text:
        return []

    # Token estimation: 1 token ≈ 4 chars
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap_tokens * chars_per_token

    # Split into paragraphs (double newline or single newline)
    paragraphs = text.split('\n\n')
    if len(paragraphs) == 1:
        # Try single newline split
        paragraphs = text.split('\n')

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_size = len(para)

        # If single paragraph exceeds max, split it with fixed chunking
        if para_size > max_chars:
            # Flush current chunk first
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            # Split large paragraph
            sub_chunks = chunk_text_fixed(para, max_chars, overlap_chars)
            chunks.extend(sub_chunks)
            continue

        # Check if adding this paragraph would exceed limit
        if current_size + para_size + 2 > max_chars and current_chunk:  # +2 for \n\n
            # Save current chunk
            chunks.append('\n\n'.join(current_chunk))

            # Start new chunk with overlap
            # Keep last paragraph(s) for overlap
            overlap_size = 0
            overlap_paras = []
            for p in reversed(current_chunk):
                if overlap_size + len(p) <= overlap_chars:
                    overlap_paras.insert(0, p)
                    overlap_size += len(p) + 2
                else:
                    break

            current_chunk = overlap_paras
            current_size = overlap_size

        current_chunk.append(para)
        current_size += para_size + 2

    # Add final chunk
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def chunk_text(text: str, chunk_size: int, overlap: int, chunker: str = "fixed") -> list[str]:
    """
    Split text into chunks using specified chunker.

    Args:
        text: Input text
        chunk_size: Size parameter (chars for fixed, tokens for paragraph)
        overlap: Overlap parameter (chars for fixed, tokens for paragraph)
        chunker: "fixed" or "paragraph"
    """
    if chunker == "paragraph":
        return chunk_text_paragraph(text, max_tokens=chunk_size, overlap_tokens=overlap)
    else:
        return chunk_text_fixed(text, chunk_size, overlap)


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


def get_embeddings_batch(texts: list[str], api_url: str, verify_ssl: bool = True) -> tuple[list[list[float]], float]:
    """
    Get embeddings for multiple texts in a single API call.

    Args:
        texts: List of texts to embed
        api_url: API endpoint
        verify_ssl: SSL verification flag

    Returns:
        (list of vectors, elapsed_time)
    """
    start = time.perf_counter()
    resp = requests.post(
        api_url,
        headers={"Content-Type": "application/json"},
        json={"inputs": texts},
        timeout=120,  # Longer timeout for batch
        verify=verify_ssl,
    )
    resp.raise_for_status()
    elapsed = time.perf_counter() - start

    result = resp.json()

    # Handle different response formats
    if isinstance(result, list):
        # Direct list of vectors
        if len(result) > 0 and isinstance(result[0], list) and isinstance(result[0][0], (int, float)):
            vectors = result
        # List of dicts with embeddings
        elif len(result) > 0 and isinstance(result[0], dict):
            vectors = [r.get("embedding", r.get("data", r)) for r in result]
        else:
            vectors = result
    elif isinstance(result, dict):
        vectors = result.get("data", result.get("embeddings", []))
    else:
        vectors = result

    return vectors, elapsed


def index_parent(solr_url: str, collection: str, doc: dict) -> float:
    """Index parent document. Returns elapsed time."""
    start = time.perf_counter()
    url = f"{solr_url}/{collection}/update/json/docs?commit=false"
    resp = requests.post(url, json=doc, timeout=30)
    resp.raise_for_status()
    return time.perf_counter() - start


def index_chunks(solr_url: str, collection: str, docs: list[dict], batch_size: int = 100) -> float:
    """
    Batch index chunk documents with configurable batch size.

    Args:
        solr_url: Solr base URL
        collection: Collection name
        docs: List of documents to index
        batch_size: Number of docs per batch (default 100)

    Returns:
        Total elapsed time
    """
    start = time.perf_counter()
    url = f"{solr_url}/{collection}/update/json/docs?commit=false"

    # Split into batches
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        resp = requests.post(url, json=batch, timeout=120)
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
    chunker: str = "fixed",
    api_batch_size: int = 1,
    solr_batch_size: int = 100,
) -> dict:
    """
    Process a single document: chunk, embed, index. Returns stats.

    Args:
        doc_path: Path to document
        api_url: Embedding API URL
        solr_url: Solr base URL
        parent_collection: Parent collection name
        chunk_collection: Chunk collection name
        chunk_size: Chunk size (chars for fixed, tokens for paragraph)
        overlap: Overlap (chars for fixed, tokens for paragraph)
        verify_ssl: SSL verification flag
        vector_field: Name of vector field in Solr
        chunker: "fixed" or "paragraph"
        api_batch_size: Number of texts per API call (1 = individual calls)
        solr_batch_size: Number of docs per Solr batch
    """

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
    chunks = chunk_text(text, chunk_size, overlap, chunker)
    num_chunks = len(chunks)
    chunk_sizes = [len(c) for c in chunks]

    log.info(f"│  Chunks: {num_chunks} ({chunker} chunker)")
    if chunk_sizes:
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
        "chunker": chunker,
    }
    parent_time = index_parent(solr_url, parent_collection, parent_doc)
    log.info(f"│  ✓ Parent indexed ({parent_time*1000:.0f}ms)")

    # Embed chunks
    chunk_docs = []
    total_api_time = 0
    num_api_calls = 0

    if api_batch_size > 1:
        # Batch API calls
        log.info(f"│  Embedding {num_chunks} chunks (batch size: {api_batch_size})...")
        for i in range(0, num_chunks, api_batch_size):
            batch_chunks = chunks[i:i + api_batch_size]
            vectors, api_time = get_embeddings_batch(batch_chunks, api_url, verify_ssl)
            total_api_time += api_time
            num_api_calls += 1

            # Create chunk documents
            for j, (chunk, vector) in enumerate(zip(batch_chunks, vectors)):
                idx = i + j
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
            if num_chunks > 50 and (i + api_batch_size) % 50 == 0:
                log.info(f"│    {min(i + api_batch_size, num_chunks)}/{num_chunks} chunks embedded...")

    else:
        # Individual API calls
        log.info(f"│  Embedding {num_chunks} chunks...")
        for idx, chunk in enumerate(chunks):
            vector, api_time = get_embedding(chunk, api_url, verify_ssl)
            total_api_time += api_time
            num_api_calls += 1

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

    # Index chunks to Solr
    chunk_time = index_chunks(solr_url, chunk_collection, chunk_docs, solr_batch_size)

    total_time = time.perf_counter() - doc_start

    log.info(f"│  ✓ {num_chunks} chunks indexed ({chunk_time*1000:.0f}ms)")
    log.info(f"│  API time: {total_api_time:.2f}s ({num_api_calls} calls, {total_api_time/num_api_calls*1000:.0f}ms avg)")
    log.info(f"│  Total time: {total_time:.2f}s ({num_chunks/total_time:.1f} chunks/sec)")
    log.info(f"└─ ✓ {doc_id}")
    log.info("")

    return {
        "doc_id": doc_id,
        "doc_size": doc_size,
        "num_chunks": num_chunks,
        "chunk_sizes": chunk_sizes,
        "api_calls": num_api_calls,
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

    # Chunking options
    parser.add_argument("--chunker", default="fixed", choices=["fixed", "paragraph"],
                       help="Chunking strategy: 'fixed' for char-based, 'paragraph' for semantic (use with large models)")
    parser.add_argument("--chunk-size", type=int, default=512,
                       help="Chunk size: characters for 'fixed', tokens for 'paragraph' (default: 512 for fixed, recommend 6000-8000 for paragraph/BGE-M3)")
    parser.add_argument("--overlap", type=int, default=50,
                       help="Overlap: characters for 'fixed', tokens for 'paragraph' (default: 50)")

    parser.add_argument("--pattern", default="*.txt", help="File pattern to match")
    parser.add_argument("--vector-field", default="vector", help="Name of vector field in Solr")
    parser.add_argument("--vector-dims", type=int, help="Vector dimensions (for logging)")
    parser.add_argument("--similarity", default="cosine", choices=["cosine", "dot_product", "euclidean"], help="Similarity function")

    # Performance options
    parser.add_argument("--api-batch-size", type=int, default=1,
                       help="Number of texts per API call (1=individual, >1=batch). Batch mode is faster but requires API support.")
    parser.add_argument("--solr-batch-size", type=int, default=100,
                       help="Number of documents per Solr batch update (default: 100)")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers (default: 1 for sequential)")
    parser.add_argument("--shard-id", type=int, help="Shard ID for distributed processing (0-based)")
    parser.add_argument("--shard-count", type=int, help="Total number of shards")

    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification for API calls")
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
    log.info(f"Chunker: {args.chunker}")
    if args.chunker == "paragraph":
        log.info(f"  Chunk size: {args.chunk_size} tokens (max), overlap: {args.overlap} tokens")
    else:
        log.info(f"  Chunk size: {args.chunk_size} chars, overlap: {args.overlap} chars")
    log.info(f"Batching: API={args.api_batch_size} texts/call, Solr={args.solr_batch_size} docs/batch")
    log.info(f"File pattern: {args.pattern}")
    log.info("=" * 70)
    log.info("")

    # Find all documents
    input_path = Path(args.input_dir)
    all_files = sorted(input_path.glob(args.pattern))

    if not all_files:
        log.error(f"No files matching '{args.pattern}' found in {args.input_dir}")
        return

    # Apply sharding if specified
    if args.shard_id is not None and args.shard_count is not None:
        if args.shard_id < 0 or args.shard_id >= args.shard_count:
            log.error(f"Invalid shard_id {args.shard_id}: must be between 0 and {args.shard_count - 1}")
            return

        # Filter documents for this shard using modulo
        doc_files = [f for i, f in enumerate(all_files) if i % args.shard_count == args.shard_id]

        log.info(f"Shard {args.shard_id}/{args.shard_count}: Processing {len(doc_files)} of {len(all_files)} total documents")
    else:
        doc_files = all_files
        log.info(f"Found {len(doc_files)} documents to process")

    if not doc_files:
        log.warning(f"No documents assigned to shard {args.shard_id}")
        return

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
                    args.chunker,
                    args.api_batch_size,
                    args.solr_batch_size,
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
                    args.chunker,
                    args.api_batch_size,
                    args.solr_batch_size,
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

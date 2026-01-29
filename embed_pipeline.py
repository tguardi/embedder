#!/usr/bin/env python3
"""
Embedding pipeline: Solr 7 → chunk → embeddings → Solr 9 (parent + chunk collections)

Supports two embedding backends:
  --local   Use sentence-transformers locally (MPS/GPU/CPU)
  (default) Use DJL container via REST API

Usage:
  python embed_pipeline.py           # Use DJL container
  python embed_pipeline.py --local   # Use local sentence-transformers
"""

import argparse
import logging
import os
import time
from typing import Generator, Protocol

import requests
from dotenv import load_dotenv
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config() -> dict:
    load_dotenv("config.env")
    return {
        "solr7_url": os.environ["SOLR7_URL"],
        "solr7_collection": os.environ["SOLR7_COLLECTION"],
        "solr7_query": os.getenv("SOLR7_QUERY", "*:*"),
        "solr9_url": os.environ["SOLR9_URL"],
        "solr9_parent_collection": os.environ["SOLR9_PARENT_COLLECTION"],
        "solr9_chunk_collection": os.environ["SOLR9_CHUNK_COLLECTION"],
        "djl_url": os.environ.get("DJL_URL", ""),
        "model_name": os.getenv("MODEL_NAME", "all-MiniLM-L6-v2"),
        "chunk_size": int(os.getenv("CHUNK_SIZE", "512")),
        "chunk_overlap": int(os.getenv("CHUNK_OVERLAP", "50")),
        "batch_size": int(os.getenv("BATCH_SIZE", "64")),
        "fetch_rows": int(os.getenv("FETCH_ROWS", "100")),
    }

# ---------------------------------------------------------------------------
# Embedding backends
# ---------------------------------------------------------------------------

class Embedder(Protocol):
    """Protocol for embedding backends."""
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class DJLEmbedder:
    """Remote DJL container backend."""

    def __init__(self, djl_url: str, batch_size: int):
        self.djl_url = djl_url
        self.batch_size = batch_size

    def encode(self, texts: list[str]) -> list[list[float]]:
        all_vectors = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            resp = requests.post(
                self.djl_url,
                json={"inputs": batch},
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json()
            # DJL returns list of vectors directly, or nested in a dict
            if isinstance(result, list):
                vectors = result
            else:
                vectors = result.get("data", result.get("embeddings", []))
            all_vectors.extend(vectors)
        return all_vectors


class LocalEmbedder:
    """Local sentence-transformers backend (MPS/GPU/CPU)."""

    def __init__(self, model_name: str, batch_size: int):
        from sentence_transformers import SentenceTransformer
        import torch

        # Select best available device
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"

        log.info("Loading model %s on device: %s", model_name, device)
        self.model = SentenceTransformer(model_name, device=device)
        self.batch_size = batch_size
        self.device = device

    def encode(self, texts: list[str]) -> list[list[float]]:
        import torch

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        # Sync MPS to ensure accurate timing
        if self.device == "mps":
            torch.mps.synchronize()

        return embeddings.tolist()


def create_embedder(local: bool, cfg: dict) -> Embedder:
    """Factory to create the appropriate embedder backend."""
    if local:
        return LocalEmbedder(cfg["model_name"], cfg["batch_size"])
    else:
        if not cfg["djl_url"]:
            raise ValueError("DJL_URL must be set when not using --local mode")
        return DJLEmbedder(cfg["djl_url"], cfg["batch_size"])

# ---------------------------------------------------------------------------
# Solr 7 reader (cursor-based)
# ---------------------------------------------------------------------------

def fetch_documents(solr7_url: str, collection: str, query: str, rows: int) -> Generator[dict, None, None]:
    """Yield all docs from Solr 7 using cursor-based pagination."""
    base = f"{solr7_url}/{collection}/select"
    cursor_mark = "*"
    total_fetched = 0

    while True:
        params = {
            "q": query,
            "rows": rows,
            "sort": "id asc",
            "cursorMark": cursor_mark,
            "wt": "json",
        }
        resp = requests.get(base, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        docs = data["response"]["docs"]
        if not docs:
            break

        for doc in docs:
            yield doc
            total_fetched += 1

        next_cursor = data.get("nextCursorMark")
        if next_cursor == cursor_mark:
            break  # no more pages
        cursor_mark = next_cursor

    log.info("Fetched %d documents from Solr 7", total_fetched)

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

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
# Solr 9 writers
# ---------------------------------------------------------------------------

def index_parent(solr9_url: str, collection: str, doc: dict) -> None:
    """Index a parent document (metadata only) to Solr 9."""
    url = f"{solr9_url}/{collection}/update/json/docs?commit=false"
    resp = requests.post(url, json=doc, timeout=30)
    resp.raise_for_status()


def index_chunks(
    solr9_url: str,
    collection: str,
    parent_id: str,
    chunks: list[str],
    vectors: list[list[float]],
    metadata: dict | None = None,
) -> None:
    """Index chunk documents (text + vector + parent_id) to Solr 9."""
    docs = []
    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
        doc = {
            "id": f"{parent_id}_chunk_{idx}",
            "parent_id": parent_id,
            "chunk_index": idx,
            "chunk_text": chunk,
            "vector": vector,
        }
        if metadata:
            doc.update(metadata)
        docs.append(doc)

    url = f"{solr9_url}/{collection}/update/json/docs?commit=false"
    resp = requests.post(url, json=docs, timeout=30)
    resp.raise_for_status()


def commit(solr9_url: str, collection: str) -> None:
    url = f"{solr9_url}/{collection}/update?commit=true"
    requests.get(url, timeout=60).raise_for_status()

# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Embedding pipeline: Solr 7 → Solr 9")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local sentence-transformers instead of DJL container",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Process documents but don't write to Solr 9",
    )
    args = parser.parse_args()

    cfg = load_config()

    # Create embedder
    embedder = create_embedder(args.local, cfg)
    backend_name = "local" if args.local else "DJL"

    log.info("Starting embedding pipeline")
    log.info("Embedding backend: %s", backend_name)
    log.info("Solr 7: %s/%s", cfg["solr7_url"], cfg["solr7_collection"])
    log.info("Solr 9 parent: %s/%s", cfg["solr9_url"], cfg["solr9_parent_collection"])
    log.info("Solr 9 chunks: %s/%s", cfg["solr9_url"], cfg["solr9_chunk_collection"])
    log.info("Chunk size: %d, overlap: %d", cfg["chunk_size"], cfg["chunk_overlap"])
    if args.dry_run:
        log.info("DRY RUN — will not write to Solr 9")

    doc_count = 0
    chunk_count = 0
    errors = 0
    start_time = time.perf_counter()

    docs = fetch_documents(
        cfg["solr7_url"], cfg["solr7_collection"], cfg["solr7_query"], cfg["fetch_rows"]
    )

    for doc in tqdm(docs, desc="Processing documents"):
        doc_id = doc.get("id")
        body = doc.get("body", "") or doc.get("content", "") or ""

        if not body:
            log.warning("Skipping doc %s — no body field", doc_id)
            continue

        try:
            # Chunk
            chunks = chunk_text(body, cfg["chunk_size"], cfg["chunk_overlap"])
            if not chunks:
                continue

            # Embed
            vectors = embedder.encode(chunks)

            if not args.dry_run:
                # Index parent (strip body, keep metadata)
                parent_doc = {k: v for k, v in doc.items() if k != "body" and k != "content"}
                index_parent(cfg["solr9_url"], cfg["solr9_parent_collection"], parent_doc)

                # Index chunks — add minimal metadata subset here if needed
                # TODO: define which metadata fields to include on chunks
                chunk_metadata = {}  # e.g. {"source": doc.get("source")}
                index_chunks(
                    cfg["solr9_url"],
                    cfg["solr9_chunk_collection"],
                    doc_id,
                    chunks,
                    vectors,
                    chunk_metadata,
                )

            doc_count += 1
            chunk_count += len(chunks)

        except Exception:
            log.exception("Error processing doc %s", doc_id)
            errors += 1

    # Commit both collections
    if not args.dry_run:
        log.info("Committing Solr 9 collections...")
        commit(cfg["solr9_url"], cfg["solr9_parent_collection"])
        commit(cfg["solr9_url"], cfg["solr9_chunk_collection"])

    elapsed = time.perf_counter() - start_time
    log.info("Done in %.1fs — %d docs, %d chunks, %d errors", elapsed, doc_count, chunk_count, errors)
    log.info("Throughput: %.0f chunks/sec", chunk_count / elapsed if elapsed > 0 else 0)


if __name__ == "__main__":
    main()

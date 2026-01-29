#!/usr/bin/env python3
"""
Test Solr 9 indexing throughput.

Creates test collections, indexes chunks with vectors, measures throughput.

Usage:
  # Start Solr first
  docker-compose up -d solr9

  # Run throughput test
  python test_solr_throughput.py
"""

import argparse
import requests
import time
from dotenv import load_dotenv
import os

load_dotenv("config.env")

SOLR9_URL = os.environ["SOLR9_URL"]
TEST_PARENT_COLLECTION = "test_parent"
TEST_CHUNK_COLLECTION = "test_chunks"
VECTOR_DIM = 384


def create_collection(solr_url: str, collection: str, num_shards: int = 1):
    """Create a Solr collection."""
    url = f"{solr_url}/admin/collections"
    params = {
        "action": "CREATE",
        "name": collection,
        "numShards": num_shards,
        "replicationFactor": 1,
    }
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 200:
        print(f"  Created collection: {collection}")
        return True
    else:
        print(f"  Collection {collection} already exists or error: {resp.text[:100]}")
        return False


def delete_collection(solr_url: str, collection: str):
    """Delete a Solr collection."""
    url = f"{solr_url}/admin/collections"
    params = {"action": "DELETE", "name": collection}
    try:
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            print(f"  Deleted collection: {collection}")
    except Exception:
        pass  # Collection might not exist


def add_vector_field(solr_url: str, collection: str, field: str = "vector", dim: int = 384):
    """Add a dense vector field to schema."""
    url = f"{solr_url}/{collection}/schema"
    payload = {
        "add-field": {
            "name": field,
            "type": "knn_vector",
            "indexed": True,
            "stored": True,
        }
    }
    # First add the field type if it doesn't exist
    field_type = {
        "add-field-type": {
            "name": "knn_vector",
            "class": "solr.DenseVectorField",
            "vectorDimension": dim,
            "similarityFunction": "cosine",
        }
    }
    try:
        requests.post(url, json=field_type, timeout=10)
    except Exception:
        pass  # Type might already exist

    resp = requests.post(url, json=payload, timeout=10)
    if resp.status_code == 200:
        print(f"  Added vector field to {collection}")
    else:
        print(f"  Vector field setup: {resp.text[:100]}")


def generate_mock_vector(dim: int = 384) -> list[float]:
    """Generate a mock embedding vector."""
    import random
    return [random.random() for _ in range(dim)]


def test_parent_indexing(solr_url: str, collection: str, num_docs: int) -> float:
    """Test parent document indexing throughput."""
    print(f"\nIndexing {num_docs} parent documents...")

    docs = []
    for i in range(num_docs):
        docs.append({
            "id": f"doc_{i}",
            "title": f"Document {i}",
            "author": "Test Author",
            "date": "2025-01-01",
            "source": "test",
        })

    start = time.perf_counter()
    url = f"{solr_url}/{collection}/update/json/docs?commit=false"
    resp = requests.post(url, json=docs, timeout=60)
    resp.raise_for_status()

    # Commit
    commit_url = f"{solr_url}/{collection}/update?commit=true"
    requests.get(commit_url, timeout=30).raise_for_status()

    elapsed = time.perf_counter() - start
    rate = num_docs / elapsed

    print(f"  Indexed {num_docs} docs in {elapsed:.2f}s")
    print(f"  Throughput: {rate:.0f} docs/sec")

    return rate


def test_chunk_indexing(solr_url: str, collection: str, num_chunks: int, batch_size: int = 100) -> float:
    """Test chunk document indexing with vectors."""
    print(f"\nIndexing {num_chunks} chunks with {VECTOR_DIM}-dim vectors (batch={batch_size})...")

    start = time.perf_counter()
    total_indexed = 0

    for batch_start in range(0, num_chunks, batch_size):
        batch_end = min(batch_start + batch_size, num_chunks)
        docs = []

        for i in range(batch_start, batch_end):
            parent_id = f"doc_{i // 10}"  # ~10 chunks per parent
            docs.append({
                "id": f"{parent_id}_chunk_{i % 10}",
                "parent_id": parent_id,
                "chunk_index": i % 10,
                "chunk_text": f"This is chunk {i} with some sample text content.",
                "vector": generate_mock_vector(VECTOR_DIM),
            })

        url = f"{solr_url}/{collection}/update/json/docs?commit=false"
        resp = requests.post(url, json=docs, timeout=60)
        resp.raise_for_status()
        total_indexed += len(docs)

        # Progress
        if (batch_start // batch_size) % 10 == 0:
            elapsed_so_far = time.perf_counter() - start
            rate = total_indexed / elapsed_so_far if elapsed_so_far > 0 else 0
            print(f"    {total_indexed}/{num_chunks} chunks ({rate:.0f} chunks/sec)")

    # Commit
    commit_start = time.perf_counter()
    commit_url = f"{solr_url}/{collection}/update?commit=true"
    requests.get(commit_url, timeout=120).raise_for_status()
    commit_time = time.perf_counter() - commit_start

    elapsed = time.perf_counter() - start
    rate = num_chunks / elapsed

    print(f"  Indexed {num_chunks} chunks in {elapsed:.2f}s (commit: {commit_time:.2f}s)")
    print(f"  Throughput: {rate:.0f} chunks/sec")
    print(f"  Throughput (excl. commit): {num_chunks / (elapsed - commit_time):.0f} chunks/sec")

    return rate


def test_end_to_end(num_docs: int = 100):
    """Simulate end-to-end: parent + chunks."""
    chunks_per_doc = 7  # Average from test_local.py
    total_chunks = num_docs * chunks_per_doc

    print(f"\nEnd-to-end simulation: {num_docs} docs, ~{chunks_per_doc} chunks/doc = {total_chunks} chunks")

    start = time.perf_counter()

    # Index parents
    print("  Indexing parents...")
    test_parent_indexing(SOLR9_URL, TEST_PARENT_COLLECTION, num_docs)

    # Index chunks
    print("  Indexing chunks...")
    test_chunk_indexing(SOLR9_URL, TEST_CHUNK_COLLECTION, total_chunks, batch_size=64)

    elapsed = time.perf_counter() - start
    print(f"\n  Total time: {elapsed:.2f}s")
    print(f"  Overall throughput: {total_chunks / elapsed:.0f} chunks/sec")


def main():
    parser = argparse.ArgumentParser(description="Test Solr 9 indexing throughput")
    parser.add_argument("--setup", action="store_true", help="Create test collections")
    parser.add_argument("--cleanup", action="store_true", help="Delete test collections")
    parser.add_argument("--num-docs", type=int, default=100, help="Number of documents to test")
    parser.add_argument("--num-chunks", type=int, default=1000, help="Number of chunks to test")
    args = parser.parse_args()

    print("=" * 60)
    print("Solr 9 Indexing Throughput Test")
    print(f"Solr URL: {SOLR9_URL}")
    print("=" * 60)

    # Check Solr connection
    try:
        resp = requests.get(f"{SOLR9_URL}/admin/info/system", timeout=5)
        resp.raise_for_status()
        print("  Solr 9 is reachable")
    except Exception as e:
        print(f"\nERROR: Cannot connect to Solr 9: {e}")
        print("Start it with: docker-compose up -d solr9")
        exit(1)

    if args.cleanup:
        print("\nCleaning up test collections...")
        delete_collection(SOLR9_URL, TEST_PARENT_COLLECTION)
        delete_collection(SOLR9_URL, TEST_CHUNK_COLLECTION)
        print("Done")
        return

    if args.setup:
        print("\nSetting up test collections...")
        delete_collection(SOLR9_URL, TEST_PARENT_COLLECTION)
        delete_collection(SOLR9_URL, TEST_CHUNK_COLLECTION)
        time.sleep(2)
        create_collection(SOLR9_URL, TEST_PARENT_COLLECTION)
        create_collection(SOLR9_URL, TEST_CHUNK_COLLECTION)
        time.sleep(2)
        add_vector_field(SOLR9_URL, TEST_CHUNK_COLLECTION, "vector", VECTOR_DIM)
        print("Setup complete")
        return

    # Run tests
    tests = [
        ("Parent docs", lambda: test_parent_indexing(SOLR9_URL, TEST_PARENT_COLLECTION, args.num_docs)),
        ("Chunks with vectors", lambda: test_chunk_indexing(SOLR9_URL, TEST_CHUNK_COLLECTION, args.num_chunks)),
    ]

    results = []
    for name, test_fn in tests:
        try:
            rate = test_fn()
            results.append((name, rate))
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append((name, 0))

    # End-to-end test
    try:
        test_end_to_end(args.num_docs)
    except Exception as e:
        print(f"  End-to-end ERROR: {e}")

    print("\n" + "=" * 60)
    print("Summary:")
    for name, rate in results:
        print(f"  {name}: {rate:.0f}/sec")


if __name__ == "__main__":
    main()

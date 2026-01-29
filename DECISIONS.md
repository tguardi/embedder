# Architecture Decisions

## Overview

This document captures the key architectural decisions for the embedding pipeline that migrates documents from Solr 7 to Solr 9 with vector embeddings.

---

## Decision 1: Dual Embedding Backend (Local vs DJL)

**Context:**
The production environment uses a DJL container running on Linux with NVIDIA GPU. However, local development happens on Apple Silicon (M4 Max) which cannot run the DJL GPU container.

**Decision:**
Support two embedding backends, selectable via `--local` flag:

| Mode | Backend | Use Case |
|------|---------|----------|
| Default | DJL container (REST API) | Production on Linux + NVIDIA GPU |
| `--local` | sentence-transformers | Development on Apple Silicon (MPS) |

**Rationale:**
- Docker on Mac runs containers in a Linux VM with no GPU access
- The `pytorch-gpu` DJL image is x86_64 + CUDA only (no ARM64 build)
- Local sentence-transformers achieves ~1,340 chunks/sec on M4 Max via MPS
- Both backends produce identical 384-dim vectors (same model)
- Enables fast local iteration without infrastructure dependencies

**Consequences:**
- Requires `torch` and `sentence-transformers` as optional dependencies
- Same chunking/indexing code path regardless of backend
- Easy to test locally, deploy to production without code changes

---

## Decision 2: Fixed-Size Chunking with Overlap

**Context:**
Documents need to be split into chunks for embedding. Various strategies exist: semantic, sentence-based, fixed-size.

**Decision:**
Use fixed character-size chunking with configurable overlap.

**Configuration:**
```
CHUNK_SIZE=512    # characters per chunk
CHUNK_OVERLAP=50  # overlap between consecutive chunks
```

**Rationale:**
- Matches existing Java implementation
- Predictable chunk counts for capacity planning
- Overlap preserves context at chunk boundaries
- Simple to implement and debug

**Trade-offs:**
- May split mid-word or mid-sentence
- Not semantically aware
- Good enough for RAG retrieval where top-k averaging handles boundary issues

---

## Decision 3: Cursor-Based Solr 7 Pagination

**Context:**
Need to read potentially millions of documents from Solr 7.

**Decision:**
Use cursor-based pagination (`cursorMark`) instead of offset-based (`start`).

**Rationale:**
- Offset pagination degrades with deep pages (Solr must skip N docs)
- Cursor pagination maintains consistent performance regardless of position
- Memory-efficient: processes one page at a time via generator

**Implementation:**
```python
def fetch_documents(...) -> Generator[dict, None, None]:
    cursor_mark = "*"
    while True:
        # fetch page with cursorMark
        # yield docs
        # update cursor_mark
```

---

## Decision 4: Two-Collection Solr 9 Schema

**Context:**
Need to store both document metadata and chunk vectors in Solr 9.

**Decision:**
Use two separate collections linked by `parent_id`:

| Collection | Contents |
|------------|----------|
| Parent | Full document metadata (no body/vectors) |
| Chunks | `parent_id`, `chunk_index`, `chunk_text`, `vector`, minimal metadata |

**Rationale:**
- Keeps vector collection lean for fast kNN search
- Parent metadata queryable separately
- Join via `parent_id` for retrieval augmentation
- Matches existing Java architecture

---

## Decision 5: Batch Processing

**Context:**
Embedding models are most efficient when processing batches of text.

**Decision:**
Batch embedding requests with configurable `BATCH_SIZE` (default: 64).

**Rationale:**
- Amortizes model overhead across multiple inputs
- GPU utilization improves with larger batches
- 64 balances throughput and memory usage

**Observed performance (M4 Max MPS):**
- Batch 32: ~1,260 chunks/sec
- Batch 64: ~1,320 chunks/sec
- Batch 128: ~1,340 chunks/sec

---

## Decision 6: Deferred Commits

**Context:**
Solr commits are expensive. Committing after every document would be slow.

**Decision:**
Index with `commit=false`, then commit once at the end of the pipeline.

**Rationale:**
- Single commit for entire batch is much faster
- Documents visible atomically after commit
- Trade-off: if pipeline crashes mid-run, no documents are visible

**Future consideration:**
Add periodic commits every N documents for very large runs.

---

## Decision 7: DJL Serving Image Selection

**Context:**
DJL offers multiple Docker images for different hardware.

**Decision:**
Use `deepjavalibrary/djl-serving:0.32.0-pytorch-gpu` for production.

**Rationale:**
- Pinned version for reproducibility
- PyTorch backend supports sentence-transformers models
- GPU support for NVIDIA hardware
- Version 0.28+ has explicit text embedding support

**Alternative images:**
- `pytorch-cpu`: For environments without GPU
- `pytorch-inf2`: For AWS Inferentia

---

## Decision 8: Solr Throughput Testing

**Context:**
Need to verify Solr 9 indexing won't be a bottleneck compared to embedding generation.

**Decision:**
Created `test_solr_throughput.py` to measure:
- Parent document indexing rate
- Chunk + vector indexing rate
- Commit overhead
- End-to-end simulation

**Expected Results:**
- Parent docs: ~5,000-10,000 docs/sec
- Chunks with 384-dim vectors: ~1,000-3,000 chunks/sec
- Embedding generation: ~1,340 chunks/sec (M4 Max MPS)

**Finding:**
Vector field indexing in Solr is comparable to embedding generation speed. For balanced throughput, both need optimization:
- Use batch indexing (done)
- Defer commits to end of run (done)
- Consider multi-shard Solr cluster for production

---

## File Structure

```
embed-pipeline/
├── config.env               # All configuration (Solr URLs, chunking params)
├── docker-compose.yml       # DJL + Solr 9 services
├── embed_pipeline.py        # Main pipeline script
├── test_local.py            # Test embedding backends
├── test_solr_throughput.py  # Measure Solr indexing performance
├── requirements.txt         # Python dependencies
├── export_docs.sh           # Combines files into combined.md
├── combined.md              # Generated single-file export
├── README.md                # Usage guide
└── DECISIONS.md             # This file
```

---

## Environment Matrix

| Environment | Embedding | How to Run |
|-------------|-----------|------------|
| Mac (dev) | Local MPS | `python embed_pipeline.py --local` |
| Mac (dev) | DJL CPU | `docker-compose up -d` then `python embed_pipeline.py` |
| Linux + GPU (prod) | DJL CUDA | `docker-compose up -d` then `python embed_pipeline.py` |

---

## Open Questions

- [ ] Chunk size and overlap values (currently placeholder 512/50)
- [ ] Which metadata fields to copy to chunk collection
- [ ] Retry/resume strategy for failed runs
- [ ] Periodic commits for very large imports

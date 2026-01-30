# Embedder - Text to Vectors Pipeline

Simple tool to process documents with your custom embedding API and index to Solr.

---

## What You Need

1. **Your embedding API endpoint** that accepts:
   ```json
   POST /your-endpoint
   {"inputs": "text"}
   ```
   And returns a vector: `[0.123, 0.456, ...]`

2. **Documents to process** (text files)

3. **Solr 9** for storage

---

## Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Start Solr

```bash
docker-compose -f docker-compose.simple.yml up -d
```

### 3. Setup Solr Collections

```bash
# Default: 384-dimensional vectors with cosine similarity
./setup_solr.sh

# Or customize for your model and field name:
VECTOR_FIELD=body-chunk-vector VECTOR_DIMS=768 SIMILARITY=cosine ./setup_solr.sh
```

This creates:
- `documents` collection (parent metadata)
- `vectors` collection (chunks with embeddings)
- Vector field with specified dimensions and similarity function

**Environment Variables:**
- `VECTOR_FIELD` - Field name for vectors (default: `vector`)
  - Example: `body-chunk-vector`, `embedding_vector`, `vec_field`
- `VECTOR_DIMS` - Vector dimensions (default: `384`)
  - Common values: `384` (MiniLM), `768` (BERT), `1536` (OpenAI)
- `SIMILARITY` - Similarity function: `cosine`, `dot_product`, or `euclidean` (default: `cosine`)

### 4. Create Test Documents

**For quick testing** (3 documents):
```bash
./setup_test_docs.sh
```

**For load testing** (10,000 documents):
```bash
python generate_batch.py --count 10000 --output batch_documents/
```

**Batch generation options:**
```bash
python generate_batch.py \
  --count 10000 \                    # Number of documents
  --output batch_documents/ \        # Output directory
  --type all                         # all, supervisory, camels, or lfbo
```

Generates realistic banking examination documents:
- **Supervisory Letter** - Federal Reserve supervisory concerns and findings
- **CAMELS Summary** - Comprehensive examination ratings and financial metrics
- **LFBO Rating Letter** - Large Financial Institution rating communication

These documents contain realistic banking terminology, regulatory citations, and examination findings.

### 5. Process Documents

```bash
# Using default field name (vector)
python batch_embedder.py test_documents/ \
  --api-url "YOUR_API_URL_HERE"

# Or match your custom field name from setup:
python batch_embedder.py test_documents/ \
  --api-url "YOUR_API_URL_HERE" \
  --vector-field body-chunk-vector \
  --vector-dims 768 \
  --similarity cosine \
  --no-verify-ssl
```

**Important:** The `--vector-field` must match the `VECTOR_FIELD` you used in `setup_solr.sh`

**That's it!** Your documents are chunked, embedded, and indexed to Solr.

---

## What Gets Logged

Unlike systems that only show doc IDs, this shows comprehensive analytics:

### Per-Document Logging:
```
┌─ Processing: doc1
│  File: doc1.txt
│  Size: 412 characters
│  Chunks: 2
│    Min/Avg/Max size: 412/412/412 chars
│  ✓ Parent indexed (15ms)
│  Embedding 2 chunks...
│  ✓ 2 chunks indexed (23ms)
│  API time: 0.45s (225ms avg)
│  Total time: 0.52s (3.8 chunks/sec)
└─ ✓ doc1
```

### Summary Analytics:
```
======================================================================
ANALYTICS SUMMARY
======================================================================
DOCUMENTS:
  Total processed: 5
  Total characters: 1,847
  Average doc size: 369 chars

CHUNKS:
  Total chunks: 12
  Average chunks/doc: 2.4
  Average chunk size: 153 chars

CHUNK SIZE DISTRIBUTION:
   100- 199 chars:    8 ( 66.7%) ████████████████████████████████
   400- 499 chars:    4 ( 33.3%) ████████████████

API PERFORMANCE:
  Total API calls: 12
  Total API time: 2.67s
  Average API latency: 222ms
  API throughput: 4.5 calls/sec

SOLR PERFORMANCE:
  Total Solr time: 0.12s
  Average Solr batch time: 24ms

OVERALL:
  Total time: 3.24s
  Documents/sec: 1.5
  Chunks/sec: 3.7
  Characters/sec: 570

TIME BREAKDOWN:
  API calls: 2.7s (82.4%)
  Solr writes: 0.1s (3.7%)
  Other (I/O, chunking): 0.5s (13.9%)
```

---

## Command Options

```bash
python batch_embedder.py INPUT_DIR \
  --api-url URL \                    # Your embedding API (required)
  --solr-url URL \                   # Solr base URL (default: localhost:8983)
  --parent-collection NAME \         # Parent collection (default: documents)
  --chunk-collection NAME \          # Chunk collection (default: vectors)
  --vector-field NAME \              # Vector field name (default: vector)
  --vector-dims 384 \                # Vector dimensions (for logging only)
  --similarity cosine \              # Similarity: cosine, dot_product, euclidean
  --chunk-size 512 \                 # Characters per chunk
  --overlap 50 \                     # Overlap between chunks
  --pattern "*.txt" \                # File pattern to match
  --no-verify-ssl                    # Disable SSL cert verification (for self-signed certs)
```

**Important:** Make sure the `--vector-field`, `--vector-dims`, and `--similarity` match what you used in `setup_solr.sh`.

---

## Solr Structure

### Parent Collection (documents)
Stores document metadata:
```json
{
  "id": "doc1",
  "filename": "doc1.txt",
  "size": 412,
  "num_chunks": 2,
  "min_chunk_size": 412,
  "max_chunk_size": 412,
  "avg_chunk_size": 412
}
```

### Chunk Collection (vectors)
Stores chunks with embeddings:
```json
{
  "id": "doc1_chunk_0",
  "parent_id": "doc1",
  "chunk_index": 0,
  "chunk_text": "Introduction to Machine Learning...",
  "chunk_size": 412,
  "vector": [0.123, 0.456, 0.789, ...]
}
```

---

## Verify Results

### Check parent documents:
```bash
curl "http://localhost:8983/solr/documents/select?q=*:*"
```

### Check chunks for a specific document:
```bash
curl "http://localhost:8983/solr/vectors/select?q=parent_id:doc1"
```

### Count total chunks:
```bash
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=0"
```

---

## Files

| File | Purpose |
|------|---------|
| `batch_embedder.py` | **Main tool** - process documents with analytics |
| `setup_solr.sh` | Create Solr collections with vector support |
| `setup_test_docs.sh` | Create sample documents for testing |
| `docker-compose.simple.yml` | Start Solr for local testing |
| `QUICKSTART.md` | Detailed usage guide |
| `DECISIONS.md` | Architecture decisions |
| `archive/` | Advanced tools (full Solr 7→9 migration, etc.) |

---

## Quick Reference

```bash
# Setup (one time)
pip install requests
docker-compose -f docker-compose.simple.yml up -d
./setup_solr.sh
./setup_test_docs.sh

# Run
python batch_embedder.py test_documents/ --api-url YOUR_URL

# Check results
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=0"
```

**Need help?** See [QUICKSTART.md](QUICKSTART.md) or `archive/` for advanced features.

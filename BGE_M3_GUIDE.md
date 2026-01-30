# BGE-M3 and Large Model Guide

Guide for using BGE-M3 and other large embedding models with paragraph chunking and batch processing.

---

## BGE-M3 Specifications

- **Max input tokens**: 8192 tokens
- **Output dimensions**: 1024
- **Best chunking strategy**: Paragraph-based (semantic boundaries)
- **Batch support**: Yes (recommended batch size: 4-8 texts)

---

## Setup for BGE-M3

### 1. Configure Solr with BGE-M3 Vector Field

```bash
# Option A: Single vector field for BGE-M3
VECTOR_FIELD=bge_m3_vector VECTOR_DIMS=1024 SIMILARITY=cosine ./setup_solr.sh

# Option B: Multiple vector fields (BGE-M3 + other models)
./setup_solr_multi_vector.sh
```

The multi-vector setup creates:
- `bge_m3_vector` (1024 dims, cosine)
- `vector` (384 dims, cosine) - for smaller models
- `large_vector` (1536 dims, cosine) - for OpenAI-sized models

### 2. Run BGE-M3 Embedder

**Basic usage with paragraph chunking:**
```bash
python batch_embedder.py batch_documents/ \
  --api-url "YOUR_BGE_M3_API_URL" \
  --vector-field bge_m3_vector \
  --vector-dims 1024 \
  --chunker paragraph \
  --chunk-size 6000 \
  --overlap 100 \
  --api-batch-size 8 \
  --workers 4 \
  --no-verify-ssl
```

**Parallel processing with sharding:**
```bash
./parallel_batch.sh batch_documents/ "YOUR_BGE_M3_API_URL" 4 4 \
  --vector-field bge_m3_vector \
  --chunker paragraph \
  --chunk-size 6000 \
  --api-batch-size 8 \
  --no-verify-ssl
```

---

## Chunking Strategies

### Fixed Chunking (for small models)

**Use when:**
- Model has small context (< 512 tokens)
- You need consistent chunk sizes
- Processing code or structured data

**Configuration:**
```bash
--chunker fixed \
--chunk-size 512 \     # characters
--overlap 50           # characters
```

**Example:** `sentence-transformers/all-MiniLM-L6-v2` (384 dims, 256 tokens max)

### Paragraph Chunking (for large models)

**Use when:**
- Model has large context (> 1000 tokens)
- You want semantic boundaries
- Processing natural language documents

**Configuration:**
```bash
--chunker paragraph \
--chunk-size 6000 \    # tokens (not characters!)
--overlap 100          # tokens
```

**How it works:**
1. Splits text on paragraph boundaries (`\n\n`)
2. Keeps paragraphs together when possible
3. Splits large paragraphs if they exceed token limit
4. Uses token estimation: 1 token ≈ 4 characters for English

**Example:** BGE-M3 (1024 dims, 8192 tokens max)

**Recommended chunk sizes:**
| Model Max Tokens | Recommended Chunk Size | Reason |
|-----------------|----------------------|--------|
| 8192 (BGE-M3) | 6000-7000 | Leave buffer for tokenization variance |
| 4096 | 3000-3500 | Safe margin |
| 2048 | 1500-1800 | Conservative approach |

---

## Batch Processing

### API Batching

Send multiple texts in a single API call for better throughput.

**API Requirements:**
Your API must accept:
```json
{
  "inputs": ["text1", "text2", "text3", ...]
}
```

And return:
```json
[
  [0.1, 0.2, ...],  // vector for text1
  [0.3, 0.4, ...],  // vector for text2
  ...
]
```

**Configuration:**
```bash
--api-batch-size 8  # Send 8 texts per API call
```

**Recommendations:**
- Small models (384d): `--api-batch-size 16-32`
- Large models (1024d): `--api-batch-size 4-8`
- Very large models (1536d): `--api-batch-size 2-4`

### Solr Batching

Batch Solr updates for better indexing performance (already optimized by default).

```bash
--solr-batch-size 100  # 100 docs per Solr batch (default)
```

**Recommendations:**
- Small documents: `--solr-batch-size 200`
- Large documents: `--solr-batch-size 50`
- Default (512 char chunks): `--solr-batch-size 100`

---

## Running Multiple Models Simultaneously

Process the same documents with different embedding models to create multiple vector representations.

### Setup

1. Configure Solr with multiple vector fields:
```bash
./setup_solr_multi_vector.sh
```

2. Set your API URLs:
```bash
export BGE_M3_URL="https://your-bge-m3-api.com/embed"
export SMALL_MODEL_URL="https://your-small-api.com/embed"
```

3. Run multi-vector batch:
```bash
./multi_vector_batch.sh batch_documents/
```

### Custom Configuration

Edit `multi_vector_batch.sh` to configure your models:

```bash
# BGE-M3 (large model with paragraph chunking)
MODEL_NAMES[0]="bge-m3"
API_URLS[0]="$BGE_M3_URL"
VECTOR_FIELDS[0]="bge_m3_vector"
CHUNKERS[0]="paragraph"
CHUNK_SIZES[0]="6000"
OVERLAPS[0]="100"
API_BATCH_SIZES[0]="8"
WORKERS[0]="4"

# Small model (fixed chunking)
MODEL_NAMES[1]="minilm"
API_URLS[1]="$SMALL_MODEL_URL"
VECTOR_FIELDS[1]="small_vector"
CHUNKERS[1]="fixed"
CHUNK_SIZES[1]="512"
OVERLAPS[1]="50"
API_BATCH_SIZES[1]="16"
WORKERS[1]="10"
```

### Benefits

- **Hybrid search**: Combine results from multiple models
- **Fallback**: Use small model for speed, large model for quality
- **Experimentation**: Compare model performance
- **Specialization**: Different models for different tasks

---

## Performance Tuning

### For BGE-M3 on M4 Max

**Recommended configuration:**
```bash
python batch_embedder.py batch_documents/ \
  --api-url "$BGE_M3_URL" \
  --vector-field bge_m3_vector \
  --chunker paragraph \
  --chunk-size 6000 \
  --overlap 100 \
  --api-batch-size 8 \
  --solr-batch-size 100 \
  --workers 4 \
  --no-verify-ssl
```

**Or use sharding for maximum performance:**
```bash
# 4 processes × 4 workers = 16 total parallel workers
./parallel_batch.sh batch_documents/ "$BGE_M3_URL" 4 4 \
  --vector-field bge_m3_vector \
  --chunker paragraph \
  --chunk-size 6000 \
  --api-batch-size 8 \
  --no-verify-ssl
```

### Tuning Parameters

**--workers** (thread-level parallelism):
- CPU cores available: Use 50-75% of cores
- M4 Max (12-16 cores): 4-8 workers
- M1 Max (10 cores): 4-6 workers

**--api-batch-size** (texts per API call):
- Limited by API memory and throughput
- Start with 8, increase if API handles it well
- Decrease if you see timeout errors

**Sharding** (process-level parallelism):
- Use when thread-level isn't enough
- M4 Max: 4 processes × 4 workers = 16 parallel
- Avoids Python GIL contention

---

## Clearing Collections

### Clear documents only (keep schema):
```bash
./clear_collections.sh
```

### Delete and recreate (for changing vector dimensions):
```bash
./clear_collections.sh --recreate

# Then setup with new dimensions
VECTOR_FIELD=bge_m3_vector VECTOR_DIMS=1024 ./setup_solr.sh
```

---

## Complete Example Workflow

### 1. Initial Setup

```bash
# Start Solr
docker-compose -f docker-compose.simple.yml up -d

# Setup multiple vector fields
./setup_solr_multi_vector.sh

# Generate 10K test documents
python generate_batch.py --count 10000 --output batch_documents/
```

### 2. Process with BGE-M3

```bash
export BGE_M3_URL="https://your-api.com/embed"

python batch_embedder.py batch_documents/ \
  --api-url "$BGE_M3_URL" \
  --vector-field bge_m3_vector \
  --vector-dims 1024 \
  --chunker paragraph \
  --chunk-size 6000 \
  --overlap 100 \
  --api-batch-size 8 \
  --workers 4 \
  --no-verify-ssl
```

### 3. Verify Results

```bash
# Check document count
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=0"

# Check a specific chunk
curl "http://localhost:8983/solr/vectors/select?q=parent_id:doc000000&fl=id,chunk_index,bge_m3_vector&rows=1"

# Check vector dimensions
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=1&fl=bge_m3_vector" | jq '.response.docs[0].bge_m3_vector | length'
```

### 4. Try Different Embedding (Optional)

```bash
# Clear only the data (keeps bge_m3_vector field)
./clear_collections.sh

# Try with different chunk size
python batch_embedder.py batch_documents/ \
  --api-url "$BGE_M3_URL" \
  --vector-field bge_m3_vector \
  --chunker paragraph \
  --chunk-size 7000 \
  --overlap 150 \
  --api-batch-size 4 \
  --workers 6 \
  --no-verify-ssl
```

---

## Troubleshooting

### Token Limit Exceeded

**Error:** API returns error about input too long

**Solution:** Reduce chunk size
```bash
--chunk-size 5000  # Reduce from 6000
```

### Out of Memory

**Error:** API or system runs out of memory

**Solution:** Reduce batch sizes
```bash
--api-batch-size 4  # Reduce from 8
--workers 2         # Reduce from 4
```

### Slow Processing

**Issue:** Processing is slower than expected

**Solutions:**
1. Increase API batch size: `--api-batch-size 16`
2. Increase workers: `--workers 8`
3. Use sharding: `./parallel_batch.sh batch_documents/ "$URL" 4 4 ...`

### API Timeout

**Error:** requests.exceptions.Timeout

**Solution:** Reduce batch size or increase timeout in code
```bash
--api-batch-size 4  # Fewer texts per call
```

---

## API Response Format Reference

Your embedding API can return vectors in several formats. The tool handles all of these:

**Format 1: Direct list**
```json
[[0.1, 0.2, ...], [0.3, 0.4, ...]]
```

**Format 2: Dict with 'data' key**
```json
{
  "data": [[0.1, 0.2, ...], [0.3, 0.4, ...]]
}
```

**Format 3: Dict with 'embeddings' key**
```json
{
  "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]]
}
```

**Format 4: List of dicts with 'embedding' key**
```json
[
  {"embedding": [0.1, 0.2, ...]},
  {"embedding": [0.3, 0.4, ...]}
]
```

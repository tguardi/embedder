# Usage Summary - Quick Reference

## For BGE-M3 (or any large model with 8k token limit)

### Setup (one time)

```bash
# Start Solr
docker-compose -f docker-compose.simple.yml up -d

# Setup with multiple vector fields (supports BGE-M3 + other models)
./setup_solr_multi_vector.sh

# Generate test documents (optional)
python generate_batch.py --count 10000 --output batch_documents/
```

### Process with BGE-M3

**Single instance:**
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

**Multiple instances with sharding (recommended for M4 Max):**
```bash
# 4 processes × 4 workers = 16 total parallel workers
./parallel_batch.sh batch_documents/ "YOUR_BGE_M3_API_URL" 4 4 \
  --vector-field bge_m3_vector \
  --chunker paragraph \
  --chunk-size 6000 \
  --api-batch-size 8 \
  --no-verify-ssl
```

---

## For Small Models (384-dim, < 512 tokens)

### Process with small model

```bash
python batch_embedder.py batch_documents/ \
  --api-url "YOUR_API_URL" \
  --vector-field vector \
  --vector-dims 384 \
  --chunker fixed \
  --chunk-size 512 \
  --overlap 50 \
  --workers 10 \
  --no-verify-ssl
```

**With sharding:**
```bash
./parallel_batch.sh batch_documents/ "YOUR_API_URL" 4 10 \
  --vector-field vector \
  --chunker fixed \
  --chunk-size 512 \
  --no-verify-ssl
```

---

## Running Multiple Models at Once

Process the same documents with different models to create multiple vector representations:

### 1. Edit multi_vector_batch.sh to configure your models

```bash
# Example configuration in multi_vector_batch.sh:

# BGE-M3
MODEL_NAMES[0]="bge-m3"
API_URLS[0]="$BGE_M3_URL"
VECTOR_FIELDS[0]="bge_m3_vector"
CHUNKERS[0]="paragraph"
CHUNK_SIZES[0]="6000"
OVERLAPS[0]="100"
API_BATCH_SIZES[0]="8"
WORKERS[0]="4"

# Small model
MODEL_NAMES[1]="small-model"
API_URLS[1]="$SMALL_MODEL_URL"
VECTOR_FIELDS[1]="small_vector"
CHUNKERS[1]="fixed"
CHUNK_SIZES[1]="512"
OVERLAPS[1]="50"
API_BATCH_SIZES[1]="1"
WORKERS[1]="10"
```

### 2. Run multi-vector batch

```bash
export BGE_M3_URL="https://your-bge-m3-api.com/embed"
export SMALL_MODEL_URL="https://your-small-api.com/embed"

./multi_vector_batch.sh batch_documents/
```

This will:
- Run both models in parallel (separate processes)
- Create `bge_m3_vector` and `small_vector` fields in same Solr collection
- Allow you to use either vector for search, or combine them for hybrid search

---

## Clearing Collections

### Clear documents only (keeps schema/vector fields):
```bash
./clear_collections.sh
```

Use this when you want to re-run embeddings with same model but different parameters.

### Delete and recreate (for changing vector dimensions):
```bash
./clear_collections.sh --recreate

# Then setup again with new dimensions
VECTOR_FIELD=new_vector VECTOR_DIMS=2048 ./setup_solr.sh
```

Use this when switching to a model with different dimensions.

---

## Key Parameters Explained

### Chunker
- `--chunker fixed`: Character-based chunks (for small models)
- `--chunker paragraph`: Semantic chunks respecting paragraph breaks (for large models)

### Chunk Size
- **Fixed chunker**: Characters (e.g., `512`)
- **Paragraph chunker**: Tokens (e.g., `6000`)
  - Rule of thumb: 1 token ≈ 4 characters for English

### API Batch Size
- `--api-batch-size 1`: One text per API call (default, compatible with all APIs)
- `--api-batch-size 8`: Send 8 texts per call (requires API support, much faster)
  - Your API must accept: `{"inputs": ["text1", "text2", ...]}`
  - And return: `[[vec1], [vec2], ...]`

### Workers
- `--workers 4`: Thread-level parallelism (4 documents at once)
- Good for I/O-bound workloads
- Recommended: 4-10 for most cases

### Sharding
- `./parallel_batch.sh ... 4 4`: 4 processes × 4 workers = 16 parallel
- Process-level parallelism (avoids Python GIL)
- Better for CPU-bound workloads
- Recommended for M4 Max: 4 processes

---

## Verification

### Check document count:
```bash
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=0"
```

### Check a specific chunk:
```bash
curl "http://localhost:8983/solr/vectors/select?q=parent_id:doc000000&rows=1&fl=id,chunk_index,bge_m3_vector"
```

### Check vector dimensions:
```bash
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=1&fl=bge_m3_vector" | jq '.response.docs[0].bge_m3_vector | length'
```

---

## Recommended Configurations

### BGE-M3 on M4 Max
```bash
./parallel_batch.sh batch_documents/ "$BGE_M3_URL" 4 4 \
  --vector-field bge_m3_vector \
  --chunker paragraph \
  --chunk-size 6000 \
  --api-batch-size 8 \
  --no-verify-ssl
```

### Small model (384d) on M4 Max
```bash
./parallel_batch.sh batch_documents/ "$API_URL" 4 10 \
  --vector-field vector \
  --chunker fixed \
  --chunk-size 512 \
  --no-verify-ssl
```

### Both models simultaneously
```bash
# Edit multi_vector_batch.sh first, then:
export BGE_M3_URL="..."
export SMALL_MODEL_URL="..."
./multi_vector_batch.sh batch_documents/
```

---

## Troubleshooting

### "Token limit exceeded" error
Reduce chunk size:
```bash
--chunk-size 5000  # Reduce from 6000
```

### API timeouts
Reduce batch size:
```bash
--api-batch-size 4  # Reduce from 8
```

### Out of memory
Reduce parallelism:
```bash
--workers 2         # Reduce from 4
--api-batch-size 4  # Reduce from 8
```

### Processing too slow
Increase parallelism:
```bash
--workers 8                    # Increase workers
--api-batch-size 16            # Increase batch size
# Or use sharding:
./parallel_batch.sh ... 4 8    # 4 processes × 8 workers
```

---

## Full Documentation

- [BGE_M3_GUIDE.md](BGE_M3_GUIDE.md) - Comprehensive guide for large models
- [QUICKSTART.md](QUICKSTART.md) - Detailed usage guide
- [README.md](README.md) - Overview and all features

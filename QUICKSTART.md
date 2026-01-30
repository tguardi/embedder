# Quick Start Guide

Text files → your custom API → Solr with parent/child structure

---

## What You Have

You have a working API endpoint:
```bash
curl -X POST YOUR_API_URL \
  -H "Content-Type: application/json" \
  -d '{"inputs": "test"}'
# Returns: [0.123, 0.456, ...]
```

## What You Need

Get embeddings for multiple documents and index them to Solr with:
- **Parent collection**: document metadata (filename, size, chunks)
- **Child collection**: chunks with vectors and parent_id linkage

---

## Setup (One Time)

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Start Solr

```bash
docker-compose -f docker-compose.simple.yml up -d
```

Wait ~10 seconds, then verify:
```bash
curl http://localhost:8983/solr/admin/info/system
```

### 3. Setup Solr Collections

**Default setup** (384-dim vectors, cosine similarity):
```bash
./setup_solr.sh
```

**Custom setup** (match your model):
```bash
VECTOR_FIELD=body-chunk-vector VECTOR_DIMS=768 SIMILARITY=cosine ./setup_solr.sh
```

This creates:
- `documents` collection (parent metadata)
- `vectors` collection (chunks with embeddings)
- Vector field with proper dimensions and similarity function

### 4. Create Test Documents

```bash
./setup_test_docs.sh
```

Generates 3 realistic banking examination documents:
- Supervisory Letter
- CAMELS Summary
- LFBO Rating Letter

---

## Run the Pipeline

**Basic usage** (with default vector field):
```bash
python batch_embedder.py test_documents/ \
  --api-url "YOUR_API_URL_HERE"
```

**With custom vector field** (matching your setup):
```bash
python batch_embedder.py test_documents/ \
  --api-url "YOUR_API_URL_HERE" \
  --vector-field body-chunk-vector \
  --vector-dims 768 \
  --similarity cosine \
  --no-verify-ssl
```

### What Happens:

1. **Finds documents** in `test_documents/`
2. **For each document:**
   - Reads the text
   - Chunks it (default 512 chars, 50 overlap)
   - Gets embeddings from your API
   - Indexes parent doc to "documents" collection
   - Indexes chunks with vectors to "vectors" collection
   - Logs detailed per-document analytics
3. **Shows comprehensive summary** with analytics

### Expected Output:

```
======================================================================
BATCH DOCUMENT EMBEDDER
======================================================================
Input directory: test_documents/
API URL: https://your-api.com/embed
Solr: http://localhost:8983/solr
  Parent collection: documents
  Chunk collection: vectors
  Vector field: body-chunk-vector
  Vector dimensions: 768
  Similarity function: cosine
Chunk size: 512, overlap: 50
File pattern: *.txt
======================================================================

Found 3 documents to process

┌─ Processing: doc1_supervisory_letter
│  File: doc1_supervisory_letter.txt
│  Size: 2,847 characters
│  Chunks: 6
│    Min/Avg/Max size: 462/474/512 chars
│  ✓ Parent indexed (18ms)
│  Embedding 6 chunks...
│  ✓ 6 chunks indexed (145ms)
│  API time: 1.23s (205ms avg)
│  Total time: 1.39s (4.3 chunks/sec)
└─ ✓ doc1_supervisory_letter

┌─ Processing: doc2_camels_summary
...

======================================================================
ANALYTICS SUMMARY
======================================================================
DOCUMENTS:
  Total processed: 3
  Total characters: 8,456
  Average doc size: 2,819 chars

CHUNKS:
  Total chunks: 18
  Average chunks/doc: 6.0
  Average chunk size: 470 chars

CHUNK SIZE DISTRIBUTION:
   400- 499 chars:   12 ( 66.7%) ████████████████████████████████
   500- 599 chars:    6 ( 33.3%) ████████████████

API PERFORMANCE:
  Total API calls: 18
  Total API time: 3.67s
  Average API latency: 204ms
  API throughput: 4.9 calls/sec

SOLR PERFORMANCE:
  Total Solr time: 0.42s
  Average Solr batch time: 140ms

TIME BREAKDOWN:
  API calls: 3.7s (82.4%)
  Solr writes: 0.4s (9.0%)
  Other (I/O, chunking): 0.4s (8.6%)
```

---

## Verify in Solr

### Check parent documents:
```bash
curl "http://localhost:8983/solr/documents/select?q=*:*&rows=10"
```

### Check chunks:
```bash
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=10"
```

### Check specific document's chunks:
```bash
curl "http://localhost:8983/solr/vectors/select?q=parent_id:doc1"
```

---

## Options

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
  --no-verify-ssl                    # Disable SSL verification for self-signed certs
```

**Important:** Match `--vector-field`, `--vector-dims`, and `--similarity` with your `setup_solr.sh` settings.

---

## Document Structure in Solr

### Parent Collection (documents)
```json
{
  "id": "doc1",
  "filename": "doc1.txt",
  "size": 412,
  "num_chunks": 2
}
```

### Chunk Collection (vectors)
```json
{
  "id": "doc1_supervisory_letter_chunk_0",
  "parent_id": "doc1_supervisory_letter",
  "chunk_index": 0,
  "chunk_text": "BOARD OF GOVERNORS OF THE FEDERAL RESERVE...",
  "chunk_size": 512,
  "body-chunk-vector": [0.123, 0.456, 0.789, ...]
}
```

Note: The vector field name (`body-chunk-vector` in this example) matches what you configured in `setup_solr.sh`.

---

## Real World Usage

### Process your own documents:

```bash
# 1. Put your text files in a directory
mkdir my_documents
cp /path/to/your/files/*.txt my_documents/

# 2. Run the pipeline
python batch_embedder.py my_documents/ \
  --api-url "https://your-api.com/embed" \
  --chunk-size 1000 \
  --overlap 100
```

### Process a large corpus:

```bash
# Larger chunks for books/articles
python batch_embedder.py books/ \
  --api-url "https://your-api.com/embed" \
  --chunk-size 2000 \
  --overlap 200 \
  --parent-collection "books" \
  --chunk-collection "book_chunks"
```

---

## Troubleshooting

**SSL Certificate Verification Error**
```bash
# Add --no-verify-ssl for self-signed certificates
python batch_embedder.py test_documents/ \
  --api-url "YOUR_API_URL" \
  --no-verify-ssl
```

**404 Error from Solr**
```bash
# Make sure you ran setup_solr.sh first
./setup_solr.sh
```

**Solr Not Running**
```bash
# Check Solr status
docker-compose -f docker-compose.simple.yml ps
curl http://localhost:8983/solr/admin/info/system

# Restart if needed
docker-compose -f docker-compose.simple.yml restart
```

**No Files Found**
```bash
# Check directory and pattern
ls test_documents/
python batch_embedder.py test_documents/ --pattern "*.md"
```

**Wrong Vector Field Name**
```bash
# Make sure --vector-field matches VECTOR_FIELD in setup
VECTOR_FIELD=body-chunk-vector ./setup_solr.sh
python batch_embedder.py test_documents/ \
  --api-url YOUR_URL \
  --vector-field body-chunk-vector
```

---

## What's Different from Full Pipeline?

| Feature | Simple Tools | Full Pipeline (embed_pipeline.py) |
|---------|--------------|----------------------------------|
| **Input** | Text files | Solr 7 collection |
| **Parent/Child** | ✅ Yes | ✅ Yes |
| **Logging** | ✅ Per-document | Basic |
| **Custom API** | ✅ Your URL | DJL container or local |
| **Dependencies** | requests, tqdm | torch, sentence-transformers |
| **Complexity** | Simple | Full-featured |

**Use simple tools when:**
- You have text files (not Solr 7)
- You have a custom embedding API
- You want minimal dependencies
- You're testing/prototyping

**Use full pipeline when:**
- You're migrating Solr 7 → Solr 9
- You want local model support
- You need autoscaling (DJL containers)

---

## Next Steps

1. ✅ Test with sample documents
2. ✅ Verify in Solr
3. Process your own documents
4. Customize chunk size for your content
5. Add more metadata fields (edit batch_embedder.py line 101-106)
6. Query vectors in Solr (vector search)

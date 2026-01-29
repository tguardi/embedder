# Quick Start - Simple Workflow

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
- **Parent collection**: document metadata (filename, size, etc.)
- **Child collection**: chunks with vectors

---

## Setup (One Time)

### 1. Install Dependencies

```bash
pip install requests tqdm
```

### 2. Start Solr

```bash
# Start Solr with auto-created collections
docker-compose -f docker-compose.simple.yml up -d

# Wait for startup (~10 seconds)
docker-compose -f docker-compose.simple.yml logs -f
```

This creates:
- Solr at http://localhost:8983
- Collection "vectors" (auto-created)

### 3. Create Test Documents

```bash
./setup_test_docs.sh
```

Creates 5 sample documents in `test_documents/`

---

## Run the Pipeline

```bash
python batch_embedder.py test_documents/ \
  --api-url "YOUR_API_URL_HERE" \
  --solr-url "http://localhost:8983/solr" \
  --parent-collection "documents" \
  --chunk-collection "vectors"
```

### What Happens:

1. **Finds documents** in `test_documents/`
2. **For each document:**
   - Reads the text
   - Chunks it (default 512 chars, 50 overlap)
   - Gets embeddings from your API
   - Indexes parent doc to "documents" collection
   - Indexes chunks to "vectors" collection
   - Logs progress
3. **Commits** both collections
4. **Shows summary**

### Expected Output:

```
============================================================
Batch Document Embedder
============================================================
Input directory: test_documents/
API URL: https://your-api.com/embed
Solr: http://localhost:8983/solr
  Parent collection: documents
  Chunk collection: vectors
Chunk size: 512, overlap: 50
============================================================
Found 5 documents

2025-01-29 10:00:00 [INFO] Processing document: doc1 (doc1.txt)
2025-01-29 10:00:00 [INFO]   Document size: 412 characters
2025-01-29 10:00:00 [INFO]   Generated 2 chunks
2025-01-29 10:00:00 [INFO]   Indexed parent document
2025-01-29 10:00:00 [INFO]   Indexed 2 chunks
2025-01-29 10:00:00 [INFO]   ✓ doc1: 2 chunks

2025-01-29 10:00:01 [INFO] Processing document: doc2 (doc2.txt)
...

============================================================
SUMMARY
============================================================
Documents processed: 5/5
Total chunks: 12
Total characters: 1,847
Time: 3.2s
Throughput: 4 chunks/sec

Document breakdown:
  doc1: 2 chunks (412 chars)
  doc2: 3 chunks (524 chars)
  doc3: 2 chunks (318 chars)
  doc4: 3 chunks (445 chars)
  doc5: 2 chunks (348 chars)
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
  --chunk-size 512 \                 # Characters per chunk
  --overlap 50 \                     # Overlap between chunks
  --pattern "*.txt"                  # File pattern to match
```

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
  "id": "doc1_chunk_0",
  "parent_id": "doc1",
  "chunk_index": 0,
  "chunk_text": "Introduction to Machine Learning...",
  "vector": [0.123, 0.456, 0.789, ...]
}
```

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

**"No files found"**
```bash
# Check directory
ls test_documents/

# Check pattern
python batch_embedder.py test_documents/ --pattern "*.md"
```

**"Connection refused" (Solr)**
```bash
# Check Solr is running
curl http://localhost:8983/solr/admin/info/system

# Restart Solr
docker-compose -f docker-compose.simple.yml restart
```

**"Connection refused" (API)**
```bash
# Test your API manually first
curl -X POST YOUR_API_URL \
  -H "Content-Type: application/json" \
  -d '{"inputs": "test"}'
```

**"Collection not found"**
```bash
# Create collections manually (Solr admin UI or API)
# Or let Solr auto-create on first write
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

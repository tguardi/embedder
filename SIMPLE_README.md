# Simple Embedder

Minimalist tool: text file → chunks → embeddings from your custom API → JSON output.

## Quick Start

### 1. Install

```bash
pip install requests tqdm
# or
pip install -r simple_requirements.txt
```

### 2. Create Input File

```bash
# Create a sample text file
cat > input.txt << 'EOF'
This is your document content.
It can be as long as you want.
Multiple paragraphs are fine.

The script will automatically chunk it.
EOF
```

### 3. Run

```bash
python simple_embedder.py input.txt output.json \
  --api-url "YOUR_API_URL_HERE"
```

**Example with your curl command:**
```bash
# If your curl works like this:
curl -X POST https://your-api.com/embed \
  -H "Content-Type: application/json" \
  -d '{"inputs": "test"}'

# Then run:
python simple_embedder.py input.txt output.json \
  --api-url "https://your-api.com/embed"
```

### 4. Check Output

```bash
cat output.json
```

Output format:
```json
{
  "metadata": {
    "input_file": "input.txt",
    "api_url": "https://...",
    "chunk_size": 512,
    "overlap": 50,
    "num_chunks": 10,
    "vector_dim": 384
  },
  "chunks": [
    {
      "text": "This is your document content...",
      "vector": [0.123, 0.456, ...]
    },
    ...
  ]
}
```

---

## Options

```bash
python simple_embedder.py input.txt output.json \
  --api-url "YOUR_URL" \
  --chunk-size 1000 \      # Characters per chunk (default: 512)
  --overlap 100 \          # Overlap between chunks (default: 50)
  --batch-size 20          # Requests per batch (default: 10)
```

---

## How It Works

1. **Read** — Loads entire text file
2. **Chunk** — Splits into fixed-size chunks with overlap
3. **Embed** — Sends each chunk to your API: `POST {"inputs": chunk}`
4. **Save** — Writes JSON with text + vectors

---

## Examples

### Process a book
```bash
python simple_embedder.py book.txt book_embeddings.json \
  --api-url "https://your-api.com/embed" \
  --chunk-size 1000
```

### Process multiple files
```bash
for file in docs/*.txt; do
  python simple_embedder.py "$file" "embeddings/$(basename $file .txt).json" \
    --api-url "https://your-api.com/embed"
done
```

### Large file (bigger chunks)
```bash
python simple_embedder.py large.txt output.json \
  --api-url "https://your-api.com/embed" \
  --chunk-size 2000 \
  --overlap 200
```

---

## API Requirements

Your API must accept:
```json
POST /your-endpoint
Content-Type: application/json

{
  "inputs": "text to embed"
}
```

And return a vector (or object containing a vector):
```json
[0.123, 0.456, 0.789, ...]
```

or
```json
{
  "data": [0.123, 0.456, ...]
}
```

---

## Troubleshooting

**"Connection refused"**
- Check API URL is correct
- Test with curl first: `curl -X POST YOUR_URL -H "Content-Type: application/json" -d '{"inputs": "test"}'`

**"Too slow"**
- Increase `--batch-size` if API can handle it
- Reduce `--chunk-size` for smaller requests
- Your API might have rate limits

**"Out of memory"**
- Process file in multiple parts
- Reduce chunk size

---

## What About Solr?

This simplified version just outputs JSON. If you need Solr integration later, use the full `embed_pipeline.py` instead.

This version is for:
- Quick testing with your new API
- Generating embeddings for offline use
- Simple batch processing

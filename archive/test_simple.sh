#!/bin/bash
# Quick test of the simple embedder workflow

set -e

API_URL="${1:-}"

if [ -z "$API_URL" ]; then
    echo "Usage: ./test_simple.sh YOUR_API_URL"
    echo ""
    echo "Example:"
    echo "  ./test_simple.sh https://your-api.com/embed"
    exit 1
fi

echo "=== Simple Embedder Test ==="
echo "API URL: $API_URL"
echo ""

# Create test input
echo "Creating test input file..."
cat > test_input.txt << 'EOF'
This is a test document for the embedding pipeline.

It contains multiple paragraphs to test the chunking functionality.
Each chunk will be sent to the embedding API and we'll get back vectors.

The simple embedder makes it easy to:
- Read text files
- Chunk them automatically
- Get embeddings from your custom API
- Save results to JSON or index to Solr

Let's see how it works!
EOF

echo "Test file created ($(wc -c < test_input.txt) bytes)"
echo ""

# Test 1: JSON output
echo "Test 1: Embedding to JSON..."
python3 simple_embedder.py test_input.txt test_output.json \
    --api-url "$API_URL" \
    --chunk-size 100 \
    --overlap 20

echo ""
echo "Output summary:"
python3 -c "import json; data=json.load(open('test_output.json')); print(f\"  Chunks: {data['metadata']['num_chunks']}\"); print(f\"  Vector dim: {data['metadata']['vector_dim']}\")"
echo ""

# Test 2: Solr (if running)
if curl -s http://localhost:8983/solr/admin/info/system > /dev/null 2>&1; then
    echo "Test 2: Embedding to Solr..."
    python3 simple_to_solr.py test_input.txt \
        --api-url "$API_URL" \
        --solr-url "http://localhost:8983/solr" \
        --collection "vectors" \
        --chunk-size 100 \
        --overlap 20 \
        --doc-id "test_doc"

    echo ""
    echo "Solr check:"
    curl -s "http://localhost:8983/solr/vectors/select?q=*:*&rows=0" | \
        python3 -c "import sys,json; print(f\"  Total docs: {json.load(sys.stdin)['response']['numFound']}\")"
else
    echo "Test 2: Skipped (Solr not running)"
    echo "  Start with: docker-compose -f docker-compose.simple.yml up -d"
fi

echo ""
echo "=== Tests Complete ==="
echo "Files created:"
echo "  - test_input.txt"
echo "  - test_output.json"

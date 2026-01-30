#!/bin/bash
# Quick test script to verify your embedding setup works

set -e

API_URL="${1:-}"
MODEL_TYPE="${2:-small}"  # small, large, or bge-m3

if [ -z "$API_URL" ]; then
    echo "Usage: $0 API_URL [MODEL_TYPE]"
    echo ""
    echo "MODEL_TYPE options:"
    echo "  small   - Small models (384d, fixed chunking)"
    echo "  large   - Large models (1536d, paragraph chunking)"
    echo "  bge-m3  - BGE-M3 (1024d, paragraph chunking)"
    echo ""
    echo "Example:"
    echo "  $0 https://your-api.com/embed small"
    echo "  $0 https://your-api.com/embed bge-m3"
    exit 1
fi

echo "========================================================================"
echo "QUICK TEST - Embedding Pipeline"
echo "========================================================================"
echo "API URL: $API_URL"
echo "Model type: $MODEL_TYPE"
echo ""

# Check if Solr is running
if ! curl -s "http://localhost:8983/solr/admin/info/system" > /dev/null 2>&1; then
    echo "✗ Solr is not running"
    echo ""
    echo "Starting Solr..."
    docker-compose -f docker-compose.simple.yml up -d
    sleep 5
fi

echo "✓ Solr is running"
echo ""

# Check if test documents exist
if [ ! -d "test_documents" ] || [ -z "$(ls -A test_documents)" ]; then
    echo "Creating test documents..."
    ./setup_test_docs.sh
    echo ""
fi

echo "✓ Test documents ready"
echo ""

# Configure based on model type
case "$MODEL_TYPE" in
    small)
        VECTOR_FIELD="vector"
        VECTOR_DIMS="384"
        CHUNKER="fixed"
        CHUNK_SIZE="512"
        OVERLAP="50"
        API_BATCH="1"
        WORKERS="2"
        ;;
    large)
        VECTOR_FIELD="large_vector"
        VECTOR_DIMS="1536"
        CHUNKER="paragraph"
        CHUNK_SIZE="6000"
        OVERLAP="100"
        API_BATCH="4"
        WORKERS="2"
        ;;
    bge-m3)
        VECTOR_FIELD="bge_m3_vector"
        VECTOR_DIMS="1024"
        CHUNKER="paragraph"
        CHUNK_SIZE="6000"
        OVERLAP="100"
        API_BATCH="8"
        WORKERS="2"
        ;;
    *)
        echo "✗ Unknown model type: $MODEL_TYPE"
        echo "  Valid options: small, large, bge-m3"
        exit 1
        ;;
esac

echo "Configuration:"
echo "  Vector field: $VECTOR_FIELD"
echo "  Dimensions: $VECTOR_DIMS"
echo "  Chunker: $CHUNKER"
echo "  Chunk size: $CHUNK_SIZE"
echo "  Overlap: $OVERLAP"
echo "  API batch size: $API_BATCH"
echo "  Workers: $WORKERS"
echo ""

# Check if collections exist, create if not
if ! curl -s "http://localhost:8983/solr/vectors/select?q=*:*&rows=0" > /dev/null 2>&1; then
    echo "Setting up Solr collections..."
    ./setup_solr_multi_vector.sh
    echo ""
fi

echo "✓ Solr collections ready"
echo ""

# Clear existing data for clean test
echo "Clearing existing vectors..."
./clear_collections.sh
echo ""

# Run embedder
echo "========================================================================"
echo "Running embedder..."
echo "========================================================================"
echo ""

python batch_embedder.py test_documents/ \
    --api-url "$API_URL" \
    --vector-field "$VECTOR_FIELD" \
    --vector-dims "$VECTOR_DIMS" \
    --chunker "$CHUNKER" \
    --chunk-size "$CHUNK_SIZE" \
    --overlap "$OVERLAP" \
    --api-batch-size "$API_BATCH" \
    --workers "$WORKERS" \
    --no-verify-ssl

echo ""
echo "========================================================================"
echo "VERIFICATION"
echo "========================================================================"

# Verify results
PARENT_COUNT=$(curl -s "http://localhost:8983/solr/documents/select?q=*:*&rows=0" | grep -o '"numFound":[0-9]*' | cut -d':' -f2)
CHUNK_COUNT=$(curl -s "http://localhost:8983/solr/vectors/select?q=*:*&rows=0" | grep -o '"numFound":[0-9]*' | cut -d':' -f2)

echo "Documents indexed: $PARENT_COUNT"
echo "Chunks indexed: $CHUNK_COUNT"
echo ""

# Check a sample vector
echo "Sample chunk (first 5 vector values):"
curl -s "http://localhost:8983/solr/vectors/select?q=*:*&rows=1&fl=id,$VECTOR_FIELD" | \
    jq -r ".response.docs[0].$VECTOR_FIELD[0:5]"

echo ""
echo "✓ Test completed successfully!"
echo ""
echo "Next steps:"
echo "  - View all documents: curl 'http://localhost:8983/solr/documents/select?q=*:*'"
echo "  - View all chunks: curl 'http://localhost:8983/solr/vectors/select?q=*:*&rows=10'"
echo "  - Query specific doc: curl 'http://localhost:8983/solr/vectors/select?q=parent_id:doc1'"
echo ""

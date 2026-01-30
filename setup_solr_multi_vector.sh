#!/bin/bash
# Setup Solr collections with multiple vector fields for different embedding models

set -e

SOLR_URL="${SOLR_URL:-http://localhost:8983/solr}"

echo "========================================================================"
echo "SETUP SOLR WITH MULTIPLE VECTOR FIELDS"
echo "========================================================================"
echo "Solr URL: $SOLR_URL"
echo ""

# Wait for Solr to be ready
echo "Waiting for Solr to be ready..."
for i in {1..30}; do
    if curl -s "$SOLR_URL/admin/info/system" > /dev/null 2>&1; then
        echo "✓ Solr is ready"
        break
    fi
    sleep 1
done

if ! curl -s "$SOLR_URL/admin/info/system" > /dev/null 2>&1; then
    echo "✗ Error: Solr is not responding"
    echo "  Make sure Solr is running: docker-compose -f docker-compose.simple.yml up -d"
    exit 1
fi

echo ""

# Detect if running in SolrCloud or standalone mode
echo "Detecting Solr mode..."
if curl -s "$SOLR_URL/admin/collections?action=LIST" 2>&1 | grep -q "Solr instance is not running in SolrCloud mode"; then
    echo "Running in standalone mode"
    STANDALONE=true
else
    echo "Running in SolrCloud mode"
    STANDALONE=false
fi

echo ""

# Create parent collection (documents)
echo "Creating 'documents' collection..."
if [ "$STANDALONE" = true ]; then
    docker exec $(docker ps -q -f ancestor=solr:9.7) solr create_core -c documents 2>/dev/null && echo "✓ Core 'documents' created" || echo "  Core 'documents' may already exist (this is OK)"
else
    if curl -s "$SOLR_URL/admin/collections?action=CREATE&name=documents&numShards=1&replicationFactor=1" | grep -q '"status":0'; then
        echo "✓ Collection 'documents' created"
    else
        echo "  Collection 'documents' may already exist (this is OK)"
    fi
fi

# Create chunk collection (vectors)
echo "Creating 'vectors' collection..."
if [ "$STANDALONE" = true ]; then
    docker exec $(docker ps -q -f ancestor=solr:9.7) solr create_core -c vectors 2>/dev/null && echo "✓ Core 'vectors' created" || echo "  Core 'vectors' may already exist (this is OK)"
else
    if curl -s "$SOLR_URL/admin/collections?action=CREATE&name=vectors&numShards=1&replicationFactor=1" | grep -q '"status":0'; then
        echo "✓ Collection 'vectors' created"
    else
        echo "  Collection 'vectors' may already exist (this is OK)"
    fi
fi

echo ""

# Define vector field configurations
# Format: "field_name:dimensions:similarity"
VECTOR_CONFIGS=(
    "vector:384:cosine"                    # Default small model
    "bge_m3_vector:1024:cosine"           # BGE-M3
    "small_vector:384:cosine"             # Alternative small model
    "large_vector:1536:cosine"            # Large model (e.g., OpenAI)
)

echo "Adding vector fields to 'vectors' collection..."
echo ""

for config in "${VECTOR_CONFIGS[@]}"; do
    IFS=':' read -r field_name dims similarity <<< "$config"

    echo "Adding field: $field_name (${dims}d, $similarity)"

    # Add field type
    curl -s -X POST "$SOLR_URL/vectors/schema" \
      -H 'Content-type:application/json' \
      -d "{
        \"add-field-type\": {
          \"name\": \"knn_vector_${dims}\",
          \"class\": \"solr.DenseVectorField\",
          \"vectorDimension\": ${dims},
          \"similarityFunction\": \"${similarity}\"
        }
      }" 2>/dev/null | grep -q '"status":0' || echo -n ""

    # Add field (ignore error if already exists)
    response=$(curl -s -X POST "$SOLR_URL/vectors/schema" \
      -H 'Content-type:application/json' \
      -d "{
        \"add-field\": {
          \"name\": \"${field_name}\",
          \"type\": \"knn_vector_${dims}\",
          \"indexed\": true,
          \"stored\": true
        }
      }" 2>/dev/null)

    if echo "$response" | grep -q '"status":0'; then
        echo "  ✓ Field '$field_name' added"
    else
        echo "  Field '$field_name' may already exist (this is OK)"
    fi
done

echo ""
echo "========================================================================"
echo "Setup Complete!"
echo "========================================================================"
echo ""
echo "Collections created:"
echo "  - documents (parent metadata)"
echo "  - vectors (chunks with embeddings)"
echo ""
echo "Vector fields available in 'vectors' collection:"
for config in "${VECTOR_CONFIGS[@]}"; do
    IFS=':' read -r field_name dims similarity <<< "$config"
    echo "  - $field_name (${dims}d, $similarity)"
done
echo ""
echo "Usage examples:"
echo ""
echo "Single model:"
echo "  python batch_embedder.py test_documents/ \\"
echo "    --api-url YOUR_URL \\"
echo "    --vector-field bge_m3_vector \\"
echo "    --chunker paragraph \\"
echo "    --chunk-size 6000 \\"
echo "    --api-batch-size 8"
echo ""
echo "Multiple models simultaneously:"
echo "  export BGE_M3_URL='https://your-bge-m3-api.com/embed'"
echo "  export SMALL_MODEL_URL='https://your-small-api.com/embed'"
echo "  ./multi_vector_batch.sh batch_documents/"
echo ""
echo "Check collections:"
echo "  curl '$SOLR_URL/admin/cores?action=STATUS'"
echo ""

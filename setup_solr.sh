#!/bin/bash
# Setup Solr collections for the embedding pipeline

set -e

SOLR_URL="${SOLR_URL:-http://localhost:8983/solr}"
VECTOR_FIELD="${VECTOR_FIELD:-vector}"
VECTOR_DIMS="${VECTOR_DIMS:-384}"
SIMILARITY="${SIMILARITY:-cosine}"

echo "Setting up Solr collections..."
echo "Solr URL: $SOLR_URL"
echo "Vector field: $VECTOR_FIELD"
echo "Vector dimensions: $VECTOR_DIMS"
echo "Similarity function: $SIMILARITY"
echo ""

# Wait for Solr to be ready
echo "Waiting for Solr to be ready..."
for i in {1..30}; do
    if curl -s "$SOLR_URL/admin/info/system" > /dev/null 2>&1; then
        echo "✓ Solr is ready"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
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
    # Standalone mode: create core
    docker exec $(docker ps -q -f ancestor=solr:9.7) solr create_core -c documents 2>/dev/null && echo "✓ Core 'documents' created" || echo "  Core 'documents' may already exist (this is OK)"
else
    # SolrCloud mode: create collection
    if curl -s "$SOLR_URL/admin/collections?action=CREATE&name=documents&numShards=1&replicationFactor=1" | grep -q '"status":0'; then
        echo "✓ Collection 'documents' created"
    else
        echo "  Collection 'documents' may already exist (this is OK)"
    fi
fi

# Create chunk collection (vectors)
echo "Creating 'vectors' collection..."
if [ "$STANDALONE" = true ]; then
    # Standalone mode: create core (may already exist from docker-compose)
    docker exec $(docker ps -q -f ancestor=solr:9.7) solr create_core -c vectors 2>/dev/null && echo "✓ Core 'vectors' created" || echo "  Core 'vectors' may already exist (this is OK)"
else
    # SolrCloud mode: create collection
    if curl -s "$SOLR_URL/admin/collections?action=CREATE&name=vectors&numShards=1&replicationFactor=1" | grep -q '"status":0'; then
        echo "✓ Collection 'vectors' created"
    else
        echo "  Collection 'vectors' may already exist (this is OK)"
    fi
fi

echo ""

# Add vector field to vectors collection
echo "Adding vector field '$VECTOR_FIELD' to 'vectors' collection..."

# First, add the field type for dense vectors
curl -X POST "$SOLR_URL/vectors/schema" \
  -H 'Content-type:application/json' \
  -d "{
    \"add-field-type\": {
      \"name\": \"knn_vector_${VECTOR_DIMS}\",
      \"class\": \"solr.DenseVectorField\",
      \"vectorDimension\": ${VECTOR_DIMS},
      \"similarityFunction\": \"${SIMILARITY}\"
    }
  }" 2>/dev/null

# Then add the vector field
curl -X POST "$SOLR_URL/vectors/schema" \
  -H 'Content-type:application/json' \
  -d "{
    \"add-field\": {
      \"name\": \"${VECTOR_FIELD}\",
      \"type\": \"knn_vector_${VECTOR_DIMS}\",
      \"indexed\": true,
      \"stored\": true
    }
  }" 2>/dev/null

echo "✓ Vector field '${VECTOR_FIELD}' added (${VECTOR_DIMS} dims, ${SIMILARITY} similarity)"

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Collections created:"
echo "  - documents (parent metadata)"
echo "  - vectors (chunks with embeddings)"
echo ""
echo "Vector configuration:"
echo "  - Field name: $VECTOR_FIELD"
echo "  - Dimensions: $VECTOR_DIMS"
echo "  - Similarity: $SIMILARITY"
echo ""
echo "You can now run:"
echo "  python batch_embedder.py test_documents/ --api-url YOUR_URL --vector-field $VECTOR_FIELD"
echo ""
echo "Check cores/collections:"
echo "  curl '$SOLR_URL/admin/cores?action=STATUS'"
echo ""

#!/bin/bash
# Setup Solr collections for the embedding pipeline

set -e

SOLR_URL="${SOLR_URL:-http://localhost:8983/solr}"

echo "Setting up Solr collections..."
echo "Solr URL: $SOLR_URL"
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

# Create parent collection (documents)
echo "Creating 'documents' collection..."
if curl -s "$SOLR_URL/admin/collections?action=CREATE&name=documents&numShards=1&replicationFactor=1" | grep -q '"status":0'; then
    echo "✓ Collection 'documents' created"
else
    echo "  Collection 'documents' may already exist (this is OK)"
fi

# Create chunk collection (vectors)
echo "Creating 'vectors' collection..."
if curl -s "$SOLR_URL/admin/collections?action=CREATE&name=vectors&numShards=1&replicationFactor=1" | grep -q '"status":0'; then
    echo "✓ Collection 'vectors' created"
else
    echo "  Collection 'vectors' may already exist (this is OK)"
fi

echo ""

# Add vector field to vectors collection
echo "Adding vector field to 'vectors' collection..."

# First, add the field type for dense vectors
curl -X POST "$SOLR_URL/vectors/schema" \
  -H 'Content-type:application/json' \
  -d '{
    "add-field-type": {
      "name": "knn_vector",
      "class": "solr.DenseVectorField",
      "vectorDimension": 384,
      "similarityFunction": "cosine"
    }
  }' 2>/dev/null

# Then add the vector field
curl -X POST "$SOLR_URL/vectors/schema" \
  -H 'Content-type:application/json' \
  -d '{
    "add-field": {
      "name": "vector",
      "type": "knn_vector",
      "indexed": true,
      "stored": true
    }
  }' 2>/dev/null

echo "✓ Vector field added"

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Collections created:"
echo "  - documents (parent metadata)"
echo "  - vectors (chunks with embeddings)"
echo ""
echo "You can now run:"
echo "  python batch_embedder.py test_documents/ --api-url YOUR_URL"
echo ""
echo "Check collections:"
echo "  curl '$SOLR_URL/admin/collections?action=LIST'"
echo ""

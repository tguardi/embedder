#!/bin/bash
# Clear all documents from Solr collections
# Use --recreate flag to fully delete and recreate collections (needed when changing vector dimensions)

SOLR_URL="${SOLR_URL:-http://localhost:8983/solr}"
RECREATE=false

# Parse arguments
if [ "$1" == "--recreate" ]; then
    RECREATE=true
fi

echo "========================================================================"
echo "CLEAR SOLR COLLECTIONS"
echo "========================================================================"
echo "Solr URL: $SOLR_URL"
if [ "$RECREATE" == "true" ]; then
    echo "Mode: DELETE AND RECREATE (for changing vector dimensions)"
else
    echo "Mode: CLEAR DOCUMENTS ONLY (keeps schema)"
fi
echo ""

# Check if Solr is running
if ! curl -s "$SOLR_URL/admin/info/system" > /dev/null 2>&1; then
    echo "✗ Error: Solr is not responding"
    echo "  Make sure Solr is running: docker-compose -f docker-compose.simple.yml up -d"
    exit 1
fi

if [ "$RECREATE" == "true" ]; then
    # Detect Solr mode (standalone vs SolrCloud)
    if curl -s "$SOLR_URL/admin/collections?action=LIST" 2>&1 | grep -q "Solr instance is not running in SolrCloud mode"; then
        STANDALONE=true
        echo "Detected: Solr Standalone mode"
    else
        STANDALONE=false
        echo "Detected: SolrCloud mode"
    fi
    echo ""

    # Delete collections/cores
    echo "Deleting 'documents' collection..."
    if [ "$STANDALONE" == "true" ]; then
        docker exec $(docker ps -q -f ancestor=solr:9.7) solr delete -c documents 2>/dev/null || echo "  (already deleted or doesn't exist)"
    else
        curl -s "$SOLR_URL/admin/collections?action=DELETE&name=documents" > /dev/null 2>&1 || echo "  (already deleted or doesn't exist)"
    fi
    echo "✓ Deleted 'documents'"

    echo "Deleting 'vectors' collection..."
    if [ "$STANDALONE" == "true" ]; then
        docker exec $(docker ps -q -f ancestor=solr:9.7) solr delete -c vectors 2>/dev/null || echo "  (already deleted or doesn't exist)"
    else
        curl -s "$SOLR_URL/admin/collections?action=DELETE&name=vectors" > /dev/null 2>&1 || echo "  (already deleted or doesn't exist)"
    fi
    echo "✓ Deleted 'vectors'"

    echo ""
    echo "========================================================================"
    echo "Collections deleted!"
    echo "========================================================================"
    echo ""
    echo "Now run setup_solr.sh with your new vector dimensions:"
    echo "  VECTOR_FIELD=vector VECTOR_DIMS=768 SIMILARITY=cosine ./setup_solr.sh"
    echo ""

else
    # Clear documents collection
    echo "Clearing 'documents' collection..."
    RESPONSE=$(curl -s "$SOLR_URL/documents/update?commit=true" \
        -H "Content-Type: text/xml" \
        --data-binary '<delete><query>*:*</query></delete>')

    if echo "$RESPONSE" | grep -q '"status":0'; then
        echo "✓ Cleared 'documents' collection"
    else
        echo "  'documents' collection may not exist or already empty"
    fi

    # Clear vectors collection
    echo "Clearing 'vectors' collection..."
    RESPONSE=$(curl -s "$SOLR_URL/vectors/update?commit=true" \
        -H "Content-Type: text/xml" \
        --data-binary '<delete><query>*:*</query></delete>')

    if echo "$RESPONSE" | grep -q '"status":0'; then
        echo "✓ Cleared 'vectors' collection"
    else
        echo "  'vectors' collection may not exist or already empty"
    fi

    echo ""
    echo "========================================================================"
    echo "Collections cleared!"
    echo "========================================================================"
    echo ""
    echo "Verify:"
    echo "  curl '$SOLR_URL/documents/select?q=*:*&rows=0'"
    echo "  curl '$SOLR_URL/vectors/select?q=*:*&rows=0'"
    echo ""
    echo "Note: This only clears documents. To change vector dimensions, use:"
    echo "  ./clear_collections.sh --recreate"
    echo ""
fi

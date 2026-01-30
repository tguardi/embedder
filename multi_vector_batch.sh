#!/bin/bash
# Run multiple embedding models simultaneously with different configurations
# Each model writes to a different vector field in the same collections

set -e

INPUT_DIR="${1:-batch_documents}"
shift || true

echo "========================================================================"
echo "MULTI-VECTOR BATCH EMBEDDER"
echo "========================================================================"
echo "Input directory: $INPUT_DIR"
echo ""
echo "This script runs multiple embedding models simultaneously."
echo "Each model uses a different vector field in Solr."
echo ""

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "✗ Error: Directory '$INPUT_DIR' not found"
    exit 1
fi

# Configuration arrays (add your models here)
declare -a MODEL_NAMES
declare -a API_URLS
declare -a VECTOR_FIELDS
declare -a CHUNKERS
declare -a CHUNK_SIZES
declare -a OVERLAPS
declare -a API_BATCH_SIZES
declare -a WORKERS

# Example configuration - customize these for your models
# BGE-M3 (large model with paragraph chunking)
MODEL_NAMES[0]="bge-m3"
API_URLS[0]="${BGE_M3_URL:-}"
VECTOR_FIELDS[0]="bge_m3_vector"
CHUNKERS[0]="paragraph"
CHUNK_SIZES[0]="6000"  # tokens
OVERLAPS[0]="100"      # tokens
API_BATCH_SIZES[0]="8"
WORKERS[0]="4"

# Smaller model (fixed chunking)
MODEL_NAMES[1]="small-model"
API_URLS[1]="${SMALL_MODEL_URL:-}"
VECTOR_FIELDS[1]="small_vector"
CHUNKERS[1]="fixed"
CHUNK_SIZES[1]="512"   # chars
OVERLAPS[1]="50"       # chars
API_BATCH_SIZES[1]="1"
WORKERS[1]="10"

# Check which models are configured
ACTIVE_MODELS=()
for i in "${!MODEL_NAMES[@]}"; do
    if [ -n "${API_URLS[$i]}" ]; then
        ACTIVE_MODELS+=($i)
        echo "Model $((i+1)): ${MODEL_NAMES[$i]}"
        echo "  API URL: ${API_URLS[$i]}"
        echo "  Vector field: ${VECTOR_FIELDS[$i]}"
        echo "  Chunker: ${CHUNKERS[$i]}"
        echo "  Chunk size: ${CHUNK_SIZES[$i]} (${CHUNKERS[$i] == 'paragraph' && echo 'tokens' || echo 'chars'})"
        echo "  Overlap: ${OVERLAPS[$i]}"
        echo "  API batch size: ${API_BATCH_SIZES[$i]}"
        echo "  Workers: ${WORKERS[$i]}"
        echo ""
    fi
done

if [ ${#ACTIVE_MODELS[@]} -eq 0 ]; then
    echo "✗ Error: No models configured"
    echo ""
    echo "Set environment variables for your APIs:"
    echo "  export BGE_M3_URL='https://your-bge-m3-api.com/embed'"
    echo "  export SMALL_MODEL_URL='https://your-small-api.com/embed'"
    echo ""
    echo "Or edit this script to configure models directly."
    exit 1
fi

echo "========================================================================"
echo "Starting ${#ACTIVE_MODELS[@]} embedding processes..."
echo "========================================================================"
echo ""

# Create logs directory
mkdir -p logs

# Array to store PIDs
PIDS=()

# Launch each model's embedder in background
for idx in "${ACTIVE_MODELS[@]}"; do
    MODEL="${MODEL_NAMES[$idx]}"
    LOG_FILE="logs/multi_vector_${MODEL}.log"

    echo "Starting $MODEL (logging to $LOG_FILE)..."

    python batch_embedder.py "$INPUT_DIR" \
        --api-url "${API_URLS[$idx]}" \
        --chunk-collection "vectors" \
        --vector-field "${VECTOR_FIELDS[$idx]}" \
        --chunker "${CHUNKERS[$idx]}" \
        --chunk-size "${CHUNK_SIZES[$idx]}" \
        --overlap "${OVERLAPS[$idx]}" \
        --api-batch-size "${API_BATCH_SIZES[$idx]}" \
        --workers "${WORKERS[$idx]}" \
        --no-verify-ssl \
        "$@" \
        > "$LOG_FILE" 2>&1 &

    PIDS+=($!)
    echo "  $MODEL started (PID: ${PIDS[-1]})"
done

echo ""
echo "All models launched. Waiting for completion..."
echo "Monitor progress: tail -f logs/multi_vector_*.log"
echo ""

# Wait for all processes to complete
EXIT_CODES=()
for idx in "${!ACTIVE_MODELS[@]}"; do
    model_idx="${ACTIVE_MODELS[$idx]}"
    model="${MODEL_NAMES[$model_idx]}"
    pid="${PIDS[$idx]}"

    echo "Waiting for $model (PID: $pid)..."
    wait $pid
    EXIT_CODES[$idx]=$?

    if [ ${EXIT_CODES[$idx]} -eq 0 ]; then
        echo "  ✓ $model completed successfully"
    else
        echo "  ✗ $model failed with exit code ${EXIT_CODES[$idx]}"
    fi
done

echo ""
echo "========================================================================"
echo "MULTI-VECTOR BATCH COMPLETE"
echo "========================================================================"

# Check for failures
FAILURES=0
for idx in "${!EXIT_CODES[@]}"; do
    if [ ${EXIT_CODES[$idx]} -ne 0 ]; then
        ((FAILURES++))
    fi
done

if [ $FAILURES -eq 0 ]; then
    echo "✓ All models completed successfully"
    echo ""
    echo "Vector fields created in Solr 'vectors' collection:"
    for idx in "${ACTIVE_MODELS[@]}"; do
        echo "  - ${VECTOR_FIELDS[$idx]} (${MODEL_NAMES[$idx]})"
    done
    echo ""
    echo "View logs:"
    for idx in "${ACTIVE_MODELS[@]}"; do
        echo "  logs/multi_vector_${MODEL_NAMES[$idx]}.log"
    done
    exit 0
else
    echo "✗ $FAILURES model(s) failed"
    echo ""
    echo "Check logs for errors:"
    for idx in "${!ACTIVE_MODELS[@]}"; do
        if [ ${EXIT_CODES[$idx]} -ne 0 ]; then
            model_idx="${ACTIVE_MODELS[$idx]}"
            echo "  logs/multi_vector_${MODEL_NAMES[$model_idx]}.log (FAILED)"
        fi
    done
    exit 1
fi

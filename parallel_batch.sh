#!/bin/bash
# Run multiple batch_embedder.py instances in parallel using modulo sharding
# Each instance processes documents where (doc_number % num_instances) == instance_id

set -e

# Configuration
INPUT_DIR="${1:-batch_documents}"
API_URL="${2:-}"
NUM_INSTANCES="${3:-4}"
WORKERS_PER_INSTANCE="${4:-10}"

if [ -z "$API_URL" ]; then
    echo "Usage: $0 INPUT_DIR API_URL [NUM_INSTANCES] [WORKERS_PER_INSTANCE]"
    echo ""
    echo "Example:"
    echo "  $0 batch_documents/ https://api.example.com/embed 4 10"
    echo ""
    echo "Defaults:"
    echo "  NUM_INSTANCES: 4"
    echo "  WORKERS_PER_INSTANCE: 10"
    echo ""
    exit 1
fi

# Additional arguments (pass through to batch_embedder.py)
EXTRA_ARGS="${@:5}"

echo "========================================================================"
echo "PARALLEL BATCH EMBEDDER"
echo "========================================================================"
echo "Input directory: $INPUT_DIR"
echo "API URL: $API_URL"
echo "Number of instances: $NUM_INSTANCES"
echo "Workers per instance: $WORKERS_PER_INSTANCE"
echo "Total parallel workers: $((NUM_INSTANCES * WORKERS_PER_INSTANCE))"
echo "Extra args: $EXTRA_ARGS"
echo "========================================================================"
echo ""

# Create logs directory
mkdir -p logs

# Array to store PIDs
PIDS=()

# Launch instances
for instance_id in $(seq 0 $((NUM_INSTANCES - 1))); do
    LOG_FILE="logs/instance_${instance_id}.log"

    echo "Starting instance $instance_id (logging to $LOG_FILE)..."

    # Launch in background with modulo sharding
    python batch_embedder.py "$INPUT_DIR" \
        --api-url "$API_URL" \
        --workers "$WORKERS_PER_INSTANCE" \
        --shard-id "$instance_id" \
        --shard-count "$NUM_INSTANCES" \
        $EXTRA_ARGS \
        > "$LOG_FILE" 2>&1 &

    PIDS+=($!)
    echo "  Instance $instance_id started (PID: ${PIDS[$instance_id]})"
done

echo ""
echo "All instances launched. Waiting for completion..."
echo "Monitor progress: tail -f logs/instance_*.log"
echo ""

# Wait for all instances to complete
EXIT_CODES=()
for instance_id in $(seq 0 $((NUM_INSTANCES - 1))); do
    pid=${PIDS[$instance_id]}
    echo "Waiting for instance $instance_id (PID: $pid)..."
    wait $pid
    EXIT_CODES[$instance_id]=$?

    if [ ${EXIT_CODES[$instance_id]} -eq 0 ]; then
        echo "  ✓ Instance $instance_id completed successfully"
    else
        echo "  ✗ Instance $instance_id failed with exit code ${EXIT_CODES[$instance_id]}"
    fi
done

echo ""
echo "========================================================================"
echo "PARALLEL BATCH COMPLETE"
echo "========================================================================"

# Check for failures
FAILURES=0
for instance_id in $(seq 0 $((NUM_INSTANCES - 1))); do
    if [ ${EXIT_CODES[$instance_id]} -ne 0 ]; then
        ((FAILURES++))
    fi
done

if [ $FAILURES -eq 0 ]; then
    echo "✓ All instances completed successfully"
    echo ""
    echo "View individual logs:"
    for instance_id in $(seq 0 $((NUM_INSTANCES - 1))); do
        echo "  logs/instance_${instance_id}.log"
    done
    exit 0
else
    echo "✗ $FAILURES instance(s) failed"
    echo ""
    echo "Check logs for errors:"
    for instance_id in $(seq 0 $((NUM_INSTANCES - 1))); do
        if [ ${EXIT_CODES[$instance_id]} -ne 0 ]; then
            echo "  logs/instance_${instance_id}.log (FAILED)"
        fi
    done
    exit 1
fi

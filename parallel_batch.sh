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
    python3 batch_embedder.py "$INPUT_DIR" \
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

# Aggregate metrics from all instances
echo ""
echo "AGGREGATED METRICS:"
echo "------------------------------------------------------------------------"

TOTAL_DOCS=0
TOTAL_CHUNKS=0
TOTAL_TIME=0
TOTAL_API_CALLS=0
TOTAL_API_TIME=0
AVG_API_LATENCY=0
DOCS_PER_SEC=0
CHUNKS_PER_SEC=0

for instance_id in $(seq 0 $((NUM_INSTANCES - 1))); do
    LOG_FILE="logs/instance_${instance_id}.log"
    if [ -f "$LOG_FILE" ]; then
        # Extract metrics from each log
        # Log format: "2026-02-02 10:15:23 [INFO]   Total processed: 100"
        # Use awk with colon as additional delimiter to get value after ":"
        DOCS=$(grep "Total processed:" "$LOG_FILE" | tail -1 | awk -F':' '{print $NF}' | tr -d ' ')
        CHUNKS=$(grep "Total chunks:" "$LOG_FILE" | tail -1 | awk -F':' '{print $NF}' | tr -d ' ,' )
        TIME=$(grep "Total time:" "$LOG_FILE" | tail -1 | awk -F':' '{print $NF}' | tr -d ' s')
        API_CALLS=$(grep "Total API calls:" "$LOG_FILE" | tail -1 | awk -F':' '{print $NF}' | tr -d ' ,')
        API_TIME=$(grep "Total API time:" "$LOG_FILE" | tail -1 | awk -F':' '{print $NF}' | tr -d ' s')

        # Accumulate (handle empty values)
        TOTAL_DOCS=$((TOTAL_DOCS + ${DOCS:-0}))
        TOTAL_CHUNKS=$((TOTAL_CHUNKS + ${CHUNKS:-0}))
        TOTAL_API_CALLS=$((TOTAL_API_CALLS + ${API_CALLS:-0}))

        # For float values, use bc if available, otherwise accumulate manually
        if [ -n "$TIME" ]; then
            TOTAL_TIME=$(echo "$TOTAL_TIME + $TIME" | bc 2>/dev/null || echo "$TOTAL_TIME")
        fi
        if [ -n "$API_TIME" ]; then
            TOTAL_API_TIME=$(echo "$TOTAL_API_TIME + $API_TIME" | bc 2>/dev/null || echo "$TOTAL_API_TIME")
        fi
    fi
done

# Calculate aggregate metrics (use the longest instance time as total time)
MAX_TIME=0
for instance_id in $(seq 0 $((NUM_INSTANCES - 1))); do
    LOG_FILE="logs/instance_${instance_id}.log"
    if [ -f "$LOG_FILE" ]; then
        TIME=$(grep "Total time:" "$LOG_FILE" | tail -1 | awk -F':' '{print $NF}' | tr -d ' s')
        if [ -n "$TIME" ]; then
            # Compare times (convert to integer milliseconds for comparison)
            TIME_MS=$(echo "$TIME * 1000" | bc 2>/dev/null | cut -d. -f1)
            MAX_TIME_MS=$(echo "$MAX_TIME * 1000" | bc 2>/dev/null | cut -d. -f1)
            if [ "${TIME_MS:-0}" -gt "${MAX_TIME_MS:-0}" ]; then
                MAX_TIME=$TIME
            fi
        fi
    fi
done

# Calculate throughput metrics
if [ -n "$MAX_TIME" ] && [ "$(echo "$MAX_TIME > 0" | bc 2>/dev/null)" == "1" ]; then
    DOCS_PER_SEC=$(echo "scale=1; $TOTAL_DOCS / $MAX_TIME" | bc 2>/dev/null)
    CHUNKS_PER_SEC=$(echo "scale=1; $TOTAL_CHUNKS / $MAX_TIME" | bc 2>/dev/null)
fi

if [ "$TOTAL_API_CALLS" -gt 0 ] && [ -n "$TOTAL_API_TIME" ] && [ "$(echo "$TOTAL_API_TIME > 0" | bc 2>/dev/null)" == "1" ]; then
    AVG_API_LATENCY=$(echo "scale=0; ($TOTAL_API_TIME / $TOTAL_API_CALLS) * 1000" | bc 2>/dev/null)
fi

# Print summary
echo "Configuration: $NUM_INSTANCES instances × $WORKERS_PER_INSTANCE workers = $((NUM_INSTANCES * WORKERS_PER_INSTANCE)) total workers"
echo ""
echo "Documents processed:    $TOTAL_DOCS"
echo "Total chunks:           $TOTAL_CHUNKS"
echo "Wall-clock time:        ${MAX_TIME}s"
echo ""
echo "Throughput:"
echo "  Documents/sec:        ${DOCS_PER_SEC}"
echo "  Chunks/sec:           ${CHUNKS_PER_SEC}"
echo ""
echo "API Performance:"
echo "  Total API calls:      $TOTAL_API_CALLS"
echo "  Total API time:       ${TOTAL_API_TIME}s"
echo "  Avg API latency:      ${AVG_API_LATENCY}ms"
echo ""
echo "------------------------------------------------------------------------"

# Save to run history CSV
HISTORY_FILE="run_history.csv"

# Create or upgrade header if needed
if [ ! -f "$HISTORY_FILE" ]; then
    echo "timestamp,input_dir,instances,workers,total_workers,batch_size,chunk_size,overlap,docs,chunks,wall_time_sec,docs_per_sec,chunks_per_sec,api_calls,api_time_sec,api_latency_ms,status" > "$HISTORY_FILE"
else
    if ! head -1 "$HISTORY_FILE" | grep -q "chunk_size"; then
        TMP_HISTORY="$(mktemp)"
        echo "timestamp,input_dir,instances,workers,total_workers,batch_size,chunk_size,overlap,docs,chunks,wall_time_sec,docs_per_sec,chunks_per_sec,api_calls,api_time_sec,api_latency_ms,status" > "$TMP_HISTORY"
        tail -n +2 "$HISTORY_FILE" | awk -F',' 'BEGIN{OFS=","} {print $1,$2,$3,$4,$5,$6,"","",$7,$8,$9,$10,$11,$12,$13,$14,$15}' >> "$TMP_HISTORY"
        mv "$TMP_HISTORY" "$HISTORY_FILE"
    fi
fi

# Extract batch size, chunk size, overlap from EXTRA_ARGS (if present)
BATCH_SIZE=""
CHUNK_SIZE=""
OVERLAP=""
ARGS=($EXTRA_ARGS)
for ((i=0; i<${#ARGS[@]}; i++)); do
    case "${ARGS[i]}" in
        --api-batch-size) BATCH_SIZE="${ARGS[i+1]}";;
        --chunk-size) CHUNK_SIZE="${ARGS[i+1]}";;
        --overlap) OVERLAP="${ARGS[i+1]}";;
        --api-batch-size=*) BATCH_SIZE="${ARGS[i]#*=}";;
        --chunk-size=*) CHUNK_SIZE="${ARGS[i]#*=}";;
        --overlap=*) OVERLAP="${ARGS[i]#*=}";;
    esac
done
BATCH_SIZE=${BATCH_SIZE:-1}   # Default to 1 if not specified
CHUNK_SIZE=${CHUNK_SIZE:-512} # batch_embedder default
OVERLAP=${OVERLAP:-50}        # batch_embedder default

# Determine status
if [ $FAILURES -eq 0 ]; then
    STATUS="success"
else
    STATUS="failed"
fi

# Append run data
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "$TIMESTAMP,$INPUT_DIR,$NUM_INSTANCES,$WORKERS_PER_INSTANCE,$((NUM_INSTANCES * WORKERS_PER_INSTANCE)),$BATCH_SIZE,$CHUNK_SIZE,$OVERLAP,$TOTAL_DOCS,$TOTAL_CHUNKS,$MAX_TIME,$DOCS_PER_SEC,$CHUNKS_PER_SEC,$TOTAL_API_CALLS,$TOTAL_API_TIME,$AVG_API_LATENCY,$STATUS" >> "$HISTORY_FILE"

echo ""
echo "📊 Run logged to $HISTORY_FILE"
echo ""

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

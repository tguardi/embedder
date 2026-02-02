#!/bin/bash
# View and analyze benchmark run history
#
# Usage: ./view_run_history.sh [options]
#
# Options:
#   --all         Show all runs
#   --last N      Show last N runs (default: 10)
#   --top         Show top 5 fastest runs by docs/sec
#   --csv         Output in CSV format (for importing to spreadsheet)

HISTORY_FILE="run_history.csv"

if [ ! -f "$HISTORY_FILE" ]; then
    echo "No run history found. Run some benchmarks first!"
    exit 1
fi

MODE="${1:---last}"
ARG="${2:-10}"

HEADER=$(head -1 "$HISTORY_FILE")
if echo "$HEADER" | grep -q "chunk_size"; then
    HAS_CHUNK=1
    COL_DOCS_PER_SEC=12
    COL_CHUNKS_PER_SEC=13
    COL_API_LATENCY=16
else
    HAS_CHUNK=0
    COL_DOCS_PER_SEC=10
    COL_CHUNKS_PER_SEC=11
    COL_API_LATENCY=14
fi

case "$MODE" in
    --all)
        echo "========================================================================"
        echo "ALL BENCHMARK RUNS"
        echo "========================================================================"
        echo ""
        cat "$HISTORY_FILE" | column -t -s ','
        ;;

    --last)
        echo "========================================================================"
        echo "LAST $ARG BENCHMARK RUNS"
        echo "========================================================================"
        echo ""
        head -1 "$HISTORY_FILE" > /tmp/history_header.csv
        tail -n "$ARG" "$HISTORY_FILE" >> /tmp/history_header.csv
        cat /tmp/history_header.csv | column -t -s ','
        rm /tmp/history_header.csv
        ;;

    --top)
        echo "========================================================================"
        echo "TOP 5 FASTEST RUNS (by docs/sec)"
        echo "========================================================================"
        echo ""
        (head -1 "$HISTORY_FILE"; tail -n +2 "$HISTORY_FILE" | sort -t',' -k${COL_DOCS_PER_SEC} -rn | head -5) | column -t -s ','
        ;;

    --csv)
        cat "$HISTORY_FILE"
        ;;

    --compare)
        echo "========================================================================"
        echo "RUN COMPARISON (Recent Runs)"
        echo "========================================================================"
        echo ""
        echo "Configuration Performance Summary:"
        echo ""
        tail -n +2 "$HISTORY_FILE" | awk -F',' \
        -v docs_col="$COL_DOCS_PER_SEC" \
        -v chunks_col="$COL_CHUNKS_PER_SEC" \
        -v api_col="$COL_API_LATENCY" \
        -v has_chunk="$HAS_CHUNK" '
        {
            if (has_chunk == 1) {
                config = $3 "x" $4 "xB" $6 "xC" $7 "xO" $8
            } else {
                config = $3 "x" $4 "xB" $6
            }
            if (docs_per_sec[config] == "" || $(docs_col) > docs_per_sec[config]) {
                instances[config] = $3
                workers[config] = $4
                batch[config] = $6
                docs_per_sec[config] = $(docs_col)
                chunks_per_sec[config] = $(chunks_col)
                api_latency[config] = $(api_col)
            }
        }
        END {
            printf "%-15s | %8s | %10s | %12s\n", "Config", "Docs/sec", "Chunks/sec", "API Latency"
            printf "%-15s-+-%8s-+-%10s-+-%12s\n", "---------------", "--------", "----------", "------------"
            for (c in docs_per_sec) {
                printf "%-15s | %8.1f | %10.1f | %9sms\n", c, docs_per_sec[c], chunks_per_sec[c], api_latency[c]
            }
        }
        ' | sort -t'|' -k2 -rn
        ;;

    --stats)
        echo "========================================================================"
        echo "RUN STATISTICS"
        echo "========================================================================"
        echo ""

        TOTAL_RUNS=$(tail -n +2 "$HISTORY_FILE" | wc -l | tr -d ' ')
        SUCCESSFUL=$(tail -n +2 "$HISTORY_FILE" | grep -c "success")
        FAILED=$(tail -n +2 "$HISTORY_FILE" | grep -c "failed")

        echo "Total runs: $TOTAL_RUNS"
        echo "Successful: $SUCCESSFUL"
        echo "Failed: $FAILED"
        echo ""

        # Calculate stats using awk
        tail -n +2 "$HISTORY_FILE" | grep "success" | awk -F',' -v docs_col="$COL_DOCS_PER_SEC" '
        BEGIN {
            max_docs_sec = 0
            min_docs_sec = 999999
            sum_docs_sec = 0
            count = 0
        }
        {
            if ($(docs_col) != "" && $(docs_col) > 0) {
                docs_sec = $(docs_col)
                sum_docs_sec += docs_sec
                if (docs_sec > max_docs_sec) max_docs_sec = docs_sec
                if (docs_sec < min_docs_sec) min_docs_sec = docs_sec
                count++
            }
        }
        END {
            if (count > 0) {
                avg = sum_docs_sec / count
                printf "Documents/sec:\n"
                printf "  Best:    %.1f\n", max_docs_sec
                printf "  Worst:   %.1f\n", min_docs_sec
                printf "  Average: %.1f\n", avg
            }
        }
        '
        ;;

    --help)
        cat << 'EOF'
Usage: ./view_run_history.sh [options]

Options:
  --all           Show all runs in history
  --last N        Show last N runs (default: 10)
  --top           Show top 5 fastest runs by docs/sec
  --compare       Compare different configurations
  --stats         Show statistics across all runs
  --csv           Output raw CSV (for import to spreadsheet)
  --help          Show this help message

Examples:
  ./view_run_history.sh                # Show last 10 runs
  ./view_run_history.sh --last 20      # Show last 20 runs
  ./view_run_history.sh --top          # Show 5 fastest runs
  ./view_run_history.sh --compare      # Compare configurations
  ./view_run_history.sh --stats        # Show overall statistics
  ./view_run_history.sh --csv > data.csv  # Export to CSV file

Run history is stored in: run_history.csv
EOF
        ;;

    *)
        echo "Unknown option: $MODE"
        echo "Use --help for usage information"
        exit 1
        ;;
esac

echo ""

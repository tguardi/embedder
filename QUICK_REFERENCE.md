# Quick Reference Card

## 1. Generate Test Data

**Option A: Synthetic data (fast)**
```bash
./generate_1k_batch.sh batch_1k
```
Creates 1000 test documents in ~5 seconds.

**Option B: Real Fed speeches (realistic)**
```bash
./setup_scraper.sh  # First time only
python3 scrape_fed_speeches.py --max-speeches 1000 --output-dir batch_fed_speeches
```
Scrapes 1000 Federal Reserve speeches (~20-30 minutes).

## 2. Run Benchmark
```bash
# Basic syntax
./parallel_batch.sh INPUT_DIR API_URL INSTANCES WORKERS [options]

# Example: Conservative
./parallel_batch.sh batch_1k "YOUR_API" 5 5 \
  --api-batch-size 8 --chunker paragraph --no-verify-ssl

# Example: Moderate
./parallel_batch.sh batch_1k "YOUR_API" 10 5 \
  --api-batch-size 16 --chunker paragraph --no-verify-ssl

# Example: Aggressive
./parallel_batch.sh batch_1k "YOUR_API" 10 10 \
  --api-batch-size 32 --chunker paragraph --no-verify-ssl
```

**Key Options:**
- `INSTANCES × WORKERS = total parallelism`
- `--api-batch-size`: Texts per API call (1, 8, 16, 32, 64)
- `--chunker paragraph`: For large models (BGE-M3, etc.)
- `--chunk-size 6000`: Tokens per chunk (for paragraph mode)
- `--no-verify-ssl`: Skip SSL verification

## 3. View Results

**After each run, you get:**
```
AGGREGATED METRICS:
Configuration: 10 instances × 5 workers = 50 total workers

Documents processed:    1000
Total chunks:           2543
Wall-clock time:        45.3s

Throughput:
  Documents/sec:        22.1
  Chunks/sec:           56.1

API Performance:
  Total API calls:      318
  Total API time:       320.5s
  Avg API latency:      1008ms
```

## 4. Compare Across Runs

```bash
# View last 10 runs
./view_run_history.sh

# View top 5 fastest
./view_run_history.sh --top

# Compare configs
./view_run_history.sh --compare

# Show stats
./view_run_history.sh --stats
```

## 5. Monitor Progress

```bash
# Watch all instances
tail -f logs/instance_*.log

# Watch one instance
tail -f logs/instance_0.log

# Check Solr count
curl "http://localhost:8983/solr/documents/select?q=*:*&rows=0" | jq .response.numFound
```

## 6. Key Metrics to Track

| Metric | What it tells you |
|--------|-------------------|
| **Documents/sec** | Overall throughput |
| **Chunks/sec** | Processing rate |
| **Avg API latency** | API bottleneck indicator |
| **Wall-clock time** | Total end-to-end time |

**Watch API latency:** If it increases 2-3x, you've hit API capacity.

## 7. Finding Optimal Config

**Progressive Testing:**
```bash
# 1. Start small
./parallel_batch.sh batch_1k API 5 5 --api-batch-size 8

# 2. Increase batch size
./parallel_batch.sh batch_1k API 5 5 --api-batch-size 16

# 3. Increase workers
./parallel_batch.sh batch_1k API 5 10 --api-batch-size 16

# 4. Add instances
./parallel_batch.sh batch_1k API 10 10 --api-batch-size 16

# 5. Push harder
./parallel_batch.sh batch_1k API 10 10 --api-batch-size 32
```

Stop when you see timeouts or no improvement in throughput.

## 8. Common Configurations

| Use Case | Config | Parallelism |
|----------|--------|-------------|
| Testing | 5×5×B8 | 200 chunks in flight |
| Production | 10×5×B16 | 800 chunks in flight |
| High-Speed | 10×10×B32 | 3,200 chunks in flight |
| Maximum | 15×10×B64 | 9,600 chunks in flight |

**Format:** `instances×workers×BatchSize`

## 9. Troubleshooting

| Problem | Solution |
|---------|----------|
| Too slow | Increase workers or batch size |
| Timeouts | Decrease batch size |
| API errors | Reduce parallelism |
| OOM | Reduce batch size significantly |
| Uneven load | More docs than instances |

## 10. Files Generated

- `logs/instance_*.log` - Individual instance logs
- `run_history.csv` - All benchmark results (CSV)
- Individual collections in Solr:
  - `documents` - Parent metadata
  - `vectors` - Chunks with embeddings

## Example Workflow

```bash
# Generate test data
./generate_1k_batch.sh test_batch

# Run 3 progressive benchmarks
./parallel_batch.sh test_batch API 5 5 --api-batch-size 8 --chunker paragraph
./parallel_batch.sh test_batch API 10 5 --api-batch-size 16 --chunker paragraph
./parallel_batch.sh test_batch API 10 10 --api-batch-size 32 --chunker paragraph

# Compare results
./view_run_history.sh --top

# Pick winner, run on full dataset
./parallel_batch.sh production_data API 10 10 --api-batch-size 32 --chunker paragraph
```

---

**Full Documentation:**
- [README.md](README.md) - Complete setup and usage
- [BENCHMARK_GUIDE.md](BENCHMARK_GUIDE.md) - Detailed benchmarking guide
- [DOCUMENT_SUMMARY.md](DOCUMENT_SUMMARY.md) - Document generation details

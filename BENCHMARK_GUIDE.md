# Embedding Pipeline Benchmark Guide

Quick reference for running performance benchmarks and comparing results.

## Generate Test Data

```bash
# Generate 1000 test documents (~5-10 seconds)
./generate_1k_batch.sh batch_1k

# Or use custom output directory
./generate_1k_batch.sh my_test_batch
```

**Generated documents:**
- 500 supervisory letters (~2-3KB each)
- 350 CAMELS summaries (~1-2KB each)
- 150 LFBO letters (~1-2KB each)
- Total: ~1.5-2MB of text content

## Run Benchmarks

### Basic Syntax
```bash
./parallel_batch.sh <input_dir> <api_url> <instances> <workers> [options]
```

### Example Configurations

#### Conservative (Good Starting Point)
```bash
time ./parallel_batch.sh batch_1k "YOUR_API_URL" 5 5 \
  --vector-field bge_m3_vector \
  --vector-dims 1024 \
  --chunker paragraph \
  --chunk-size 6000 \
  --overlap 100 \
  --api-batch-size 8 \
  --no-verify-ssl
```
- **Parallelism:** 5 instances × 5 workers × 8 batch = 200 chunks in flight
- **Best for:** Initial testing, limited API resources

#### Moderate (Balanced)
```bash
time ./parallel_batch.sh batch_1k "YOUR_API_URL" 10 5 \
  --vector-field bge_m3_vector \
  --vector-dims 1024 \
  --chunker paragraph \
  --chunk-size 6000 \
  --overlap 100 \
  --api-batch-size 16 \
  --no-verify-ssl
```
- **Parallelism:** 10 instances × 5 workers × 16 batch = 800 chunks in flight
- **Best for:** Production workloads with good API capacity

#### Aggressive (Maximum Throughput)
```bash
time ./parallel_batch.sh batch_1k "YOUR_API_URL" 10 10 \
  --vector-field bge_m3_vector \
  --vector-dims 1024 \
  --chunker paragraph \
  --chunk-size 6000 \
  --overlap 100 \
  --api-batch-size 32 \
  --no-verify-ssl
```
- **Parallelism:** 10 instances × 10 workers × 32 batch = 3,200 chunks in flight
- **Best for:** High-capacity APIs, maximum speed

## Key Metrics to Compare

After each run, the script will display:

```
AGGREGATED METRICS:
------------------------------------------------------------------------
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

### What to Track

For each configuration, record:

1. **Documents/sec** - Overall document processing rate
2. **Chunks/sec** - Chunk processing throughput
3. **Avg API latency** - How fast your API responds
4. **Wall-clock time** - Total time to complete

### Example Comparison Table

| Config | Instances | Workers | Batch Size | Docs/sec | Chunks/sec | API Latency | Total Time |
|--------|-----------|---------|------------|----------|------------|-------------|------------|
| Small  | 5         | 5       | 8          | 18.5     | 47.2       | 850ms       | 54.1s      |
| Medium | 10        | 5       | 16         | 22.1     | 56.1       | 1008ms      | 45.3s      |
| Large  | 10        | 10      | 32         | 35.7     | 90.8       | 1250ms      | 28.0s      |

## Finding Your Optimal Configuration

### Methodology

1. **Start conservative:** 5 instances × 5 workers × batch 8
2. **Increase batch size:** Try 16, then 32, then 64
3. **Monitor API latency:** If it increases significantly, you've hit API capacity
4. **Add more workers:** If latency is stable, add more parallelism
5. **Find the sweet spot:** Maximum throughput without API timeouts/errors

### Signs You're Pushing Too Hard

- ❌ API latency increases dramatically (>2-3x baseline)
- ❌ Timeout errors in logs
- ❌ API returning 500/503 errors
- ❌ Diminishing returns (no speed improvement with more workers)

### Signs You Can Push More

- ✅ API latency remains stable
- ✅ No errors in logs
- ✅ Linear speedup with added workers
- ✅ CPU/network not saturated

## Quick Benchmark Script

Save this as `quick_benchmark.sh`:

```bash
#!/bin/bash
# Run progressive benchmarks and compare results

API_URL="YOUR_API_URL"
INPUT_DIR="batch_1k"

echo "Running Progressive Benchmarks..."
echo "=================================="
echo ""

echo "Test 1: Conservative (5×5×8)"
time ./parallel_batch.sh "$INPUT_DIR" "$API_URL" 5 5 \
  --api-batch-size 8 --chunker paragraph --no-verify-ssl \
  2>&1 | grep -E "(Documents/sec|Chunks/sec|Avg API latency|Wall-clock)"

echo ""
echo "Test 2: Moderate (10×5×16)"
time ./parallel_batch.sh "$INPUT_DIR" "$API_URL" 10 5 \
  --api-batch-size 16 --chunker paragraph --no-verify-ssl \
  2>&1 | grep -E "(Documents/sec|Chunks/sec|Avg API latency|Wall-clock)"

echo ""
echo "Test 3: Aggressive (10×10×32)"
time ./parallel_batch.sh "$INPUT_DIR" "$API_URL" 10 10 \
  --api-batch-size 32 --chunker paragraph --no-verify-ssl \
  2>&1 | grep -E "(Documents/sec|Chunks/sec|Avg API latency|Wall-clock)"
```

## Monitoring During Runs

### Watch all logs in real-time
```bash
tail -f logs/instance_*.log
```

### Watch specific instance
```bash
tail -f logs/instance_0.log
```

### Check progress
```bash
# Count processed documents
grep "✓" logs/instance_*.log | wc -l

# Check for errors
grep -i error logs/instance_*.log
```

### Monitor Solr
```bash
# Check document count
curl "http://localhost:8983/solr/documents/select?q=*:*&rows=0" | jq .response.numFound

# Check vector count
curl "http://localhost:8983/solr/vectors/select?q=*:*&rows=0" | jq .response.numFound
```

## Troubleshooting

### Runs too slow
- Increase workers: `--workers 10` → `--workers 20`
- Increase batch size: `--api-batch-size 8` → `--api-batch-size 32`
- Add more instances: `./parallel_batch.sh ... 10 10` → `15 10`

### API timeouts
- Decrease batch size: `--api-batch-size 64` → `--api-batch-size 16`
- Reduce workers: `--workers 20` → `--workers 10`
- Reduce instances: `15 instances` → `10 instances`

### Out of memory (API side)
- Reduce batch size significantly: `--api-batch-size 8`
- Ensure API has enough VRAM for model + batch processing

### Uneven load distribution
- Make sure number of documents is much larger than number of instances
- 1000 docs ÷ 10 instances = 100 docs each (good)
- 50 docs ÷ 10 instances = 5 docs each (too few, some instances idle)

# Embedding Pipeline

Python pipeline to migrate documents from Solr 7 to Solr 9 with vector embeddings.

## Architecture

- **Solr 7** → Read documents with body text
- **Chunking** → Fixed-size chunks with overlap
- **Embedding** → Three backends: local (MPS/GPU/CPU), DJL GPU, or DJL CPU
- **Solr 9** → Write to parent (metadata) + chunk (vectors) collections

See [DECISIONS.md](DECISIONS.md) for detailed architecture decisions.
See [AUTOSCALING.md](AUTOSCALING.md) for horizontal scaling with CPU instances.

---

## Quick Start

### 1. Install Dependencies

```bash
# If using uv (recommended)
uv pip install -r requirements.txt

# Or with pip
pip install -r requirements.txt
```

### 2. Configure

Edit `config.env` with your Solr connection details:

```bash
# Solr 7 (source)
SOLR7_URL=http://localhost:8983/solr
SOLR7_COLLECTION=your_collection

# Solr 9 (destination)
SOLR9_URL=http://localhost:8984/solr
SOLR9_PARENT_COLLECTION=parent_collection
SOLR9_CHUNK_COLLECTION=chunk_collection

# Chunking
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### 3. Run Pipeline

#### Option A: Local Mode (Development - Mac/Apple Silicon)

Best for: Development, testing, Apple Silicon Macs

```bash
python embed_pipeline.py --local
```

**Performance:** ~1,340 chunks/sec on M4 Max (MPS)

---

#### Option B: DJL GPU Mode (Production - NVIDIA GPU)

Best for: Production, sustained high-throughput workloads

```bash
# Start DJL GPU container
docker-compose up -d djl

# Wait for model load (~60s)
docker-compose logs -f djl

# Run pipeline
python embed_pipeline.py
```

**Performance:** ~3,000-5,000 chunks/sec
**Requirements:** NVIDIA GPU, Linux x86_64

---

#### Option C: DJL CPU Mode (Autoscaling - No GPU)

Best for: Bursty workloads, horizontal autoscaling, serverless

```bash
# Start DJL CPU container
docker-compose -f docker-compose.cpu.yml up -d djl-cpu

# Wait for model load (~60s)
docker-compose -f docker-compose.cpu.yml logs -f djl-cpu

# Run pipeline
python embed_pipeline.py
```

**Performance:** ~500-700 chunks/sec per instance
**Scaling:** Horizontal (5 instances ≈ 1 GPU in throughput)
**See:** [AUTOSCALING.md](AUTOSCALING.md) for K8s/ECS deployment

---

## Deployment Comparison

| Mode | Throughput/Instance | Cost/Hour | Scaling | Best For |
|------|---------------------|-----------|---------|----------|
| **Local (MPS)** | 1,340 chunks/sec | Free | N/A | Development on Mac |
| **DJL GPU** | 3,000-5,000 chunks/sec | $1-3 | Vertical | 24/7 production |
| **DJL CPU** | 500-700 chunks/sec | $0.10-0.20 | Horizontal | Bursty workloads |
| **DJL CPU × 5** | 2,500-3,500 chunks/sec | $0.50-1 | Auto | On-demand scaling |

---

## Testing

### Test Embedding Only (No Solr)

```bash
# Test local sentence-transformers (Mac)
python test_local.py --local

# Test DJL GPU container
docker-compose up -d djl
python test_local.py

# Test DJL CPU container
docker-compose -f docker-compose.cpu.yml up -d djl-cpu
python test_local.py
```

**Output:** Throughput benchmarks, vector validation

---

### Test Solr Indexing Throughput

```bash
# Start Solr 9
docker-compose up -d solr9

# Setup test collections
python test_solr_throughput.py --setup

# Run throughput test
python test_solr_throughput.py --num-docs 100 --num-chunks 1000

# Cleanup
python test_solr_throughput.py --cleanup
```

**What it measures:**
- Parent document indexing rate
- Chunk indexing rate (with 384-dim vectors)
- End-to-end throughput
- Commit overhead

**Expected results:**
- Parent docs: ~5,000-10,000 docs/sec
- Chunks with vectors: ~1,000-3,000 chunks/sec
- **Finding:** Vector indexing is comparable to embedding speed

---

## Performance Benchmarks

### Embedding Throughput

| Backend | Device | Chunks/Sec | Notes |
|---------|--------|------------|-------|
| Local | M4 Max MPS | 1,340 | Best for Mac dev |
| Local | CPU | ~700 | Fallback |
| DJL GPU | NVIDIA T4 | 3,000-5,000 | Production |
| DJL CPU | 4 vCPU | 500-700 | Autoscale |

### Solr Indexing Throughput

From `test_solr_throughput.py` (single-node Solr):
- Parent metadata: ~5,000-10,000 docs/sec
- Chunks with vectors: ~1,000-3,000 chunks/sec
- **Bottleneck:** Vector field indexing and commit time

### End-to-End Estimate

For 100K documents with ~7 chunks/doc (700K chunks):

| Mode | Embedding | Solr Indexing | Total |
|------|-----------|---------------|-------|
| Local (MPS) | 8.7 min | 5.8 min | **~15 min** |
| DJL GPU | 3-4 min | 5.8 min | **~9 min** |
| DJL CPU × 5 | 4-5 min | 5.8 min | **~10 min** |

---

## Command Reference

### Pipeline

```bash
# Dry run (no Solr writes)
python embed_pipeline.py --local --dry-run

# Production run with GPU
docker-compose up -d djl
python embed_pipeline.py

# Production run with CPU autoscaling
docker-compose -f docker-compose.cpu.yml up -d djl-cpu
python embed_pipeline.py

# With custom query
SOLR7_QUERY="status:published" python embed_pipeline.py --local
```

### Testing

```bash
# Test embedding backends
python test_local.py --local          # Local sentence-transformers
python test_local.py                  # DJL container (GPU or CPU)

# Test Solr throughput
python test_solr_throughput.py --setup
python test_solr_throughput.py --num-chunks 10000
python test_solr_throughput.py --cleanup
```

### Docker

```bash
# GPU variant (default)
docker-compose up -d
docker-compose logs -f djl
docker-compose down

# CPU variant (autoscaling-friendly)
docker-compose -f docker-compose.cpu.yml up -d
docker-compose -f docker-compose.cpu.yml logs -f djl-cpu
docker-compose -f docker-compose.cpu.yml down

# Start just Solr 9 for testing
docker-compose up -d solr9

# Remove volumes
docker-compose down -v
```

---

## Files

| File | Purpose |
|------|---------|
| `embed_pipeline.py` | Main pipeline script |
| `test_local.py` | Test embedding backends |
| `test_solr_throughput.py` | Measure Solr indexing performance |
| `config.env` | Configuration |
| `docker-compose.yml` | DJL GPU + Solr 9 services |
| `docker-compose.cpu.yml` | DJL CPU variant for autoscaling |
| `DECISIONS.md` | Architecture documentation |
| `AUTOSCALING.md` | Horizontal scaling guide (K8s, ECS, etc.) |
| `README.md` | This file |
| `combined.md` | Single-file export (generated) |

---

## Deployment Scenarios

### Scenario 1: One-Time Migration (Small Dataset)

**Setup:** Local mode on developer laptop
**Cost:** Free
**Time:** ~15 min for 100K docs

```bash
python embed_pipeline.py --local
```

---

### Scenario 2: Production Batch (Large Dataset, 24/7)

**Setup:** Single GPU instance (AWS p3.2xlarge, GCP T4)
**Cost:** $1-3/hour
**Time:** ~9 min for 100K docs

```bash
docker-compose up -d djl
python embed_pipeline.py
```

---

### Scenario 3: On-Demand / Bursty Workload

**Setup:** Kubernetes with HPA (2-10 CPU pods)
**Cost:** $0.50-2/hour (pay for what you use)
**Time:** ~10 min for 100K docs (5 instances)

```bash
kubectl apply -f k8s/deployment.yaml
python embed_pipeline.py  # Points to K8s service
```

See [AUTOSCALING.md](AUTOSCALING.md) for full setup.

---

### Scenario 4: Serverless (AWS Fargate / Cloud Run)

**Setup:** Serverless container, scale-to-zero
**Cost:** Pay-per-request
**Time:** Variable (cold starts)

See [AUTOSCALING.md](AUTOSCALING.md) for ECS/Cloud Run configs.

---

## Troubleshooting

**DJL GPU container fails on Mac:**
- The `pytorch-gpu` image requires x86_64 + NVIDIA GPU
- Use `--local` mode or `docker-compose.cpu.yml` for development on Apple Silicon

**Solr indexing is slow:**
- Check commit frequency (pipeline commits once at end)
- Increase `BATCH_SIZE` for fewer HTTP requests
- Consider Solr cluster with multiple shards

**Out of memory:**
- Reduce `BATCH_SIZE`
- Reduce `FETCH_ROWS` for Solr cursor pagination
- Increase `SOLR_HEAP` in docker-compose.yml

**DJL CPU is too slow:**
- Scale horizontally: 5 CPU instances ≈ 1 GPU
- See [AUTOSCALING.md](AUTOSCALING.md) for K8s HPA setup

**Need faster throughput:**
- Use GPU for sustained workloads
- Parallelize pipeline (multiple Python processes)
- Use multi-shard Solr cluster

---

## Production Checklist

- [ ] Update `config.env` with production Solr URLs
- [ ] Set appropriate `CHUNK_SIZE` and `CHUNK_OVERLAP`
- [ ] Define `chunk_metadata` fields (line 290 in embed_pipeline.py)
- [ ] Test with small dataset first (`--dry-run`)
- [ ] Choose deployment mode (local, GPU, CPU autoscale)
- [ ] Monitor Solr heap and disk space
- [ ] Set up autoscaling if using CPU variant
- [ ] Add monitoring/alerting for long-running jobs

---

## Next Steps

1. **Test locally:** `python test_local.py --local`
2. **Test Solr:** `python test_solr_throughput.py --setup && python test_solr_throughput.py`
3. **Dry run:** `python embed_pipeline.py --local --dry-run`
4. **Production:** Choose GPU or CPU mode based on [Deployment Scenarios](#deployment-scenarios)
5. **Scale:** See [AUTOSCALING.md](AUTOSCALING.md) for horizontal scaling

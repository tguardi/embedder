# Archive - Advanced Tools

This directory contains the full-featured embedding pipeline with advanced capabilities.

---

## What's Here

### Full Solr 7 → Solr 9 Migration
- `embed_pipeline.py` - Complete migration pipeline
- Cursor-based pagination from Solr 7
- Dual-collection writes to Solr 9
- Multiple embedding backends (local, DJL GPU, DJL CPU)

### Local Model Support
- `download_model.py` - Download models for offline use
- `LOCAL_MODELS.md` - Air-gapped deployment guide
- Support for loading models from filesystem

### Autoscaling
- `AUTOSCALING.md` - Kubernetes, ECS, Cloud Run guides
- `docker-compose.cpu.yml` - CPU-based horizontal scaling
- `docker-compose.local-model.yml` - Offline model serving

### Testing Tools
- `test_local.py` - Test embedding backends
- `test_solr_throughput.py` - Benchmark Solr performance
- `test_simple.sh` - End-to-end testing

### Alternative Simple Tools
- `simple_embedder.py` - Single file to JSON
- `simple_to_solr.py` - Single file to Solr (flat structure)

---

## When to Use These Tools

**Use the simple tool (parent directory)** when:
- You have text files and a custom API
- You want minimal dependencies
- You need comprehensive analytics

**Use these advanced tools** when:
- Migrating from Solr 7 to Solr 9
- Need local sentence-transformers models
- Want DJL container serving
- Need autoscaling infrastructure
- Running in air-gapped environments

---

## Key Files

| File | Purpose |
|------|---------|
| `embed_pipeline.py` | Full Solr 7→9 migration pipeline |
| `AUTOSCALING.md` | K8s/ECS deployment guides |
| `LOCAL_MODELS.md` | Offline/air-gapped setup |
| `SETUP.md` | Full setup on new machines |
| `requirements.txt` | Full dependencies (torch, sentence-transformers) |
| `docker-compose.yml` | DJL GPU serving |
| `docker-compose.cpu.yml` | DJL CPU autoscaling |

---

## Quick Examples

### Solr 7 → Solr 9 Migration
```bash
# Install full dependencies
pip install -r requirements.txt

# Run with local embeddings
python embed_pipeline.py --local

# Or with DJL container
docker-compose up -d djl
python embed_pipeline.py
```

### Download Model for Offline Use
```bash
python download_model.py all-MiniLM-L6-v2 ./model
```

### Test Solr Throughput
```bash
docker-compose up -d solr9
python test_solr_throughput.py --setup
python test_solr_throughput.py --num-chunks 10000
```

---

See individual markdown files for detailed documentation.

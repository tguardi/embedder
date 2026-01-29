# Setup on New Machine

Quick setup guide for running the embedding pipeline on a fresh machine.

---

## Prerequisites

**Required:**
- Python 3.9+
- Git (to clone/transfer the code)

**Optional (depends on mode):**
- Docker (for DJL container modes)
- NVIDIA GPU + drivers (for GPU mode)

---

## Step 1: Transfer Files

### Option A: Git Clone (if in a repo)
```bash
git clone <your-repo-url>
cd embed-pipeline
```

### Option B: Direct Transfer
```bash
# From this machine, create a tarball
cd /Users/guardi/Projects/rust_embeddings
tar -czf embed-pipeline.tar.gz embed-pipeline/

# Copy to target machine (scp, rsync, USB, etc.)
scp embed-pipeline.tar.gz user@remote:/path/to/destination/

# On target machine
tar -xzf embed-pipeline.tar.gz
cd embed-pipeline
```

### Option C: Use combined.md
If you just need the code without git history:
```bash
# The combined.md file contains all source code
# Extract each section manually or use the files directly
```

---

## Step 2: Install Python Dependencies

### Option A: Using uv (recommended, fastest)
```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Option B: Using pip + venv
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Configure

Edit `config.env` with your environment details:

```bash
# Solr 7 (source) - UPDATE THESE
SOLR7_URL=http://your-solr7-host:8983/solr
SOLR7_COLLECTION=your_collection_name
SOLR7_QUERY=*:*

# Solr 9 (destination) - UPDATE THESE
SOLR9_URL=http://your-solr9-host:8983/solr
SOLR9_PARENT_COLLECTION=parent_docs
SOLR9_CHUNK_COLLECTION=vector_chunks

# DJL (if using container mode) - UPDATE IF NEEDED
DJL_URL=http://localhost:8080/predictions/all-MiniLM-L6-v2

# Chunking - ADJUST BASED ON YOUR CONTENT
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Processing - TUNE BASED ON YOUR HARDWARE
BATCH_SIZE=64
FETCH_ROWS=100
```

---

## Step 4: Choose Deployment Mode

### Mode 1: Local (No Docker, fastest setup)

**Requirements:** Just Python

```bash
# Activate environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Test
python test_local.py --local

# Run pipeline
python embed_pipeline.py --local
```

**Performance:** ~700-1,300 chunks/sec (depends on CPU/GPU)

---

### Mode 2: DJL GPU (Production)

**Requirements:** Docker, NVIDIA GPU, nvidia-docker

**Setup Docker (if not installed):**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install nvidia-docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

**Run:**
```bash
# Start DJL GPU container
docker-compose up -d djl

# Wait for model load (~60s)
docker-compose logs -f djl
# Look for: "Model all-MiniLM-L6-v2 loaded"

# Test
python test_local.py

# Run pipeline
python embed_pipeline.py
```

**Performance:** ~3,000-5,000 chunks/sec

---

### Mode 3: DJL CPU (Autoscaling)

**Requirements:** Docker only (no GPU needed)

**Setup Docker (if not installed):**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in for group changes
```

**Run:**
```bash
# Start DJL CPU container
docker-compose -f docker-compose.cpu.yml up -d djl-cpu

# Wait for model load (~60s)
docker-compose -f docker-compose.cpu.yml logs -f djl-cpu

# Test
python test_local.py

# Run pipeline
python embed_pipeline.py
```

**Performance:** ~500-700 chunks/sec per instance
**Scale:** See [AUTOSCALING.md](AUTOSCALING.md) for multi-instance setup

---

## Step 5: Verify Setup

### Test Embedding Backend
```bash
python test_local.py --local  # For local mode
# OR
python test_local.py          # For DJL mode
```

**Expected output:**
```
==================================================
Embed Pipeline - Local Tests
Mode: LOCAL (sentence-transformers)
==================================================
Testing connection...
  Ping: OK

...

==================================================
Results:
  Chunking: PASS
  Embeddings: PASS
  Full Pipeline: PASS
  Large Batch: PASS
```

### Test Solr Connection (Optional)
```bash
# Start local Solr for testing
docker-compose up -d solr9

# Setup test collections
python test_solr_throughput.py --setup

# Run throughput test
python test_solr_throughput.py --num-chunks 1000

# Cleanup
python test_solr_throughput.py --cleanup
```

---

## Step 6: Run Pipeline

### Dry Run (No Solr Writes)
```bash
python embed_pipeline.py --local --dry-run
```

This will:
- Read from Solr 7 (or error if not configured)
- Generate embeddings
- NOT write to Solr 9
- Show throughput metrics

### Production Run
```bash
# Activate environment
source .venv/bin/activate

# Run pipeline
python embed_pipeline.py --local  # Or without --local for DJL mode
```

**Monitor progress:**
- Progress bar shows document processing
- Logs show throughput at the end
- Check Solr 9 admin UI for indexed documents

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'dotenv'"
```bash
# Activate virtual environment first
source .venv/bin/activate
pip install -r requirements.txt
```

### "Cannot connect to Solr 7"
```bash
# Test connection
curl http://your-solr7-host:8983/solr/admin/info/system

# Check config.env has correct URL
cat config.env | grep SOLR7_URL
```

### "DJL container not available"
```bash
# Check if container is running
docker ps

# View logs
docker-compose logs djl

# Restart
docker-compose restart djl
```

### "NVIDIA GPU not found" (GPU mode)
```bash
# Check GPU
nvidia-smi

# Check nvidia-docker
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### "Out of memory"
```bash
# Edit config.env
BATCH_SIZE=32          # Reduce from 64
FETCH_ROWS=50          # Reduce from 100
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python test_local.py --local` | Test local embeddings |
| `python test_local.py` | Test DJL embeddings |
| `python embed_pipeline.py --local --dry-run` | Dry run with local embeddings |
| `python embed_pipeline.py` | Production run with DJL |
| `docker-compose up -d djl` | Start GPU container |
| `docker-compose -f docker-compose.cpu.yml up -d` | Start CPU container |
| `docker-compose logs -f djl` | View container logs |

---

## Files You Need on Target Machine

**Minimum (for local mode):**
```
embed-pipeline/
├── config.env
├── embed_pipeline.py
├── requirements.txt
└── .env (optional, same as config.env)
```

**Full (for all modes):**
```
embed-pipeline/
├── config.env
├── embed_pipeline.py
├── test_local.py
├── test_solr_throughput.py
├── requirements.txt
├── docker-compose.yml
├── docker-compose.cpu.yml
├── README.md
├── DECISIONS.md
├── AUTOSCALING.md
└── SETUP.md (this file)
```

---

## Next Steps

1. **Choose your mode** (local, GPU, or CPU)
2. **Follow Step 1-5** above
3. **Test with dry run** (`--dry-run`)
4. **Run production** pipeline
5. **Monitor** Solr 9 for results
6. **Scale** if needed (see [AUTOSCALING.md](AUTOSCALING.md))

**Need help?** Check [README.md](README.md) for detailed documentation.

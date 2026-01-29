# Using Local Models (Air-Gapped / Offline Environments)

Guide for running the embedding pipeline without internet access to HuggingFace or external APIs.

---

## Overview

In restricted environments (air-gapped, corporate networks, etc.), you need to:
1. Download the model on a machine with internet access
2. Transfer the model files to the target environment
3. Configure the pipeline to use the local model

---

## Option 1: Local Mode (sentence-transformers)

### Step 1: Download Model (On Internet-Connected Machine)

```python
from sentence_transformers import SentenceTransformer

# Download model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Save to directory
model.save('./model')

# This creates:
# model/
# ├── config.json
# ├── pytorch_model.bin
# ├── tokenizer_config.json
# ├── vocab.txt
# └── ...
```

Or use the download script:

```python
#!/usr/bin/env python3
"""Download sentence-transformers model for offline use."""
from sentence_transformers import SentenceTransformer
import sys

model_name = sys.argv[1] if len(sys.argv) > 1 else "all-MiniLM-L6-v2"
output_dir = sys.argv[2] if len(sys.argv) > 2 else "./model"

print(f"Downloading {model_name}...")
model = SentenceTransformer(model_name)
model.save(output_dir)
print(f"Saved to {output_dir}")
```

### Step 2: Transfer Model Files

```bash
# Create tarball
tar -czf model.tar.gz model/

# Transfer to target machine (scp, USB, etc.)
scp model.tar.gz user@target:/path/to/embedder/

# On target machine
cd /path/to/embedder
tar -xzf model.tar.gz
```

### Step 3: Configure to Use Local Model

Edit `config.env`:

```bash
# Use local path instead of HuggingFace model name
MODEL_NAME=./model

# Or absolute path
# MODEL_NAME=/opt/models/all-MiniLM-L6-v2
```

### Step 4: Run Pipeline

```bash
# Local mode automatically uses the path from MODEL_NAME
python embed_pipeline.py --local
```

**No internet required!** The model loads from the local directory.

---

## Option 2: DJL Container with Local Model

### Step 1: Prepare Model Directory

Your model directory should contain the model files in a format DJL understands (PyTorch, ONNX, etc.).

For sentence-transformers models:
```
model/
├── config.json
├── pytorch_model.bin
├── tokenizer_config.json
├── vocab.txt
└── sentence_bert_config.json (optional)
```

### Step 2: Use Local Model Docker Compose

Use `docker-compose.local-model.yml`:

```bash
# Ensure your model is in ./model directory
ls model/

# Start DJL with local model
docker-compose -f docker-compose.local-model.yml up -d djl-local
```

This mounts `./model` to `/opt/ml/model` inside the container and configures DJL to load from there.

### Step 3: Update DJL_URL in config.env

```bash
# Update to match the model endpoint
# For local models, use the model directory name
DJL_URL=http://localhost:8080/predictions/model
```

### Step 4: Run Pipeline

```bash
python embed_pipeline.py
```

---

## Model Directory Structure

### Sentence-Transformers Format (Recommended)

```
model/
├── config.json                    # Model config
├── pytorch_model.bin              # Model weights
├── sentence_bert_config.json      # Sentence-transformers config
├── tokenizer_config.json          # Tokenizer config
├── special_tokens_map.json
├── vocab.txt
└── modules.json
```

### Minimal Format (Also Works)

```
model/
├── config.json
├── pytorch_model.bin
└── vocab.txt
```

---

## Verifying Your Model

### Test Local Model (sentence-transformers)

```python
from sentence_transformers import SentenceTransformer

# Load from local path
model = SentenceTransformer('./model')

# Test encoding
embeddings = model.encode(["Hello world", "Test sentence"])
print(f"Generated {len(embeddings)} embeddings")
print(f"Vector dimension: {len(embeddings[0])}")
```

### Test with Pipeline

```bash
# Set model path
export MODEL_NAME=./model

# Run test
python test_local.py --local
```

Expected output:
```
==================================================
Embed Pipeline - Local Tests
Mode: LOCAL (sentence-transformers)
==================================================
  Loading model ./model on device: cpu
Testing connection...
  Ping: OK
...
Results:
  Chunking: PASS
  Embeddings: PASS
  Full Pipeline: PASS
```

---

## Common Model Sources

### 1. Download from HuggingFace (Requires Internet)

```python
from sentence_transformers import SentenceTransformer

# Popular models
models = [
    "all-MiniLM-L6-v2",           # 384-dim, fast, good quality
    "all-mpnet-base-v2",          # 768-dim, best quality, slower
    "paraphrase-MiniLM-L6-v2",    # 384-dim, optimized for paraphrasing
]

for model_name in models:
    model = SentenceTransformer(model_name)
    model.save(f"./models/{model_name}")
```

### 2. Download from HuggingFace Hub CLI

```bash
# Install huggingface_hub
pip install huggingface_hub

# Download model
huggingface-cli download sentence-transformers/all-MiniLM-L6-v2 \
  --local-dir ./model \
  --local-dir-use-symlinks False
```

### 3. Use Pre-Downloaded Models

If someone already has the model:
```bash
# Copy from their directory
cp -r /path/to/their/model ./model
```

---

## Troubleshooting

### "Model not found at ./model"

```bash
# Check directory exists
ls -la model/

# Verify it contains model files
ls model/
# Should show: config.json, pytorch_model.bin, etc.
```

### "Invalid model format"

Ensure the directory contains at minimum:
- `config.json`
- `pytorch_model.bin` (or `model.safetensors`)
- Tokenizer files (`vocab.txt` or `tokenizer.json`)

### "Can't load sentence-transformers model"

The model must be a sentence-transformers compatible model. Not all HuggingFace models work directly.

Download using sentence-transformers library:
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('./model')
```

### "DJL can't load local model"

Check that:
1. Model directory is mounted: `docker exec djl-local ls /opt/ml/model`
2. DJL sees the files: `docker logs djl-local | grep model`
3. Path in `SERVING_LOAD_MODELS` is correct: `file:///opt/ml/model`

---

## Configuration Reference

### config.env for Local Models

```bash
# Local mode
MODEL_NAME=./model                    # Relative path
# or
MODEL_NAME=/opt/models/embeddings     # Absolute path

# DJL mode (when using docker-compose.local-model.yml)
DJL_URL=http://localhost:8080/predictions/model
```

### docker-compose.local-model.yml

```yaml
services:
  djl-local:
    volumes:
      - ./model:/opt/ml/model:ro     # Mount local model dir
    environment:
      - SERVING_LOAD_MODELS=file:///opt/ml/model
```

---

## Best Practices

1. **Validate before transfer** - Test the model on the internet-connected machine first
2. **Include all files** - Don't cherry-pick, transfer the entire model directory
3. **Check file permissions** - Ensure the model files are readable
4. **Document model version** - Keep a README with model name, version, download date
5. **Test after transfer** - Run `test_local.py --local` to verify

---

## Example: Complete Offline Setup

### On Internet Machine

```bash
# Download model
python3 << 'EOF'
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('./model')
EOF

# Package everything
tar -czf embedder-offline.tar.gz \
  embed-pipeline/ \
  model/

# Transfer embedder-offline.tar.gz to target machine
```

### On Air-Gapped Machine

```bash
# Extract
tar -xzf embedder-offline.tar.gz
cd embed-pipeline

# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies (if pip packages available offline)
pip install -r requirements.txt

# Configure
cat > config.env << 'EOF'
SOLR7_URL=http://solr7:8983/solr
SOLR7_COLLECTION=documents
SOLR9_URL=http://solr9:8983/solr
SOLR9_PARENT_COLLECTION=parent_docs
SOLR9_CHUNK_COLLECTION=vector_chunks
MODEL_NAME=../model
CHUNK_SIZE=512
CHUNK_OVERLAP=50
BATCH_SIZE=64
FETCH_ROWS=100
EOF

# Test
python test_local.py --local

# Run
python embed_pipeline.py --local
```

---

## Summary

| Scenario | Model Location | Command |
|----------|---------------|---------|
| **Internet available** | HuggingFace | `MODEL_NAME=all-MiniLM-L6-v2` |
| **Offline (local mode)** | `./model` | `MODEL_NAME=./model` + `--local` |
| **Offline (DJL)** | `./model` mounted to container | `docker-compose -f docker-compose.local-model.yml up -d` |

For most air-gapped scenarios, **local mode with a local model directory** is the simplest approach.

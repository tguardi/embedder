#!/usr/bin/env python3
"""
Download sentence-transformers model for offline use.

Usage:
  python download_model.py                                    # Downloads all-MiniLM-L6-v2 to ./model
  python download_model.py all-mpnet-base-v2                 # Downloads specific model to ./model
  python download_model.py all-MiniLM-L6-v2 /path/to/output  # Downloads to specific directory
"""

import sys
import os

def download_model(model_name: str, output_dir: str):
    """Download and save a sentence-transformers model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("ERROR: sentence-transformers not installed")
        print("Install with: pip install sentence-transformers")
        sys.exit(1)

    print(f"Downloading model: {model_name}")
    print(f"This may take a few minutes...")

    try:
        model = SentenceTransformer(model_name)
        model.save(output_dir)

        print(f"\n✓ Model downloaded successfully!")
        print(f"  Location: {os.path.abspath(output_dir)}")
        print(f"\nModel info:")
        print(f"  Name: {model_name}")
        print(f"  Vector dimension: {model.get_sentence_embedding_dimension()}")

        # List files
        files = os.listdir(output_dir)
        print(f"  Files ({len(files)}):")
        for f in sorted(files):
            file_path = os.path.join(output_dir, f)
            size = os.path.getsize(file_path)
            print(f"    - {f} ({size:,} bytes)")

        print(f"\nNext steps:")
        print(f"  1. Update config.env: MODEL_NAME={output_dir}")
        print(f"  2. Test: python test_local.py --local")
        print(f"  3. Run: python embed_pipeline.py --local")

    except Exception as e:
        print(f"\nERROR: Failed to download model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    model_name = sys.argv[1] if len(sys.argv) > 1 else "all-MiniLM-L6-v2"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./model"

    print("=" * 60)
    print("Sentence-Transformers Model Downloader")
    print("=" * 60)

    # Check if output directory already exists
    if os.path.exists(output_dir):
        files = os.listdir(output_dir)
        if files:
            print(f"\nWARNING: Directory '{output_dir}' already exists and contains files:")
            for f in files[:5]:
                print(f"  - {f}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")

            response = input("\nOverwrite? (y/N): ").strip().lower()
            if response != 'y':
                print("Aborted.")
                sys.exit(0)

    download_model(model_name, output_dir)

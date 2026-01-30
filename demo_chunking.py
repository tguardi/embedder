#!/usr/bin/env python3
"""
Demonstrate the difference between fixed and paragraph chunking.
"""

def chunk_text_fixed(text: str, chunk_size: int, overlap: int):
    """Split text into fixed-size chunks with overlap."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def chunk_text_paragraph(text: str, max_tokens: int = 8000, overlap_tokens: int = 100):
    """Split text into paragraph-based chunks for large models."""
    if not text:
        return []

    # Token estimation: 1 token ≈ 4 chars
    chars_per_token = 4
    max_chars = max_tokens * chars_per_token
    overlap_chars = overlap_tokens * chars_per_token

    # Split into paragraphs
    paragraphs = text.split('\n\n')
    if len(paragraphs) == 1:
        paragraphs = text.split('\n')

    chunks = []
    current_chunk = []
    current_size = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        para_size = len(para)

        # If single paragraph exceeds max, split it
        if para_size > max_chars:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            sub_chunks = chunk_text_fixed(para, max_chars, overlap_chars)
            chunks.extend(sub_chunks)
            continue

        # Check if adding this paragraph would exceed limit
        if current_size + para_size + 2 > max_chars and current_chunk:
            chunks.append('\n\n'.join(current_chunk))

            # Start new chunk with overlap
            overlap_size = 0
            overlap_paras = []
            for p in reversed(current_chunk):
                if overlap_size + len(p) <= overlap_chars:
                    overlap_paras.insert(0, p)
                    overlap_size += len(p) + 2
                else:
                    break

            current_chunk = overlap_paras
            current_size = overlap_size

        current_chunk.append(para)
        current_size += para_size + 2

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


if __name__ == "__main__":
    # Read sample document
    with open('test_documents/doc1_supervisory_letter.txt', 'r') as f:
        text = f.read()

    print("=" * 80)
    print("CHUNKING STRATEGY COMPARISON")
    print("=" * 80)
    print(f"\nDocument size: {len(text):,} characters ({len(text) // 4:,} estimated tokens)")
    print()

    # Fixed chunking
    print("FIXED CHUNKING (512 chars, 50 overlap):")
    fixed_chunks = chunk_text_fixed(text, 512, 50)
    print(f"  Total chunks: {len(fixed_chunks)}")
    print(f"  Chunk sizes: {[len(c) for c in fixed_chunks[:10]]}")
    print(f"  Average chunk size: {sum(len(c) for c in fixed_chunks) // len(fixed_chunks)} chars")
    print(f"\n  First chunk preview:")
    print(f"  {fixed_chunks[0][:200]}...")
    print()

    # Paragraph chunking
    print("PARAGRAPH CHUNKING (6000 tokens = ~24,000 chars, 100 token overlap):")
    para_chunks = chunk_text_paragraph(text, 6000, 100)
    print(f"  Total chunks: {len(para_chunks)}")
    print(f"  Chunk sizes: {[len(c) for c in para_chunks]}")
    print(f"  Average chunk size: {sum(len(c) for c in para_chunks) // len(para_chunks)} chars")
    print(f"\n  First chunk preview:")
    first_chunk_paras = para_chunks[0].split('\n\n')
    print(f"  (Contains {len(first_chunk_paras)} paragraphs)")
    print(f"  {para_chunks[0][:300]}...")
    print()

    # Show semantic boundaries
    print("SEMANTIC BOUNDARY PRESERVATION:")
    print(f"  Fixed chunking: Cuts mid-sentence/mid-word")
    print(f"  - Chunk 1 ends: ...{fixed_chunks[0][-50:]}")
    print(f"  - Chunk 2 starts: {fixed_chunks[1][:50]}...")
    print()
    print(f"  Paragraph chunking: Respects paragraph boundaries")
    if len(para_chunks) > 1:
        print(f"  - Chunk 1 ends: ...{para_chunks[0][-100:]}")
        print(f"  - Chunk 2 starts: {para_chunks[1][:100]}...")
    print()

    print("=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    print("Use FIXED chunking for:")
    print("  - Small models (< 512 tokens)")
    print("  - Code or structured data")
    print("  - When you need consistent chunk sizes")
    print()
    print("Use PARAGRAPH chunking for:")
    print("  - Large models (BGE-M3 with 8k tokens)")
    print("  - Natural language documents")
    print("  - When semantic boundaries matter")
    print("  - Better context preservation")
    print("=" * 80)

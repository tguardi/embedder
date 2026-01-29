#!/usr/bin/env bash
# Combines all project files into a single markdown document
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
OUT="$DIR/combined.md"

cat > "$OUT" << 'HEADER'
# Embed Pipeline — Combined Source
HEADER

for file in config.env embed_pipeline.py requirements.txt; do
    ext="${file##*.}"
    printf '\n#######\n\n## %s\n\n```%s\n' "$file" "$ext" >> "$OUT"
    cat "$DIR/$file" >> "$OUT"
    printf '\n```\n' >> "$OUT"
done

echo "Written to $OUT"

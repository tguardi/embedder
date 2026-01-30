#!/bin/bash
# Create test documents for batch processing using realistic banking documents

mkdir -p test_documents

echo "Generating realistic banking examination documents..."
python3 standalone_text_generator.py

# Rename generated files to follow our naming convention
if [ -f "example_supervisory_letter.txt" ]; then
    mv example_supervisory_letter.txt test_documents/doc1_supervisory_letter.txt
    echo "✓ Created: doc1_supervisory_letter.txt"
fi

if [ -f "example_camels_summary.txt" ]; then
    mv example_camels_summary.txt test_documents/doc2_camels_summary.txt
    echo "✓ Created: doc2_camels_summary.txt"
fi

if [ -f "example_lfbo_letter.txt" ]; then
    mv example_lfbo_letter.txt test_documents/doc3_lfbo_letter.txt
    echo "✓ Created: doc3_lfbo_letter.txt"
fi

echo ""
echo "Created 3 realistic banking examination documents in test_documents/"
ls -lh test_documents/
echo ""
echo "Document sizes:"
wc -l test_documents/*.txt
echo ""
echo "Sample content from doc1_supervisory_letter.txt:"
head -10 test_documents/doc1_supervisory_letter.txt

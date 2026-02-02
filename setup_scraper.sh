#!/bin/bash
# Install dependencies for the Fed speech scraper

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "✓ Dependencies installed!"
echo ""
echo "You can now run the scraper:"
echo "  python3 scrape_fed_speeches.py --max-speeches 1000"

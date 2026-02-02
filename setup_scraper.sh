#!/bin/bash
# Install dependencies for the Fed speech scraper

echo "Installing Python dependencies..."

# Try to install normally first
if pip3 install -r requirements.txt 2>/dev/null; then
    echo ""
    echo "✓ Dependencies installed!"
    echo ""
    echo "You can now run the scraper:"
    echo "  python3 scrape_fed_speeches.py --max-speeches 1000"
    exit 0
fi

# If that fails (externally-managed-environment), use --user flag
echo "System requires user installation..."
if pip3 install --user -r requirements.txt; then
    echo ""
    echo "✓ Dependencies installed to user directory!"
    echo ""
    echo "You can now run the scraper:"
    echo "  python3 scrape_fed_speeches.py --max-speeches 1000"
    exit 0
fi

# If both fail, suggest alternatives
echo ""
echo "✗ Installation failed. Try one of these alternatives:"
echo ""
echo "Option 1: Install with --break-system-packages (not recommended)"
echo "  pip3 install --break-system-packages -r requirements.txt"
echo ""
echo "Option 2: Use a virtual environment (recommended)"
echo "  python3 -m venv venv"
echo "  source venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  python3 scrape_fed_speeches.py --max-speeches 1000"
echo ""
echo "Option 3: Install via Homebrew"
echo "  brew install python-requests"
exit 1

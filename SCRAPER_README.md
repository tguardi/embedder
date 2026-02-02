# Federal Reserve Speech Scraper

Scrape real Federal Reserve speeches from [federalreserve.gov](https://www.federalreserve.gov/newsevents/speeches.htm) for use as test data in the embedding pipeline.

## Why Use Real Speeches?

- **Realistic content**: Actual financial policy documents with technical language
- **Varied length**: Speeches range from 2,000 to 10,000+ words
- **Public domain**: Federal Reserve content is not copyrighted
- **High quality**: Professional, well-structured documents
- **Better benchmarking**: Tests pipeline on real-world data

## Quick Start

### 1. Install Dependencies

```bash
./setup_scraper.sh
```

This installs:
- `requests` - HTTP library
- `beautifulsoup4` - HTML parsing
- `tqdm` - Progress bars (already included)

### 2. Scrape Speeches

```bash
# Default: 1000 most recent speeches
python3 scrape_fed_speeches.py

# Custom output directory
python3 scrape_fed_speeches.py --output-dir my_speeches

# Specific number of speeches
python3 scrape_fed_speeches.py --max-speeches 500

# Start from a specific year
python3 scrape_fed_speeches.py --start-year 2025 --max-speeches 100
```

## How It Works

1. **Fetches year indexes**: Scrapes speech listing pages (e.g., `/newsevents/speech/2025-speeches.htm`)
2. **Extracts metadata**: Gets title, date, speaker, and URL for each speech
3. **Downloads content**: Fetches full text from individual speech pages
4. **Saves as JSON**: Creates structured documents matching the pipeline format

## Output Format

Each speech is saved as a JSON file:

```json
{
  "id": "speech_0042",
  "title": "The Inflation Outlook",
  "date": "12/15/2025",
  "speaker": "Governor Stephen I. Miran",
  "year": 2025,
  "url": "https://www.federalreserve.gov/newsevents/speech/miran20251215a.htm",
  "content": "Thank you, Mr. Secretary...",
  "scraped_at": "2026-02-02T10:30:45.123456",
  "type": "fed_speech"
}
```

## Rate Limiting

The scraper is **polite and respectful** of the Federal Reserve's servers:

- 1 second delay between requests
- Clear user agent identification
- Robust error handling
- Skips speeches that fail to download

**Expected time for 1000 speeches**: 20-30 minutes

## Usage with Pipeline

Once scraped, use the speeches with the embedding pipeline:

```bash
# Run benchmarks
./parallel_batch.sh batch_fed_speeches "YOUR_API_URL" 10 10 \
  --vector-field bge_m3_vector \
  --vector-dims 1024 \
  --chunker paragraph \
  --chunk-size 6000 \
  --api-batch-size 16 \
  --no-verify-ssl
```

## Command Options

```bash
python3 scrape_fed_speeches.py [OPTIONS]

Options:
  --output-dir DIR       Output directory (default: batch_fed_speeches)
  --max-speeches N       Maximum speeches to scrape (default: 1000)
  --start-year YEAR      Year to start from (default: 2026)
  --help                 Show help message
```

## What Gets Scraped

- **Date**: Publication date (MM/DD/YYYY)
- **Title**: Full speech title
- **Speaker**: Name and title (e.g., "Governor John Doe")
- **Content**: Full speech text
- **URL**: Source URL for reference
- **Metadata**: Scrape timestamp, year, document type

## Typical Speech Statistics

Based on recent Federal Reserve speeches:

| Metric | Range |
|--------|-------|
| Length | 2,000 - 12,000 words |
| File size | 10-60 KB |
| Paragraphs | 20-100 |
| Chunks (6000 tokens) | 1-5 chunks |

## Troubleshooting

### Import Error: No module named 'bs4'

```bash
./setup_scraper.sh
```

### Connection Errors

- Check internet connection
- Federal Reserve website might be down temporarily
- Try again later

### Empty Content

Some speeches may have unusual HTML structure and fail to parse. The scraper will skip these and continue.

### Rate Limiting Concerns

The scraper includes 1-second delays between requests. This is intentional and respectful. Do not modify the `REQUEST_DELAY` to be faster.

## Legal & Ethical Notes

- Federal Reserve content is **not copyrighted** and is in the public domain
- The scraper identifies itself with a clear user agent
- Rate limiting ensures minimal server load
- This is for **educational and research purposes**
- Follow the Federal Reserve's [terms of use](https://www.federalreserve.gov/policy.htm)

## Comparison with Synthetic Data

| Feature | Synthetic Data | Fed Speeches |
|---------|----------------|--------------|
| Speed | 5 seconds | 20-30 minutes |
| Realism | Moderate | High |
| Variety | Template-based | Natural variation |
| Length | 1-3 KB | 10-60 KB |
| Use case | Quick tests | Production benchmarks |

## Example Workflow

```bash
# 1. Install dependencies (first time only)
./setup_scraper.sh

# 2. Scrape 1000 speeches
python3 scrape_fed_speeches.py --max-speeches 1000

# 3. Run benchmark
./parallel_batch.sh batch_fed_speeches "YOUR_API" 10 10 \
  --chunker paragraph --api-batch-size 16 --no-verify-ssl

# 4. View results
./view_run_history.sh --top
```

## Advanced Usage

### Scrape Specific Year Range

```bash
# Get only 2024 speeches
python3 scrape_fed_speeches.py --start-year 2024 --max-speeches 200

# The scraper will stop when it exhausts 2024
```

### Update Dataset

```bash
# Append new speeches to existing directory
python3 scrape_fed_speeches.py --output-dir batch_fed_speeches --max-speeches 50
```

Note: The scraper will overwrite files with the same ID, so use different output directories for separate datasets.

## File Structure

```
batch_fed_speeches/
├── speech_0000.json  # Most recent speech
├── speech_0001.json
├── speech_0002.json
├── ...
└── speech_0999.json  # 1000th speech
```

Files are numbered in chronological order from most recent to oldest.

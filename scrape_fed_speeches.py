#!/usr/bin/env python3
"""
Scrape Federal Reserve speeches from federalreserve.gov

Fetches speeches from recent years and saves them as JSON documents
for use in embedding pipeline testing.

Usage:
    python scrape_fed_speeches.py [--output-dir DIR] [--max-speeches N]

Example:
    python scrape_fed_speeches.py --output-dir batch_fed_speeches --max-speeches 1000
"""

import argparse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
import trafilatura

# Base URL for Federal Reserve
BASE_URL = "https://www.federalreserve.gov"

# User agent to identify ourselves
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Rate limiting: delay between requests (be respectful)
REQUEST_DELAY = 1.0  # seconds


def fetch_year_speeches(year: int) -> List[Dict]:
    """Fetch all speeches from a specific year."""
    url = f"{BASE_URL}/newsevents/speech/{year}-speeches.htm"

    print(f"Fetching speeches from {year}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error fetching {year}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    speeches = []

    # Find all speech links (they're in italics and link to /newsevents/speech/*.htm)
    for link in soup.find_all('a', href=re.compile(r'/newsevents/speech/\w+\.htm$')):
        # Get the full URL
        speech_url = BASE_URL + link['href']

        # Get the title (link text)
        title = link.get_text(strip=True)

        # Try to find the date and speaker by looking at surrounding elements
        # The structure is: date, title link, speaker, location
        parent = link.find_parent()
        if parent:
            text = parent.get_text()

            # Extract date (MM/DD/YYYY format at beginning)
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
            date = date_match.group(1) if date_match else None

            # Extract speaker (looks for "Governor X" or "Chair X" or "Vice Chair X")
            speaker_match = re.search(r'((?:Governor|Chair|Vice Chair)[^\n]+?)(?:\n|At)', text)
            speaker = speaker_match.group(1).strip() if speaker_match else None

            speeches.append({
                'url': speech_url,
                'title': title,
                'date': date,
                'speaker': speaker,
                'year': year
            })

    print(f"  Found {len(speeches)} speeches from {year}")
    return speeches


def fetch_speech_content(speech_info: Dict) -> Optional[str]:
    """Fetch and extract the full text content of a speech using trafilatura."""
    url = speech_info['url']

    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            print(f"  Error: trafilatura failed to download {url}")
            return None

        content = trafilatura.extract(downloaded)
        return content

    except Exception as e:
        print(f"  Error fetching speech {url}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Federal Reserve speeches for embedding pipeline testing"
    )
    parser.add_argument(
        '--output-dir',
        default='batch_fed_speeches',
        help='Output directory for scraped speeches (default: batch_fed_speeches)'
    )
    parser.add_argument(
        '--max-speeches',
        type=int,
        default=1000,
        help='Maximum number of speeches to scrape (default: 1000)'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2026,
        help='Year to start scraping from (default: 2026)'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("FEDERAL RESERVE SPEECH SCRAPER")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print(f"Target: {args.max_speeches} speeches")
    print(f"Starting from year: {args.start_year}")
    print("")

    # Collect speech metadata from multiple years
    all_speeches = []
    current_year = args.start_year

    while len(all_speeches) < args.max_speeches and current_year >= 2006:
        year_speeches = fetch_year_speeches(current_year)
        all_speeches.extend(year_speeches)
        current_year -= 1
        time.sleep(REQUEST_DELAY)  # Be polite

    # Limit to max_speeches
    all_speeches = all_speeches[:args.max_speeches]

    print("")
    print(f"Found {len(all_speeches)} speeches to download")
    print("")

    # Download full content for each speech
    successful = 0
    failed = 0

    for i, speech_info in enumerate(all_speeches):
        print(f"[{i+1}/{len(all_speeches)}] Fetching: {speech_info['title'][:60]}...")

        content = fetch_speech_content(speech_info)

        if content and len(content) > 500:  # Ensure we got substantial content
            # Create document
            doc = {
                'id': f"speech_{i:04d}",
                'title': speech_info['title'],
                'date': speech_info['date'],
                'speaker': speech_info['speaker'],
                'year': speech_info['year'],
                'url': speech_info['url'],
                'content': content,
                'scraped_at': datetime.now().isoformat(),
                'type': 'fed_speech'
            }

            # Save to file
            output_path = output_dir / f"speech_{i:04d}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(doc, f, indent=2, ensure_ascii=False)

            successful += 1

            if (i + 1) % 10 == 0:
                print(f"  Progress: {successful} speeches saved")
        else:
            print(f"  ✗ Failed to fetch content (too short or error)")
            failed += 1

        # Rate limiting
        time.sleep(REQUEST_DELAY)

    print("")
    print("=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)
    print(f"Successfully scraped: {successful} speeches")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}")
    print("")
    print("You can now use these speeches with:")
    print(f"  ./parallel_batch.sh {output_dir} YOUR_API_URL INSTANCES WORKERS \\")
    print("    --vector-field bge_m3_vector \\")
    print("    --vector-dims 1024 \\")
    print("    --chunker paragraph \\")
    print("    --chunk-size 6000 \\")
    print("    --api-batch-size 16 \\")
    print("    --no-verify-ssl")


if __name__ == '__main__':
    main()

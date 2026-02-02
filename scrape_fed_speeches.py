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
    """Fetch the full text content of a speech."""
    url = speech_info['url']

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  Error fetching speech {url}: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Remove script, style, and navigation elements
    for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()

    # Try multiple strategies to find the main content
    content_div = None

    # Strategy 1: Look for div with ID 'article'
    content_div = soup.find('div', id='article')

    # Strategy 2: Look for div with specific content classes
    if not content_div:
        content_div = soup.find('div', class_='col-xs-12 col-sm-8 col-md-8')

    # Strategy 3: Look for common content container classes
    if not content_div:
        for class_pattern in [r'col-xs-12', r'content', r'main']:
            content_div = soup.find('div', class_=re.compile(class_pattern))
            if content_div:
                break

    # Strategy 4: Look for main or article tags
    if not content_div:
        content_div = soup.find('main') or soup.find('article')

    # Strategy 5: Fall back to body
    if not content_div:
        content_div = soup.find('body')

    if not content_div:
        return None

    # Extract text content
    # Get all text, preserving paragraph breaks
    text_content = content_div.get_text(separator='\n\n', strip=True)

    # Clean up excessive whitespace and blank lines
    lines = []
    for line in text_content.split('\n'):
        line = line.strip()
        if line and len(line) > 15:  # Skip very short lines (navigation, etc.)
            lines.append(line)

    content = '\n\n'.join(lines)

    # Remove common navigation text patterns
    skip_patterns = [
        r'^Home\s*$',
        r'^Skip to main content\s*$',
        r'^Accessibility\s*$',
        r'^Federal Reserve Board\s*$',
        r'^News & Events\s*$',
        r'^Speeches\s*$',
    ]

    for pattern in skip_patterns:
        content = re.sub(pattern, '', content, flags=re.MULTILINE)

    # Clean up excessive whitespace again
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content


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
        default=2025,
        help='Year to start scraping from (default: 2025)'
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

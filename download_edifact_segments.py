#!/usr/bin/env python3
"""
Download EDIFACT segment definitions from UN/CEFACT UNTDID

This script scrapes the official UN/CEFACT UNTDID directory to extract
human-readable segment names, field descriptions, data types, and
mandatory/conditional status for EDIFACT versions D96A, D96B, and D01B.

Output: JSON files with complete segment definitions for each version
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# Base URLs for each EDIFACT version
VERSIONS = {
    'D96A': 'https://service.unece.org/trade/untdid/d96a/trsd/',
    'D96B': 'https://service.unece.org/trade/untdid/d96b/trsd/',
    'D01B': 'https://service.unece.org/trade/untdid/d01b/trsd/'
}

# Output directory
OUTPUT_DIR = Path('implementation_guides/edifact_segments')

# Rate limiting (seconds between requests)
RATE_LIMIT = 0.5


def fetch_page(url: str) -> Optional[BeautifulSoup]:
    """Fetch and parse an HTML page"""
    try:
        print(f"  Fetching: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def extract_segment_list(base_url: str) -> List[str]:
    """Extract list of segment codes from the index page"""
    index_url = base_url + 'trsdi1.htm'
    soup = fetch_page(index_url)

    if not soup:
        return []

    segments = []

    # Find all links in the page that match segment pattern
    for link in soup.find_all('a', href=True):
        href = link.get('href', '')
        # Segment links can be:
        # - Direct: 'trsdnad.htm'
        # - Relative: '../trsd/trsdnad.htm'
        # Extract just the filename
        filename = href.split('/')[-1] if '/' in href else href

        if filename.startswith('trsd') and filename.endswith('.htm') and filename != 'trsdi1.htm':
            # Extract segment code from filename (e.g., 'trsdnad.htm' -> 'NAD')
            segment_code = filename[4:-4].upper()
            segments.append(segment_code)

    # Remove duplicates and sort
    segments = sorted(set(segments))

    print(f"  Found {len(segments)} segments")
    return segments


def parse_segment_page(soup: BeautifulSoup, segment_code: str) -> Dict[str, Any]:
    """Parse a segment detail page and extract structure"""

    segment_data = {
        'code': segment_code,
        'name': '',
        'function': '',
        'fields': []
    }

    # Get text content
    text_content = soup.get_text()

    # Extract segment name
    # Pattern: "NAD    NAME AND ADDRESS" (after any header text, before Function)
    # Look for the segment code followed by multiple spaces and uppercase name
    name_pattern = rf'{segment_code}\s{{2,}}([A-Z][A-Z\s/\-,\.]+?)(?:\s*\n\s*\n|\s*Function:)'
    name_match = re.search(name_pattern, text_content)
    if name_match:
        segment_data['name'] = ' '.join(name_match.group(1).split())  # Normalize whitespace

    # Extract function/description
    # Pattern: "Function: description text"
    func_pattern = r'Function:\s*(.+?)(?:\n\s*\n|\n\d{3}\s+)'
    func_match = re.search(func_pattern, text_content, re.IGNORECASE | re.DOTALL)
    if func_match:
        # Clean up the function text (remove extra whitespace, newlines)
        function_text = func_match.group(1).strip()
        function_text = re.sub(r'\s+', ' ', function_text)
        segment_data['function'] = function_text

    # Parse field elements
    segment_data['fields'] = extract_fields_from_text(text_content)

    return segment_data


def extract_field_from_row(cells: List) -> Optional[Dict[str, Any]]:
    """Extract field data from table row cells"""
    try:
        # Typical structure: position | code | name | type | status
        # or: position | code | name | combined_type_status

        cell_texts = [cell.get_text(strip=True) for cell in cells]

        # Position (like '010', '020')
        position = cell_texts[0] if len(cell_texts) > 0 else ''
        if not re.match(r'^\d{3}$', position):
            return None  # Not a valid position, skip

        # Code (like '3035', 'C082')
        code = cell_texts[1] if len(cell_texts) > 1 else ''

        # Name
        name = cell_texts[2] if len(cell_texts) > 2 else ''

        # Data type and status (may be in separate or combined cells)
        data_type = cell_texts[3] if len(cell_texts) > 3 else ''
        status = cell_texts[4] if len(cell_texts) > 4 else 'Conditional'

        # If combined, try to split
        if 'M' in data_type or 'C' in data_type or 'Conditional' in data_type:
            # Status might be embedded in data type
            if data_type.endswith(' M'):
                status = 'Mandatory'
                data_type = data_type[:-2].strip()
            elif data_type.endswith(' C'):
                status = 'Conditional'
                data_type = data_type[:-2].strip()

        return {
            'position': position,
            'code': code,
            'name': name,
            'data_type': data_type,
            'status': status
        }

    except Exception as e:
        print(f"    Error parsing field row: {e}")
        return None


def extract_fields_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract field elements from preformatted text"""
    fields = []

    # Split into lines and process
    lines = text.split('\n')

    current_composite = None

    for line in lines:
        # Skip empty lines or header lines
        if not line.strip() or 'Change indicators' in line:
            continue

        # Pattern for top-level field (starts with position number at column 0-1)
        # Format: "010   3035  PARTY QUALIFIER                                       M  an..3"
        top_level_pattern = r'^(\d{3})\s+([A-Z0-9]+)\s+(.+?)\s+(M|C)\s+(a?n?\.{0,2}\d+)?\s*$'
        top_match = re.match(top_level_pattern, line)

        if top_match:
            position, code, name, status, data_type = top_match.groups()

            # Clean up name (remove extra spaces)
            name = ' '.join(name.split())

            status_full = 'Mandatory' if status == 'M' else 'Conditional'
            data_type = data_type if data_type else ''

            field_data = {
                'position': position,
                'code': code,
                'name': name,
                'data_type': data_type,
                'status': status_full
            }

            # Check if this is a composite (code starts with 'C')
            if code.startswith('C'):
                field_data['sub_elements'] = []
                current_composite = field_data
            else:
                current_composite = None

            fields.append(field_data)
            continue

        # Pattern for sub-element (indented with spaces)
        # Format: "      3039   Party id. identification                             M  an..35"
        sub_pattern = r'^\s{4,}(\d{4})\s+(.+?)\s+(M|C)\s+(a?n?\.{0,2}\d+)?\s*$'
        sub_match = re.match(sub_pattern, line)

        if sub_match and current_composite:
            code, name, status, data_type = sub_match.groups()

            # Clean up name
            name = ' '.join(name.split())

            status_full = 'Mandatory' if status == 'M' else 'Conditional'
            data_type = data_type if data_type else ''

            sub_element = {
                'code': code,
                'name': name,
                'data_type': data_type,
                'status': status_full
            }

            current_composite['sub_elements'].append(sub_element)

    return fields


def download_version(version: str, base_url: str) -> Dict[str, Any]:
    """Download all segments for a specific EDIFACT version"""
    print(f"\nDownloading {version}...")

    # Get list of segments
    segments_list = extract_segment_list(base_url)

    if not segments_list:
        print(f"  ERROR: No segments found for {version}")
        return {'version': version, 'segments': {}}

    # Download each segment
    version_data = {
        'version': version,
        'segments': {}
    }

    for i, segment_code in enumerate(segments_list, 1):
        print(f"  [{i}/{len(segments_list)}] Downloading {segment_code}...")

        # Construct segment URL (e.g., trsdnad.htm)
        segment_url = base_url + f'trsd{segment_code.lower()}.htm'

        # Fetch and parse
        soup = fetch_page(segment_url)
        if soup:
            segment_data = parse_segment_page(soup, segment_code)
            version_data['segments'][segment_code] = segment_data

        # Rate limiting
        time.sleep(RATE_LIMIT)

    print(f"  Downloaded {len(version_data['segments'])} segments for {version}")
    return version_data


def save_json(data: Dict[str, Any], filename: str):
    """Save data to JSON file"""
    output_path = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  Saved to: {output_path}")


def main():
    """Main download orchestrator"""
    print("EDIFACT Segment Definition Downloader")
    print("=" * 60)
    print(f"Downloading from UN/CEFACT UNTDID")
    print(f"Versions: {', '.join(VERSIONS.keys())}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Rate limit: {RATE_LIMIT}s between requests")
    print("=" * 60)

    for version, base_url in VERSIONS.items():
        try:
            # Download version
            version_data = download_version(version, base_url)

            # Save to JSON
            filename = f'{version.lower()}_segments.json'
            save_json(version_data, filename)

        except Exception as e:
            print(f"\nERROR processing {version}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Download complete!")
    print(f"Check {OUTPUT_DIR} for output files")


if __name__ == '__main__':
    main()

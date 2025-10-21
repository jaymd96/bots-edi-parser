#!/usr/bin/env python3
"""
Test the human-readable name transformer
"""

import json
from edi_parser import parse_edi_file_path, add_human_readable_names

def show_segment(data, segment_id, depth=0):
    """Extract and display a specific segment from parsed data"""
    if isinstance(data, dict):
        # Handle both BOTSID (original/dual/metadata) and segment_id (replace mode)
        if data.get('BOTSID') == segment_id or data.get('segment_id') == segment_id:
            return data
        if '_children' in data:
            for child in data['_children']:
                result = show_segment(child, segment_id, depth + 1)
                if result:
                    return result
        if 'children' in data and isinstance(data['children'], list):
            for child in data['children']:
                result = show_segment(child, segment_id, depth + 1)
                if result:
                    return result
    return None

def main():
    print("=" * 80)
    print("Testing Human-Readable Name Transformer")
    print("=" * 80)

    # Test with 835 file
    print("\n1. Testing with 835 Healthcare Claim Payment")
    print("-" * 80)

    result = parse_edi_file_path('complete_835.txt', 'x12', 'envelope')
    print(f"✓ Parsed 835 file successfully")

    # Find BPR segment in original
    bpr_original = show_segment(result['data'], 'BPR')
    if bpr_original:
        print("\nOriginal BPR segment (technical codes only):")
        print(json.dumps(bpr_original, indent=2))

    # Transform with dual mode (default)
    print("\n" + "=" * 80)
    print("MODE 1: DUAL - Keep technical codes AND add readable names")
    print("=" * 80)
    transformed_dual = add_human_readable_names(result['data'], '835', '5010', 'dual')
    bpr_dual = show_segment(transformed_dual, 'BPR')
    if bpr_dual:
        print(json.dumps(bpr_dual, indent=2))

    # Transform with replace mode
    print("\n" + "=" * 80)
    print("MODE 2: REPLACE - Replace technical codes with readable names")
    print("=" * 80)
    transformed_replace = add_human_readable_names(result['data'], '835', '5010', 'replace')
    bpr_replace = show_segment(transformed_replace, 'BPR')
    if bpr_replace:
        print(json.dumps(bpr_replace, indent=2))

    # Transform with metadata mode
    print("\n" + "=" * 80)
    print("MODE 3: METADATA - Add full metadata including descriptions")
    print("=" * 80)
    transformed_metadata = add_human_readable_names(result['data'], '835', '5010', 'metadata')
    bpr_metadata = show_segment(transformed_metadata, 'BPR')
    if bpr_metadata:
        print(json.dumps(bpr_metadata, indent=2))

    # Test with 837 file
    print("\n\n" + "=" * 80)
    print("2. Testing with 837 Healthcare Claim")
    print("=" * 80)

    result_837 = parse_edi_file_path('complete_837.txt', 'x12', 'envelope')
    print(f"✓ Parsed 837 file successfully")

    # Find NM1 segment in original
    nm1_original = show_segment(result_837['data'], 'NM1')
    if nm1_original:
        print("\nOriginal NM1 segment (technical codes only):")
        print(json.dumps(nm1_original, indent=2))

    # Transform with dual mode
    print("\n" + "=" * 80)
    print("Transformed NM1 segment (DUAL mode):")
    print("=" * 80)
    transformed_837 = add_human_readable_names(result_837['data'], '837', '5010', 'dual')
    nm1_dual = show_segment(transformed_837, 'NM1')
    if nm1_dual:
        print(json.dumps(nm1_dual, indent=2))

    print("\n" + "=" * 80)
    print("✓ Transformer testing complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()

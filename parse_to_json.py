#!/usr/bin/env python3
"""
Parse the fixed EDI files to JSON
"""

import sys
import json
sys.path.insert(0, '/Users/james/Projects/BotsRipout/edi_parser')

import edi_parser

print("=" * 80)
print("Parsing 835 Healthcare Claim Payment file to JSON")
print("=" * 80)

result_835 = edi_parser.parse_file(
    filepath='/Users/james/Projects/BotsRipout/edi_parser/complete_835.txt',
    editype='x12',
    messagetype='envelope',
    field_validation_mode='lenient',
    empty_segment_handling='skip'
)

if result_835['success']:
    print(f"✓ Successfully parsed 835 file")
    print(f"  Messages: {result_835['message_count']}")

    # Save to JSON file
    with open('835_parsed.json', 'w') as f:
        json.dump(result_835['data'], f, indent=2)
    print(f"  Saved to: 835_parsed.json")

    # Show a preview
    print("\nPreview of parsed data structure:")
    print(json.dumps(result_835['data'], indent=2)[:500] + "...")
else:
    print(f"✗ Failed to parse 835 file")
    for error in result_835['errors']:
        print(f"  - {error}")

print("\n" + "=" * 80)
print("Parsing 837 Healthcare Claim file to JSON")
print("=" * 80)

result_837 = edi_parser.parse_file(
    filepath='/Users/james/Projects/BotsRipout/edi_parser/complete_837.txt',
    editype='x12',
    messagetype='envelope',
    field_validation_mode='lenient',
    empty_segment_handling='skip'
)

if result_837['success']:
    print(f"✓ Successfully parsed 837 file")
    print(f"  Messages: {result_837['message_count']}")

    # Save to JSON file
    with open('837_parsed.json', 'w') as f:
        json.dump(result_837['data'], f, indent=2)
    print(f"  Saved to: 837_parsed.json")

    # Show a preview
    print("\nPreview of parsed data structure:")
    print(json.dumps(result_837['data'], indent=2)[:500] + "...")
else:
    print(f"✗ Failed to parse 837 file")
    for error in result_837['errors']:
        print(f"  - {error}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print(f"835 file: {'PARSED ✓' if result_835['success'] else 'FAILED ✗'}")
print(f"837 file: {'PARSED ✓' if result_837['success'] else 'FAILED ✗'}")

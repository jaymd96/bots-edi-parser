#!/usr/bin/env python3
"""
Example: Using EDIFACT Segment Definitions

Demonstrates how to use the field_mappings.edifact package to look up
human-readable segment and field names.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from edi_parser.field_mappings import edifact

def main():
    print("EDIFACT Segment Definition Examples")
    print("=" * 60)

    # List available versions
    print("\nAvailable EDIFACT versions:")
    versions = edifact.list_versions()
    for version in versions:
        segment_count = len(edifact.list_segments(version))
        print(f"  {version}: {segment_count} segments")

    # Get a segment definition
    print("\n" + "=" * 60)
    print("NAD Segment (D96A)")
    print("=" * 60)

    nad = edifact.get_segment('NAD', 'D96A')
    print(f"Code: {nad['code']}")
    print(f"Name: {nad['name']}")
    print(f"Function: {nad['function'][:80]}...")
    print(f"Fields: {len(nad['fields'])}")

    # Show fields
    print("\nFields:")
    for field in nad['fields'][:5]:  # Show first 5 fields
        print(f"\n  {field['position']}  {field['code']}  {field['name']}")
        print(f"      Type: {field['data_type']}, Status: {field['status']}")

        # Show sub-elements if composite
        if 'sub_elements' in field and field['sub_elements']:
            print(f"      Composite with {len(field['sub_elements'])} sub-elements:")
            for sub in field['sub_elements'][:3]:
                print(f"        ├─ {sub['code']}  {sub['name']}")

    # Get specific field
    print("\n" + "=" * 60)
    print("Specific Field Lookup")
    print("=" * 60)

    field = edifact.get_field('NAD', '010', 'D96A')
    print(f"NAD field 010: {field['name']}")
    print(f"  Code: {field['code']}")
    print(f"  Type: {field['data_type']}")
    print(f"  Status: {field['status']}")

    # Search segments
    print("\n" + "=" * 60)
    print("Search: Segments containing 'date'")
    print("=" * 60)

    results = edifact.search_segments('date', 'D01B')
    for result in results:
        print(f"  {result['code']:5s} - {result['name']}")

    # Compare versions
    print("\n" + "=" * 60)
    print("Version Comparison")
    print("=" * 60)

    for version in ['D96A', 'D96B', 'D01B']:
        segments = edifact.list_segments(version)
        print(f"{version}: {len(segments):3d} segments")

    # Show common segments
    print("\n" + "=" * 60)
    print("Common Commercial Segments")
    print("=" * 60)

    common = ['BGM', 'DTM', 'FTX', 'NAD', 'LIN', 'QTY', 'PRI', 'MOA']
    for code in common:
        seg = edifact.get_segment(code, 'D01B')
        if seg:
            print(f"  {code:5s} - {seg['name']}")

    # Using the SegmentDatabase class directly
    print("\n" + "=" * 60)
    print("Using SegmentDatabase Class")
    print("=" * 60)

    db = edifact.SegmentDatabase()

    # Get field by element code
    field = db.get_field_by_code('NAD', '3035', 'D96A')
    print(f"NAD element 3035: {field['name']}")

    # Search
    results = db.search_segments('monetary', 'D01B')
    print(f"\nSegments with 'monetary': {len(results)} found")
    for result in results:
        print(f"  {result['code']:5s} - {result['name']}")

    print("\n" + "=" * 60)
    print("Example complete!")


if __name__ == '__main__':
    main()

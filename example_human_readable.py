#!/usr/bin/env python3
"""
Example: Using the Human-Readable Name Transformer

This example demonstrates how to add human-readable field names to parsed EDI JSON.
"""

from edi_parser import parse_edi_file_path, add_human_readable_names
import json


def main():
    # Parse an 835 Healthcare Claim Payment file
    result = parse_edi_file_path('complete_835.txt', 'x12', 'envelope')
    print("Parsed 835 file successfully")

    # Option 1: DUAL mode (default) - Keep technical codes AND add readable names
    # This is the most common use case
    readable = add_human_readable_names(
        result['data'],
        transaction='835',
        version='5010',
        mode='dual'
    )

    print("\n" + "=" * 80)
    print("Example: BPR segment with human-readable names (DUAL mode)")
    print("=" * 80)
    print(json.dumps(find_segment(readable, 'BPR'), indent=2))

    # Option 2: REPLACE mode - Use snake_case readable names instead of codes
    # Good for applications that want fully readable JSON
    readable_replace = add_human_readable_names(
        result['data'],
        transaction='835',
        version='5010',
        mode='replace'
    )

    print("\n" + "=" * 80)
    print("Example: BPR segment with replaced field names (REPLACE mode)")
    print("=" * 80)
    bpr_replace = find_segment(readable_replace, 'BPR')
    if bpr_replace:
        # Show a few key fields
        print(f"Segment: {bpr_replace.get('segment_name', 'N/A')}")
        print(f"Payment Amount: ${bpr_replace.get('total_actual_provider_payment_amount', 'N/A')}")
        print(f"Payment Method: {bpr_replace.get('payment_method_code', 'N/A')}")
        print(f"Transaction Type: {bpr_replace.get('transaction_handling_code', 'N/A')}")

    # Option 3: METADATA mode - Add full metadata including data element numbers
    # Useful for validation and detailed analysis
    readable_metadata = add_human_readable_names(
        result['data'],
        transaction='835',
        version='5010',
        mode='metadata'
    )

    print("\n" + "=" * 80)
    print("Example: Field with metadata")
    print("=" * 80)
    bpr_meta = find_segment(readable_metadata, 'BPR')
    if bpr_meta:
        print("BPR02 (Payment Amount) metadata:")
        print(json.dumps(bpr_meta.get('BPR02_metadata', {}), indent=2))


def find_segment(data, segment_id):
    """Find a specific segment in parsed data"""
    if isinstance(data, dict):
        if data.get('BOTSID') == segment_id or data.get('segment_id') == segment_id:
            return data
        for key in ['_children', 'children']:
            if key in data and isinstance(data[key], list):
                for child in data[key]:
                    result = find_segment(child, segment_id)
                    if result:
                        return result
    return None


if __name__ == '__main__':
    main()

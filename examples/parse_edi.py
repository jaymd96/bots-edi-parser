#!/usr/bin/env python3
"""
Example script demonstrating how to use the EDI Parser

This script shows various ways to parse EDI files using the edi_parser library.
"""

import json
import sys
import os

# Add parent directory to path so we can import edi_parser
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import edi_parser


def example_parse_edifact():
    """Example: Parse an EDIFACT message"""
    print("=" * 60)
    print("Example 1: Parsing EDIFACT ORDERS message")
    print("=" * 60)

    # Sample EDIFACT ORDERS message
    edifact_content = """UNB+UNOC:3+SENDER123:14+RECEIVER456:14+20231020:1430+12345'UNH+1+ORDERS:D:96A:UN'BGM+220+PO123456+9'DTM+137:20231020:102'NAD+BY+BUYER123::92'NAD+SU+SUPPLIER789::92'UNS+D'UNT+7+1'UNZ+1+12345'"""

    result = edi_parser.parse_edi(
        content=edifact_content,
        editype='edifact',
        messagetype='ORDERS',
        charset='utf-8'
    )

    if result['success']:
        print(f"✓ Successfully parsed {result['message_count']} message(s)")
        print("\nParsed data (JSON):")
        print(json.dumps(result['data'], indent=2))
    else:
        print("✗ Parse failed!")
        print("Errors:", result['errors'])

    print()


def example_parse_x12():
    """Example: Parse an X12 850 Purchase Order"""
    print("=" * 60)
    print("Example 2: Parsing X12 850 Purchase Order")
    print("=" * 60)

    # Sample X12 850 message
    x12_content = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231020*1430*U*00401*000000001*0*P*>~GS*PO*SENDER*RECEIVER*20231020*1430*1*X*004010~ST*850*0001~BEG*00*SA*PO123456**20231020~REF*DP*DEPT001~PER*BD*JOHN DOE*TE*555-1234~N1*ST*SHIP TO NAME~N3*123 MAIN STREET~N4*ANYTOWN*CA*12345~PO1*1*10*EA*9.99*PE*IN*PRODUCT001~CTT*1~SE*10*0001~GE*1*1~IEA*1*000000001~"""

    result = edi_parser.parse_edi(
        content=x12_content,
        editype='x12',
        messagetype='850',
        charset='utf-8'
    )

    if result['success']:
        print(f"✓ Successfully parsed {result['message_count']} message(s)")
        print("\nParsed data (first 500 chars):")
        json_str = json.dumps(result['data'], indent=2)
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
    else:
        print("✗ Parse failed!")
        print("Errors:", result['errors'])

    print()


def example_parse_from_file():
    """Example: Parse EDI from a file"""
    print("=" * 60)
    print("Example 3: Parsing EDI from a file")
    print("=" * 60)

    # Create a temporary EDI file
    temp_file = '/tmp/test_edi.txt'
    with open(temp_file, 'w') as f:
        f.write("""UNB+UNOC:3+SENDER:14+RECEIVER:14+20231020:1430+1'UNH+1+ORDERS:D:96A:UN'BGM+220+ORDER1+9'UNT+3+1'UNZ+1+1'""")

    print(f"Created temporary file: {temp_file}")

    # Parse using file path
    result = edi_parser.parse_file(
        filepath=temp_file,
        editype='edifact',
        messagetype='ORDERS'
    )

    if result['success']:
        print(f"✓ Successfully parsed file")
        print("Message count:", result['message_count'])
    else:
        print("✗ Parse failed!")
        print("Errors:", result['errors'])

    # Clean up
    os.remove(temp_file)
    print(f"Removed temporary file: {temp_file}")
    print()


def example_supported_formats():
    """Example: Get supported EDI formats"""
    print("=" * 60)
    print("Example 4: List supported EDI formats")
    print("=" * 60)

    formats = edi_parser.get_supported_formats()

    print("Supported EDI formats:")
    for fmt, description in formats.items():
        print(f"  • {fmt:12} - {description}")

    print()


def example_with_options():
    """Example: Parse with custom options"""
    print("=" * 60)
    print("Example 5: Parsing with custom options")
    print("=" * 60)

    edifact_content = """UNB+UNOC:3+S:14+R:14+20231020:1430+1'UNH+1+ORDERS:D:96A:UN'BGM+220+O1+9'UNT+3+1'UNZ+1+1'"""

    result = edi_parser.parse_edi(
        content=edifact_content,
        editype='edifact',
        messagetype='ORDERS',
        debug=True,  # Enable debug logging
        checkunknownentities=False,  # Don't check for unknown entities
        continue_on_error=True  # Continue even with non-fatal errors
    )

    if result['success']:
        print("✓ Parse succeeded with custom options")
    else:
        print("✗ Parse failed")
        print("Errors:", result['errors'])

    print()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("EDI Parser - Usage Examples")
    print("=" * 60 + "\n")

    try:
        example_supported_formats()
        example_parse_edifact()
        example_parse_x12()
        example_parse_from_file()
        example_with_options()

        print("=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())

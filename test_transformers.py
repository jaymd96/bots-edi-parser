"""
Test script for 835 and 837P ontology transformers
"""

import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import edi_parser
from edi_parser.transformers.foundry_ontology.transform_835 import transform_835
from edi_parser.transformers.foundry_ontology.transform_837p import transform_837p


def test_835_transformer():
    """Test 835 transformer"""
    print("=" * 80)
    print("TESTING 835 TRANSFORMER")
    print("=" * 80)

    # Parse 835 file
    test_file = 'test_files/835/835-all-fields.dat'

    print(f"\n1. Parsing {test_file}...")
    try:
        result = edi_parser.parse_file(
            test_file,
            editype='x12',
            messagetype='835005010',
            field_validation_mode='lenient',
            continue_on_error=True
        )

        if result['errors']:
            print(f"   WARNING: {len(result['errors'])} parse errors")
            for err in result['errors'][:3]:
                print(f"     - {err}")

        if result['data'] is None:
            print(f"   ✗ Parse returned no data")
            return

        print(f"   ✓ Parsed successfully")
        print(f"   Data keys: {list(result['data'].keys())[:10]}")

    except Exception as e:
        print(f"   ✗ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Apply transformer
    print("\n2. Applying transformer...")
    try:
        transformed = transform_835(result['data'], source_filename=test_file)

        print(f"   ✓ Transform successful")
        print(f"   Output type: {type(transformed)}")
        print(f"   Output length: {len(transformed)}")

        if transformed:
            payment = transformed[0]
            print(f"   Payment object keys: {len(payment.keys())} keys")
            print(f"   Object type: {payment.get('objectType')}")
            print(f"   Patient control number: {payment.get('patientControlNumber')}")
            print(f"   Charge amount: ${payment.get('chargeAmount')}")
            print(f"   Payment amount: ${payment.get('paymentAmount')}")

            # Check key sections
            sections = ['subscriber', 'patient', 'payer', 'payee', 'serviceProvider',
                       'adjustments', 'serviceLines', 'transaction']
            print("\n   Sections present:")
            for section in sections:
                exists = section in payment
                symbol = "✓" if exists else "✗"
                print(f"     {symbol} {section}")

            # Save output
            output_file = 'test_output_835.json'
            with open(output_file, 'w') as f:
                json.dump(transformed, f, indent=2)
            print(f"\n   Saved output to {output_file}")

    except Exception as e:
        print(f"   ✗ Transform failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n✓ 835 transformer test complete")


def test_837p_transformer():
    """Test 837P transformer"""
    print("\n" + "=" * 80)
    print("TESTING 837P TRANSFORMER")
    print("=" * 80)

    # Parse 837P file
    test_file = 'test_files/837/837P-all-fields.dat'

    print(f"\n1. Parsing {test_file}...")
    try:
        result = edi_parser.parse_file(
            test_file,
            editype='x12',
            messagetype='837005010',
            field_validation_mode='lenient',
            continue_on_error=True
        )

        if result['errors']:
            print(f"   WARNING: {len(result['errors'])} parse errors")
            for err in result['errors'][:3]:
                print(f"     - {err}")

        if result['data'] is None:
            print(f"   ✗ Parse returned no data")
            return

        print(f"   ✓ Parsed successfully")
        print(f"   Data keys: {list(result['data'].keys())[:10]}")

    except Exception as e:
        print(f"   ✗ Parse failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Apply transformer
    print("\n2. Applying transformer...")
    try:
        transformed = transform_837p(result['data'], source_filename=test_file)

        print(f"   ✓ Transform successful")
        print(f"   Output type: {type(transformed)}")
        print(f"   Output length: {len(transformed)}")

        if transformed:
            claim = transformed[0]
            print(f"   Claim object keys: {len(claim.keys())} keys")
            print(f"   Object type: {claim.get('objectType')}")
            print(f"   Patient control number: {claim.get('patientControlNumber')}")
            print(f"   Charge amount: ${claim.get('chargeAmount')}")

            # Check key sections
            sections = ['subscriber', 'patient', 'billingProvider', 'providers',
                       'diags', 'serviceLines', 'transaction']
            print("\n   Sections present:")
            for section in sections:
                exists = section in claim
                symbol = "✓" if exists else "✗"
                count = f" ({len(claim[section])} items)" if exists and isinstance(claim.get(section), list) else ""
                print(f"     {symbol} {section}{count}")

            # Save output
            output_file = 'test_output_837p.json'
            with open(output_file, 'w') as f:
                json.dump(transformed, f, indent=2)
            print(f"\n   Saved output to {output_file}")

    except Exception as e:
        print(f"   ✗ Transform failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n✓ 837P transformer test complete")


if __name__ == '__main__':
    test_835_transformer()
    test_837p_transformer()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)

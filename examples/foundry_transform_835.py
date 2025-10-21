#!/usr/bin/env python3
"""
Example: Transform 835 Electronic Remittance Advice to Foundry Ontology

This example demonstrates the complete workflow:
1. Parse 835 EDI file
2. Add human-readable field names
3. Transform to Foundry ontology schemas (denials and reason codes)
"""

import json
from edi_parser import parse_edi_file_path, add_human_readable_names, transform_835


def main():
    print("=" * 80)
    print("835 Electronic Remittance Advice → Foundry Ontology Transformation")
    print("=" * 80)

    # Step 1: Parse the 835 file
    print("\n1. Parsing 835 file...")
    result = parse_edi_file_path('complete_835.txt', 'x12', 'envelope')

    if not result['success']:
        print(f"✗ Parsing failed: {result.get('errors', [])}")
        return

    print("✓ Parsed 835 successfully")

    # Step 2: Add human-readable names (dual mode)
    print("\n2. Adding human-readable field names...")
    readable_json = add_human_readable_names(
        result['data'],
        transaction='835',
        version='5010',
        mode='dual'
    )
    print("✓ Added human-readable names")

    # Step 3: Prepare metadata and claim index
    print("\n3. Preparing payer metadata and claim index...")

    # Example payer metadata: maps payer_id to payer info
    payer_metadata = {
        # 'PAYER001': {'name': 'AETNA', ...},
        # These would come from your payer master list
    }

    # Claim index: maps client_claim_id (from 837P) to claim_id (from Foundry)
    # This is built from your previously processed 837P claims
    # In production, you would query Foundry to get this mapping
    claim_index = {
        # 'CLIENT_CLAIM_123': 'CLM_ABC123...',
        # This allows us to link denials back to the original claims
    }

    # Step 4: Transform to Foundry ontology
    print("\n4. Transforming to Foundry ontology schemas...")
    foundry_data = transform_835(
        readable_json,
        payer_metadata=payer_metadata,
        claim_index=claim_index
    )

    print("✓ Transformation complete!")

    # Display results
    print("\n" + "=" * 80)
    print("TRANSFORMATION RESULTS")
    print("=" * 80)

    print(f"\n❌ Denials extracted: {len(foundry_data['denials'])}")
    print(f"📝 Unique reason codes: {len(foundry_data['reason_codes'])}")

    # Show sample denial
    if foundry_data['denials']:
        print("\n" + "-" * 80)
        print("SAMPLE DENIAL RECORD")
        print("-" * 80)
        denial = foundry_data['denials'][0]
        print(json.dumps(denial, indent=2))

        # Show denial breakdown
        print("\n" + "-" * 80)
        print("DENIAL SUMMARY")
        print("-" * 80)

        # Group by denial type
        by_type = {}
        total_denied_amount = 0

        for d in foundry_data['denials']:
            dtype = d['denial_type']
            by_type[dtype] = by_type.get(dtype, 0) + 1
            total_denied_amount += d.get('total_denied', 0)

        print(f"\nTotal Denied Amount: ${total_denied_amount:.2f}")
        print("\nDenials by Type:")
        for dtype, count in by_type.items():
            print(f"  {dtype}: {count}")

    # Show reason codes
    if foundry_data['reason_codes']:
        print("\n" + "-" * 80)
        print("REASON CODES REFERENCE")
        print("-" * 80)
        for rc in foundry_data['reason_codes']:
            print(f"\n  Code {rc['reason_code']}: {rc['description']}")
            print(f"    Typical Action: {rc['typical_action']}")

    # Optional: Save to JSON files for Foundry ingestion
    print("\n" + "=" * 80)
    print("SAVING TO JSON FILES")
    print("=" * 80)

    output_files = {
        'denials_835.json': foundry_data['denials'],
        'reason_codes_835.json': foundry_data['reason_codes'],
    }

    for filename, data in output_files.items():
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {filename} ({len(data)} records)")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("""
    The extracted denial records are now ready for:

    1. Foundry ingestion into the Denial Record object
    2. Work queue item generation (based on business rules)
    3. Reviewer assignment (based on skills and availability)
    4. Analytics and denial pattern analysis

    Note: Priority scoring and work queue generation should be handled
    in downstream Foundry transforms or Python applications.
    """)

    print("\n" + "=" * 80)
    print("✓ Complete! Data ready for Foundry ingestion")
    print("=" * 80)


if __name__ == '__main__':
    main()

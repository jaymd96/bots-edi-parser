#!/usr/bin/env python3
"""
Example: Transform 837P Professional Claims to Foundry Ontology

This example demonstrates the complete workflow:
1. Parse 837P EDI file
2. Add human-readable field names
3. Transform to Foundry ontology schemas
"""

import json
from edi_parser import parse_edi_file_path, add_human_readable_names, transform_837p


def main():
    print("=" * 80)
    print("837P Professional Claims → Foundry Ontology Transformation")
    print("=" * 80)

    # Step 1: Parse the 837P file
    print("\n1. Parsing 837P file...")
    result = parse_edi_file_path('complete_837.txt', 'x12', 'envelope')

    if not result['success']:
        print(f"✗ Parsing failed: {result.get('errors', [])}")
        return

    print("✓ Parsed 837P successfully")

    # Step 2: Add human-readable names (dual mode)
    print("\n2. Adding human-readable field names...")
    readable_json = add_human_readable_names(
        result['data'],
        transaction='837',
        version='5010',
        mode='dual'
    )
    print("✓ Added human-readable names")

    # Step 3: Prepare metadata (in real use, this would come from your database)
    print("\n3. Preparing provider and payer metadata...")

    # Example provider metadata: maps NPI to provider_id
    # In production, load from your provider database
    provider_metadata = {
        # NPI: provider_id
        # These would be extracted from the EDI and looked up
    }

    # Example payer metadata: maps payer_id to payer info
    payer_metadata = {
        # 'PAYER001': {'name': 'AETNA', ...},
        # These would come from your payer master list
    }

    # Step 4: Transform to Foundry ontology
    print("\n4. Transforming to Foundry ontology schemas...")
    foundry_data = transform_837p(
        readable_json,
        provider_metadata=provider_metadata,
        payer_metadata=payer_metadata,
        source_filename='complete_837.txt'
    )

    print("✓ Transformation complete!")

    # Display results
    print("\n" + "=" * 80)
    print("TRANSFORMATION RESULTS")
    print("=" * 80)

    print(f"\n📋 Claims extracted: {len(foundry_data['claims'])}")
    print(f"💉 Services extracted: {len(foundry_data['services'])}")
    print(f"🏥 Diagnoses extracted: {len(foundry_data['diagnoses'])}")
    print(f"👨‍⚕️ Providers extracted: {len(foundry_data['providers'])}")
    print(f"💳 Payers extracted: {len(foundry_data['payers'])}")

    # Show sample claim
    if foundry_data['claims']:
        print("\n" + "-" * 80)
        print("SAMPLE CLAIM")
        print("-" * 80)
        claim = foundry_data['claims'][0]
        print(json.dumps(claim, indent=2))

    # Show sample service
    if foundry_data['services']:
        print("\n" + "-" * 80)
        print("SAMPLE SERVICE")
        print("-" * 80)
        service = foundry_data['services'][0]
        print(json.dumps(service, indent=2))

    # Show sample diagnosis
    if foundry_data['diagnoses']:
        print("\n" + "-" * 80)
        print("SAMPLE DIAGNOSIS")
        print("-" * 80)
        diagnosis = foundry_data['diagnoses'][0]
        print(json.dumps(diagnosis, indent=2))

    # Show sample provider
    if foundry_data['providers']:
        print("\n" + "-" * 80)
        print("SAMPLE PROVIDER")
        print("-" * 80)
        provider = foundry_data['providers'][0]
        print(json.dumps(provider, indent=2))

    # Optional: Save to JSON files for Foundry ingestion
    print("\n" + "=" * 80)
    print("SAVING TO JSON FILES")
    print("=" * 80)

    output_files = {
        'claims_837p.json': foundry_data['claims'],
        'services_837p.json': foundry_data['services'],
        'diagnoses_837p.json': foundry_data['diagnoses'],
        'providers_837p.json': foundry_data['providers'],
        'payers_837p.json': foundry_data['payers'],
    }

    for filename, data in output_files.items():
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {filename} ({len(data)} records)")

    print("\n" + "=" * 80)
    print("✓ Complete! Data ready for Foundry ingestion")
    print("=" * 80)


if __name__ == '__main__':
    main()

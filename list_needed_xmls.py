#!/usr/bin/env python3
"""
List all X12 transaction types and versions to find XML implementation guides
"""

import os
import re
from collections import defaultdict

x12_path = '/Users/james/Projects/BotsRipout/edi_parser/edi_parser/grammars/x12'

# Collect all grammars by version and transaction type
grammars_by_version = defaultdict(set)
all_transactions = set()

for version_dir in sorted(os.listdir(x12_path)):
    version_path = os.path.join(x12_path, version_dir)

    # Only process version directories (4-digit numbers)
    if not re.match(r'^\d{4}$', version_dir):
        continue

    if not os.path.isdir(version_path):
        continue

    # Find all transaction grammars in this version
    for filename in os.listdir(version_path):
        # Match pattern like 850004010.py (transaction 850, version 4010)
        match = re.match(r'^(\d{3})00(\d{4})\.py$', filename)
        if match:
            transaction = match.group(1)
            version = match.group(2)
            grammars_by_version[version].add(transaction)
            all_transactions.add(transaction)

print("=" * 80)
print("X12 GRAMMARS SUMMARY")
print("=" * 80)
print(f"Total versions: {len(grammars_by_version)}")
print(f"Total unique transaction types: {len(all_transactions)}")
print()

# Show breakdown by version
print("Grammars by version:")
for version in sorted(grammars_by_version.keys()):
    count = len(grammars_by_version[version])
    print(f"  {version}: {count} transaction types")

print()
print("=" * 80)
print("HEALTHCARE-SPECIFIC TRANSACTIONS (Priority for XML search)")
print("=" * 80)

# Healthcare transactions we care about most
healthcare_transactions = {
    '270': 'Health Care Eligibility Inquiry',
    '271': 'Health Care Eligibility Response',
    '276': 'Health Care Claim Status Request',
    '277': 'Health Care Claim Status Response',
    '278': 'Health Care Services Review',
    '820': 'Payment Order/Remittance Advice',
    '834': 'Benefit Enrollment and Maintenance',
    '835': 'Health Care Claim Payment/Advice',
    '837': 'Health Care Claim',
    '997': 'Functional Acknowledgment',
    '999': 'Implementation Acknowledgment',
}

print("\nHealthcare transactions found:")
for trans_code, description in sorted(healthcare_transactions.items()):
    if trans_code in all_transactions:
        versions_with_this = [v for v in sorted(grammars_by_version.keys())
                              if trans_code in grammars_by_version[v]]
        print(f"  {trans_code} - {description}")
        print(f"       Versions: {', '.join(versions_with_this)}")

print()
print("=" * 80)
print("MOST COMMON COMMERCIAL TRANSACTIONS")
print("=" * 80)

commercial_transactions = {
    '810': 'Invoice',
    '850': 'Purchase Order',
    '855': 'Purchase Order Acknowledgment',
    '856': 'Ship Notice/Manifest',
    '860': 'Purchase Order Change Request',
    '997': 'Functional Acknowledgment',
}

print("\nCommercial transactions found:")
for trans_code, description in sorted(commercial_transactions.items()):
    if trans_code in all_transactions:
        versions_with_this = [v for v in sorted(grammars_by_version.keys())
                              if trans_code in grammars_by_version[v]]
        print(f"  {trans_code} - {description}")
        print(f"       Versions: {', '.join(versions_with_this)}")

print()
print("=" * 80)
print("RECOMMENDED XML SEARCHES")
print("=" * 80)
print()
print("We should focus on version 5010 (HIPAA standard) for healthcare transactions.")
print("Here are the XML implementation guides to search for:")
print()

# Healthcare 5010 XMLs
if '5010' in grammars_by_version:
    healthcare_5010 = sorted(set(healthcare_transactions.keys()) & grammars_by_version['5010'])
    print("HIPAA 5010 Healthcare XMLs needed:")
    for trans in healthcare_5010:
        print(f"  - {trans}.5010.X*.xml - {healthcare_transactions[trans]}")

print()
print("Common versions for commercial transactions (4010, 5010):")
for version in ['4010', '5010']:
    if version in grammars_by_version:
        commercial_in_version = sorted(set(commercial_transactions.keys()) & grammars_by_version[version])
        if commercial_in_version:
            print(f"\n  Version {version}:")
            for trans in commercial_in_version:
                print(f"    - {trans}.{version}.xml - {commercial_transactions[trans]}")

print()
print("=" * 80)
print("SEARCH STRATEGY")
print("=" * 80)
print("""
1. Healthcare (HIPAA) 5010 - Most important, widely available
   Source: https://x12.org or https://github.com/imsweb/x12-parser

2. Commercial 4010/5010 - Common business transactions
   Source: https://x12.org, vendor sites

3. Use existing XML pattern to generate field names for others

The XMLs from imsweb/x12-parser are the best open-source option.
They have consistent formatting we can parse.
""")

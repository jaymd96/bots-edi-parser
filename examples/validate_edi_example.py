#!/usr/bin/env python3
"""
Example: Using the EDI validation API

This example demonstrates how to use the validate_edi() function to find
ALL errors in an EDI file and get human-readable, actionable error information.
"""

import edi_parser

# Example 1: Validate an X12 835 Healthcare Claim Payment file
print("Example 1: Validating X12 835 file")
print("=" * 60)

result = edi_parser.validate_file(
    filepath='../complete_835.txt',
    editype='x12',
    messagetype='envelope'
)

# Check if the file is valid
if result['valid']:
    print("✓ File is valid!")
else:
    print(f"✗ Found {result['error_count']} errors")
    print()

    # Print each error with details
    for i, error in enumerate(result['errors'], 1):
        print(f"{i}. {error['description']}")
        print(f"   Location: {error['location']['path']}")
        print(f"   Severity: {error['severity']}")

        if error['expected'] and error['actual']:
            print(f"   Expected: {error['expected']}")
            print(f"   Actual: {error['actual']}")

        print(f"   💡 {error['suggestion']}")
        print()

# Example 2: Using the summary
print("\n" + "=" * 60)
print("Example 2: Using the summary")
print("=" * 60)
print(result['summary'])

# Example 3: Filtering errors by severity
print("\n" + "=" * 60)
print("Example 3: Critical errors only")
print("=" * 60)

critical_errors = [e for e in result['errors'] if e['severity'] == 'critical']
if critical_errors:
    for error in critical_errors:
        print(f"CRITICAL: {error['description']}")
else:
    print("No critical errors found")

# Example 4: Filtering by category
print("\n" + "=" * 60)
print("Example 4: Field validation errors only")
print("=" * 60)

field_errors = [e for e in result['errors'] if e['category'] == 'field_validation']
if field_errors:
    for error in field_errors:
        print(f"Field {error['location']['field']}: {error['description']}")
else:
    print("No field validation errors found")

# Example 5: Programmatic error handling
print("\n" + "=" * 60)
print("Example 5: Programmatic validation")
print("=" * 60)

def validate_edi_file(filepath, editype, messagetype):
    """
    Validate an EDI file and return True if valid, False otherwise.
    Print detailed errors if validation fails.
    """
    result = edi_parser.validate_file(filepath, editype, messagetype)

    if result['valid']:
        print(f"✓ {filepath} is valid")
        return True
    else:
        print(f"✗ {filepath} has {result['error_count']} errors:")

        # Group by severity
        by_severity = {}
        for error in result['errors']:
            severity = error['severity']
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(error)

        for severity in ['critical', 'error', 'warning']:
            if severity in by_severity:
                print(f"\n  {severity.upper()}: {len(by_severity[severity])}")
                for error in by_severity[severity][:3]:  # Show first 3
                    print(f"    - {error['description'][:80]}...")

        return False

# Validate multiple files
files_to_validate = [
    ('../complete_835.txt', 'x12', 'envelope'),
    ('../complete_837.txt', 'x12', 'envelope'),
]

print("\nValidating multiple files:")
for filepath, editype, messagetype in files_to_validate:
    validate_edi_file(filepath, editype, messagetype)
    print()

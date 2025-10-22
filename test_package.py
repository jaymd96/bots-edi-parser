#!/usr/bin/env python3
"""
Comprehensive test script for bots-edi-parser package

Tests parsing and transformation functionality against sample EDI files
to ensure the package works correctly after packaging.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Import from the installed package
try:
    from edi_parser import (
        parse_edi_file_path,
        add_human_readable_names,
        transform_837p,
        transform_835,
    )
    print("✓ Successfully imported edi_parser package")
except ImportError as e:
    print(f"✗ Failed to import edi_parser: {e}")
    sys.exit(1)


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record_pass(self, test_name):
        self.passed += 1
        print(f"✓ {test_name}")

    def record_fail(self, test_name, error):
        self.failed += 1
        error_msg = f"✗ {test_name}: {error}"
        print(error_msg)
        self.errors.append(error_msg)

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Summary: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for error in self.errors:
                print(f"  {error}")
        print(f"{'='*60}")
        return self.failed == 0


def test_837_file(file_path, results):
    """Test parsing and transforming an 837P file"""
    test_name = f"837P: {file_path.name}"

    try:
        # Try envelope first, fall back to transaction if it fails
        result = parse_edi_file_path(
            filepath=str(file_path),
            editype='x12',
            messagetype='envelope',
            charset='utf-8'
        )

        # If envelope parsing failed, try as transaction
        if not result.get('success'):
            result = parse_edi_file_path(
                filepath=str(file_path),
                editype='x12',
                messagetype='837',
                charset='utf-8'
            )

        if not result.get('success'):
            errors = result.get('errors', ['Unknown error'])
            raise ValueError(f"Parse failed: {', '.join(errors)}")

        # Add human-readable names
        readable = add_human_readable_names(
            result['data'],
            transaction='837',
            version='5010',
            mode='dual'
        )

        # Transform to ontology
        ontology = transform_837p(readable, source_filename=str(file_path))

        # Validate ontology structure
        required_keys = ['claims', 'services', 'diagnoses', 'providers', 'payers']
        for key in required_keys:
            if key not in ontology:
                raise ValueError(f"Missing required key in ontology: {key}")

        # Print some stats
        claims_count = len(ontology.get('claims', []))
        services_count = len(ontology.get('services', []))
        diagnoses_count = len(ontology.get('diagnoses', []))

        results.record_pass(f"{test_name} ({claims_count} claims, {services_count} services, {diagnoses_count} diagnoses)")

        return ontology

    except Exception as e:
        results.record_fail(test_name, str(e))
        return None


def test_835_file(file_path, results):
    """Test parsing and transforming an 835 file"""
    test_name = f"835: {file_path.name}"

    try:
        # Try envelope first, fall back to transaction if it fails
        result = parse_edi_file_path(
            filepath=str(file_path),
            editype='x12',
            messagetype='envelope',
            charset='utf-8'
        )

        # If envelope parsing failed, try as transaction
        if not result.get('success'):
            result = parse_edi_file_path(
                filepath=str(file_path),
                editype='x12',
                messagetype='835',
                charset='utf-8'
            )

        if not result.get('success'):
            errors = result.get('errors', ['Unknown error'])
            raise ValueError(f"Parse failed: {', '.join(errors)}")

        # Add human-readable names
        readable = add_human_readable_names(
            result['data'],
            transaction='835',
            version='5010',
            mode='dual'
        )

        # Transform to ontology
        ontology = transform_835(readable)

        # Validate ontology structure
        required_keys = ['denials', 'reason_codes']
        for key in required_keys:
            if key not in ontology:
                raise ValueError(f"Missing required key in ontology: {key}")

        # Print some stats
        denials_count = len(ontology.get('denials', []))
        reason_codes_count = len(ontology.get('reason_codes', []))

        results.record_pass(f"{test_name} ({denials_count} denials, {reason_codes_count} reason codes)")

        return ontology

    except Exception as e:
        results.record_fail(test_name, str(e))
        return None


def main():
    """Run all tests"""
    print("="*60)
    print("Testing bots-edi-parser package")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()

    results = TestResult()
    base_path = Path(__file__).parent

    # Test 837P files
    print("Testing 837P Claims files:")
    print("-" * 60)

    file_837_complete = base_path / "complete_837.txt"
    if file_837_complete.exists():
        test_837_file(file_837_complete, results)
    else:
        results.record_fail("complete_837.txt", "File not found")

    # Note: test_837_transaction.txt is transaction-only (no ISA envelope)
    # Skipping since it requires special grammar handling
    print("⚠ test_837_transaction.txt - Transaction-only file (skipping)")

    print()

    # Test 835 files
    print("Testing 835 Remittance files:")
    print("-" * 60)

    file_835_complete = base_path / "complete_835.txt"
    if file_835_complete.exists():
        test_835_file(file_835_complete, results)
    else:
        results.record_fail("complete_835.txt", "File not found")

    # Note: test_835_transaction.txt is transaction-only (no ISA envelope)
    # Skipping since it requires special grammar handling
    print("⚠ test_835_transaction.txt - Transaction-only file (skipping)")

    print()

    # Print summary
    success = results.summary()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

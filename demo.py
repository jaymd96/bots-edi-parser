#!/usr/bin/env python3
"""
EDI Parser Demo - CLI to demonstrate parser capabilities

Usage:
    # Run a specific file
    python -m edi_parser.demo validate 835 test_files/835/835-all-fields.dat
    python -m edi_parser.demo parse 837 test_files/837/commercial.dat --lenient
    python -m edi_parser.demo --verbose validate 835 test_files/835/835-denial.dat

    # Browse and select from test files
    python -m edi_parser.demo browse 835
    python -m edi_parser.demo browse 837

    # List available test files
    python -m edi_parser.demo list 835
    python -m edi_parser.demo list 837

    # Run all test files in a directory
    python -m edi_parser.demo validate-all 835
    python -m edi_parser.demo parse-all 837 --lenient
"""

import sys
import os
import logging
import argparse
import json
from pathlib import Path

# Add parent to path if running as script
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).parent))

import edi_parser


class DemoRunner:
    """Demo class demonstrating EDI parser functionality"""

    def __init__(self, verbose=False):
        """Initialize demo runner with logging configuration"""
        self.setup_logging(verbose)
        self.logger = logging.getLogger(__name__)

    def setup_logging(self, verbose):
        """Configure logging based on verbosity level"""
        if verbose:
            level = logging.DEBUG
            format_str = '%(asctime)s [%(levelname)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s'
        else:
            level = logging.INFO
            format_str = '%(levelname)s: %(message)s'

        logging.basicConfig(
            level=level,
            format=format_str,
            datefmt='%H:%M:%S'
        )

    def format_error_details(self, error):
        """Format a single structured error object with rich details"""
        lines = []
        lines.append(f"  [{error['code']}] {error['severity'].upper()}")
        lines.append(f"  Category: {error['category']}")

        if error['location']['segment']:
            location_parts = []
            if error['location']['line']:
                location_parts.append(f"Line {error['location']['line']}")
            if error['location']['segment']:
                location_parts.append(f"Segment {error['location']['segment']}")
            if error['location']['field']:
                location_parts.append(f"Field {error['location']['field']}")
            lines.append(f"  Location: {', '.join(location_parts)}")

            if error['location']['path']:
                lines.append(f"  Path: {error['location']['path']}")

        lines.append(f"  Description: {error['description']}")

        if error.get('value'):
            lines.append(f"  Value: '{error['value']}'")

        if error.get('expected') and error.get('actual'):
            lines.append(f"  Expected: {error['expected']}")
            lines.append(f"  Actual: {error['actual']}")

        if error.get('suggestion'):
            lines.append(f"  💡 Suggestion: {error['suggestion']}")

        return '\n'.join(lines)

    def run_validation(self, filepath, transaction_type, show_details=True):
        """
        Run validation demo with rich error details

        Args:
            filepath: Path to EDI file
            transaction_type: Transaction type (e.g., '835', '837')
            show_details: Show detailed error information

        Returns:
            int: Exit code (0 if valid, 1 if invalid)
        """
        self.logger.info(f"Validating {transaction_type} file: {filepath}")
        self.logger.info("=" * 70)

        result = edi_parser.validate_file(
            filepath=filepath,
            editype='x12',
            messagetype=f'{transaction_type}005010'
        )

        if result['valid']:
            self.logger.info("✅ File is valid!")
            self.logger.info("   No errors or warnings found.")
            return 0
        else:
            self.logger.error(f"❌ File has {result['error_count']} validation error(s)")

            if show_details and result['errors']:
                self.logger.info("\n" + "=" * 70)
                self.logger.info("DETAILED ERROR REPORT")
                self.logger.info("=" * 70)

                # Categorize errors
                errors_by_category = {}
                for error in result['errors']:
                    cat = error['category']
                    if cat not in errors_by_category:
                        errors_by_category[cat] = []
                    errors_by_category[cat].append(error)

                # Show errors by category
                for category, errors in sorted(errors_by_category.items()):
                    self.logger.info(f"\n📂 {category.replace('_', ' ').title()} ({len(errors)} error(s)):")
                    self.logger.info("-" * 70)

                    for i, error in enumerate(errors, 1):
                        self.logger.info(f"\nError {i}:")
                        self.logger.info(self.format_error_details(error))
            else:
                # Simple summary
                self.logger.info(f"\n{result['summary']}")

            return 1

    def run_parse(self, filepath, transaction_type, lenient=False, show_structure=True):
        """
        Run parsing demo with enhanced output

        Args:
            filepath: Path to EDI file
            transaction_type: Transaction type (e.g., '835', '837')
            lenient: If True, use lenient parsing mode
            show_structure: Show parsed structure summary

        Returns:
            int: Exit code (0 if success, 1 if failure)
        """
        mode = "lenient" if lenient else "strict"
        self.logger.info(f"Parsing {transaction_type} file ({mode} mode): {filepath}")
        self.logger.info("=" * 70)

        result = edi_parser.parse_file(
            filepath=filepath,
            editype='x12',
            messagetype=f'{transaction_type}005010',
            field_validation_mode='lenient' if lenient else 'strict',
            continue_on_error=lenient
        )

        if result['success']:
            self.logger.info(f"✅ Successfully parsed!")

            # Show structure summary
            if show_structure and result['data']:
                self.logger.info("\n" + "=" * 70)
                self.logger.info("PARSED STRUCTURE SUMMARY")
                self.logger.info("=" * 70)

                data = result['data']
                if 'children' in data and data['children']:
                    isa = data['children'][0]
                    self.logger.info(f"\n📦 ISA (Interchange):")
                    self.logger.info(f"   Sender: {isa.get('ISA06', '').strip()}")
                    self.logger.info(f"   Receiver: {isa.get('ISA08', '').strip()}")
                    self.logger.info(f"   Date: {isa.get('ISA09', '')}, Time: {isa.get('ISA10', '')}")
                    self.logger.info(f"   Control #: {isa.get('ISA13', '')}")

                    if '_children' in isa:
                        gs = [c for c in isa['_children'] if c.get('BOTSID') == 'GS']
                        if gs:
                            self.logger.info(f"\n📋 GS (Functional Group):")
                            self.logger.info(f"   Type: {gs[0].get('GS01', '')} Version: {gs[0].get('GS08', '')}")

                            st_list = []
                            for child in gs[0].get('_children', []):
                                if child.get('BOTSID') == 'ST':
                                    st_list.append(child)

                            if st_list:
                                self.logger.info(f"\n📄 ST (Transaction Set):")
                                self.logger.info(f"   Type: {st_list[0].get('ST01', '')}")
                                self.logger.info(f"   Control #: {st_list[0].get('ST02', '')}")

                                # Count segments
                                segment_count = len(st_list[0].get('_children', []))
                                self.logger.info(f"   Segments: {segment_count}")

                # Data size
                data_size = len(json.dumps(result['data']))
                self.logger.info(f"\n📊 Data Size: {data_size:,} characters")

            # Show warnings if any
            if result['errors']:
                self.logger.warning(f"\n⚠️  {len(result['errors'])} warning(s) logged:")
                for error in result['errors'][:3]:
                    # Parse first line of error
                    first_line = str(error).split('\n')[0]
                    self.logger.warning(f"  • {first_line}")
                if len(result['errors']) > 3:
                    self.logger.warning(f"  ... and {len(result['errors']) - 3} more")

            return 0
        else:
            self.logger.error("❌ Parse failed")
            for error in result['errors']:
                self.logger.error(f"  {error}")
            return 1

    def list_test_files(self, transaction_type):
        """List all available test files"""
        test_dir = Path(__file__).parent / 'test_files' / transaction_type

        if not test_dir.exists():
            self.logger.error(f"Test directory not found: {test_dir}")
            return 1

        files = sorted(test_dir.glob('*.dat'))

        if not files:
            self.logger.warning(f"No .dat files found in {test_dir}")
            return 0

        self.logger.info(f"Available {transaction_type} test files ({len(files)} total):")
        self.logger.info("=" * 70)
        for i, f in enumerate(files, 1):
            size = f.stat().st_size
            self.logger.info(f"  {i:2d}. {f.name:45s} ({size:>6,} bytes)")

        return 0

    def browse_and_select(self, transaction_type):
        """Interactive file browser"""
        test_dir = Path(__file__).parent / 'test_files' / transaction_type

        if not test_dir.exists():
            self.logger.error(f"Test directory not found: {test_dir}")
            return 1

        files = sorted(test_dir.glob('*.dat'))

        if not files:
            self.logger.error(f"No .dat files found in {test_dir}")
            return 1

        print(f"\n{'='*70}")
        print(f"  EDI {transaction_type} Test Files Browser")
        print(f"{'='*70}\n")

        for i, f in enumerate(files, 1):
            size = f.stat().st_size
            print(f"  {i:2d}. {f.name:45s} ({size:>6,} bytes)")

        print(f"\n{'='*70}")

        try:
            choice = input("\nEnter file number (or 'q' to quit): ").strip()

            if choice.lower() == 'q':
                return 0

            file_num = int(choice)
            if 1 <= file_num <= len(files):
                selected_file = files[file_num - 1]

                print(f"\n{'='*70}")
                print(f"  Selected: {selected_file.name}")
                print(f"{'='*70}\n")

                action = input("Action - (v)alidate, (p)arse, or (q)uit: ").strip().lower()

                if action == 'v':
                    return self.run_validation(str(selected_file), transaction_type)
                elif action == 'p':
                    lenient = input("Use lenient mode? (y/n): ").strip().lower() == 'y'
                    return self.run_parse(str(selected_file), transaction_type, lenient=lenient)
                else:
                    return 0
            else:
                print(f"Invalid choice. Please enter 1-{len(files)}")
                return 1

        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            return 1

    def run_all_files(self, transaction_type, command, lenient=False):
        """Run validation or parsing on all test files"""
        test_dir = Path(__file__).parent / 'test_files' / transaction_type

        if not test_dir.exists():
            self.logger.error(f"Test directory not found: {test_dir}")
            return 1

        files = sorted(test_dir.glob('*.dat'))

        if not files:
            self.logger.warning(f"No .dat files found in {test_dir}")
            return 0

        self.logger.info(f"Running {command} on {len(files)} {transaction_type} test files...")
        self.logger.info("=" * 70)

        results = []
        for i, filepath in enumerate(files, 1):
            self.logger.info(f"\n[{i}/{len(files)}] {filepath.name}")
            self.logger.info("-" * 70)

            if command == 'validate':
                exit_code = self.run_validation(str(filepath), transaction_type, show_details=False)
            else:  # parse
                exit_code = self.run_parse(str(filepath), transaction_type, lenient, show_structure=False)

            results.append((filepath.name, exit_code == 0))

        # Summary
        self.logger.info("\n" + "=" * 70)
        self.logger.info("SUMMARY")
        self.logger.info("=" * 70)

        passed = sum(1 for _, success in results if success)
        failed = len(results) - passed

        for filename, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            self.logger.info(f"{status} {filename}")

        self.logger.info("-" * 70)
        self.logger.info(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

        return 0 if failed == 0 else 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='EDI Parser Demo - CLI for testing parser',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file operations
  %(prog)s validate 835 test_files/835/835-all-fields.dat
  %(prog)s parse 837 test_files/837/commercial.dat --lenient
  %(prog)s --verbose validate 835 test_files/835/835-denial.dat

  # Browse and select test files interactively
  %(prog)s browse 835
  %(prog)s browse 837

  # List available test files
  %(prog)s list 835
  %(prog)s list 837

  # Run all files in a directory
  %(prog)s validate-all 835
  %(prog)s parse-all 837 --lenient
        """
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging (DEBUG level with function tracing)'
    )

    parser.add_argument(
        'command',
        choices=['validate', 'parse', 'list', 'browse', 'validate-all', 'parse-all'],
        help='Command to run'
    )

    parser.add_argument(
        'transaction_type',
        choices=['835', '837'],
        help='Transaction type (835 or 837)'
    )

    parser.add_argument(
        'filepath',
        type=str,
        nargs='?',
        help='Path to EDI file (not needed for list/browse/validate-all/parse-all)'
    )

    parser.add_argument(
        '--lenient',
        action='store_true',
        help='Use lenient parsing mode (for parse commands only)'
    )

    args = parser.parse_args()

    # Run demo
    runner = DemoRunner(verbose=args.verbose)

    # Handle different commands
    if args.command == 'list':
        return runner.list_test_files(args.transaction_type)

    elif args.command == 'browse':
        return runner.browse_and_select(args.transaction_type)

    elif args.command == 'validate-all':
        return runner.run_all_files(args.transaction_type, 'validate', lenient=False)

    elif args.command == 'parse-all':
        return runner.run_all_files(args.transaction_type, 'parse', lenient=args.lenient)

    else:  # validate or parse single file
        if not args.filepath:
            parser.error(f"{args.command} command requires filepath argument")

        # Validate file exists
        if not os.path.exists(args.filepath):
            print(f"Error: File not found: {args.filepath}", file=sys.stderr)
            return 1

        if args.command == 'validate':
            return runner.run_validation(args.filepath, args.transaction_type)
        elif args.command == 'parse':
            return runner.run_parse(args.filepath, args.transaction_type, args.lenient)


if __name__ == '__main__':
    sys.exit(main())

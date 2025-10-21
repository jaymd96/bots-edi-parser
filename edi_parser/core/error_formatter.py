"""
Error formatter for EDI validation
Converts error strings to structured, human-readable error objects
"""

import re
from typing import Dict, Any, Optional, List
from . import error_metadata


def parse_error_string(error_str: str) -> Dict[str, Any]:
    """
    Parse an error string into components

    Example input:
        "[F06]Line:5 pos:123: Record "BPR" field "BPR10" too small (min 10): "123456789"."

    Returns:
        dict with parsed components
    """
    result = {
        'code': None,
        'line': None,
        'position': None,
        'segment': None,
        'field': None,
        'record_path': None,
        'value': None,
        'raw_message': error_str,
        'params': {}
    }

    # Extract error code [F06], [S50], etc.
    code_match = re.search(r'\[([A-Z]\d+)\]', error_str)
    if code_match:
        result['code'] = code_match.group(1)

    # Extract line number
    line_match = re.search(r'[Ll]ine[:\s]+(\d+)', error_str)
    if line_match:
        result['line'] = int(line_match.group(1))

    # Extract position
    pos_match = re.search(r'pos[:\s]+(\d+)', error_str)
    if pos_match:
        result['position'] = int(pos_match.group(1))

    # Extract record/segment name - handles both quoted and unquoted
    record_match = re.search(r'[Rr]ecord[:\s]+"([^"]+)"', error_str)
    if record_match:
        record_path = record_match.group(1)
        result['record_path'] = record_path
        # Get just the last segment (e.g., "ST-BPR" -> "BPR")
        segments = record_path.split('-')
        result['segment'] = segments[-1] if segments else record_path

    # Extract field name
    field_match = re.search(r'[Ff]ield[:\s]+"([^"]+)"', error_str)
    if field_match:
        result['field'] = field_match.group(1)

    # Extract value in quotes
    value_matches = re.findall(r'"([^"]*)"', error_str)
    if value_matches:
        # The last quoted value is usually the actual field value
        result['value'] = value_matches[-1]

    # Extract specific parameters
    min_match = re.search(r'min[:\s]+(\d+)', error_str)
    if min_match:
        result['params']['min'] = int(min_match.group(1))

    max_match = re.search(r'max[:\s]+(\d+)', error_str)
    if max_match:
        result['params']['max'] = int(max_match.group(1))

    count_match = re.search(r'occurs[:\s]+(\d+)', error_str)
    if count_match:
        result['params']['count'] = int(count_match.group(1))

    return result


def create_field_path(segment: Optional[str], field: Optional[str]) -> str:
    """
    Create a field path like ST/BPR/BPR10

    Args:
        segment: Segment ID (may be path like "ST-BPR")
        field: Field ID

    Returns:
        Path string
    """
    if not segment:
        return field or ''

    # Convert segment path from "ST-BPR" to "ST/BPR"
    path_parts = segment.replace('-', '/').split('/')

    if field:
        path_parts.append(field)

    return '/'.join(path_parts)


def format_expected_vs_actual(parsed: Dict[str, Any], metadata: Dict[str, str]) -> tuple:
    """
    Generate expected vs actual strings

    Returns:
        (expected_str, actual_str)
    """
    code = parsed['code']
    params = parsed['params']
    value = parsed['value']

    expected = None
    actual = None

    if code == 'F05':  # Too big
        expected = f"{params.get('max', '?')} characters maximum"
        if value:
            actual = f"{len(value)} characters"
    elif code == 'F06':  # Too small
        expected = f"{params.get('min', '?')} characters minimum"
        if value:
            actual = f"{len(value)} characters"
    elif code in ('F07', 'F08'):  # Date/time format
        if code == 'F07':
            expected = "Valid date in YYMMDD or YYYYMMDD format"
        else:
            expected = "Valid time in HHMM or HHMMSS format"
        actual = f'"{value}"' if value else "Invalid format"
    elif code in ('F10', 'F11', 'F12'):  # Character/numeric validation
        if code == 'F10':
            expected = "Alphanumeric characters only"
        elif code == 'F11':
            expected = "Numeric characters only"
        else:
            expected = "Integer (no decimal point)"
        actual = f'"{value}"' if value else "Invalid format"
    elif code == 'S03':  # Occurs too few times
        expected = f"At least {params.get('min', '?')} occurrences"
        actual = f"{params.get('count', '?')} occurrences"
    elif code == 'S04':  # Occurs too many times
        expected = f"At most {params.get('max', '?')} occurrences"
        actual = f"{params.get('count', '?')} occurrences"
    elif code == 'F02':  # Mandatory field missing
        expected = "Required field with value"
        actual = "Missing or empty"

    return expected, actual


def enrich_error(error_str: str) -> Dict[str, Any]:
    """
    Convert an error string to a structured, enriched error object

    Args:
        error_str: Raw error string from parser

    Returns:
        Structured error dictionary with metadata
    """
    # Parse the error string
    parsed = parse_error_string(error_str)

    # Get metadata for this error code
    code = parsed['code'] or 'UNKNOWN'
    metadata = error_metadata.get_error_metadata(code)

    # Build location object
    location = {
        'line': parsed['line'],
        'position': parsed['position'],
        'segment': parsed['segment'],
        'field': parsed['field'],
        'path': create_field_path(parsed['segment'], parsed['field'])
    }

    # Generate expected vs actual
    expected, actual = format_expected_vs_actual(parsed, metadata)

    # Format description using metadata template and parsed parameters
    description = metadata['description']
    suggestion = metadata['suggestion']

    # Replace placeholders in description and suggestion
    replacements = {
        'record': parsed['segment'] or parsed['record_path'] or '?',
        'field': parsed['field'] or '?',
        'value': parsed['value'] or '?',
        'line': parsed['line'] or '?',
        'pos': parsed['position'] or '?',
        'length': len(parsed['value']) if parsed['value'] else 0,
        **parsed['params']  # min, max, count, etc.
    }

    for key, value in replacements.items():
        placeholder = '{' + key + '}'
        if placeholder in description:
            description = description.replace(placeholder, str(value))
        if placeholder in suggestion:
            suggestion = suggestion.replace(placeholder, str(value))

    # Create structured error object
    error_obj = {
        'code': code,
        'severity': metadata['severity'],
        'category': metadata['category'],
        'location': location,
        'message': parsed['raw_message'],
        'description': description,
        'expected': expected,
        'actual': actual,
        'value': parsed['value'],
        'suggestion': suggestion
    }

    return error_obj


def enrich_error_list(error_list: List[str]) -> List[Dict[str, Any]]:
    """
    Convert a list of error strings to structured error objects

    Args:
        error_list: List of raw error strings

    Returns:
        List of enriched error dictionaries
    """
    return [enrich_error(error_str) for error_str in error_list]


def format_error_summary(errors: List[Dict[str, Any]]) -> str:
    """
    Create a human-readable summary of errors

    Args:
        errors: List of structured error dictionaries

    Returns:
        Formatted summary string
    """
    if not errors:
        return "No errors found."

    summary_lines = [
        f"Found {len(errors)} validation errors:",
        ""
    ]

    # Group by severity
    critical = [e for e in errors if e['severity'] == 'critical']
    errors_list = [e for e in errors if e['severity'] == 'error']
    warnings = [e for e in errors if e['severity'] == 'warning']

    if critical:
        summary_lines.append(f"  Critical: {len(critical)}")
    if errors_list:
        summary_lines.append(f"  Errors: {len(errors_list)}")
    if warnings:
        summary_lines.append(f"  Warnings: {len(warnings)}")

    summary_lines.append("")

    # Show first few errors with details
    for i, error in enumerate(errors[:5], 1):
        summary_lines.extend([
            f"{i}. [{error['severity'].upper()}] {error['description']}",
            f"   Location: {error['location']['path']}",
            f"   Suggestion: {error['suggestion']}",
            ""
        ])

    if len(errors) > 5:
        summary_lines.append(f"... and {len(errors) - 5} more errors")

    return "\n".join(summary_lines)

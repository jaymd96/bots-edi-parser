"""
Helper functions for Foundry ontology transformations
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


def generate_claim_id(content: str) -> str:
    """
    Generate a deterministic claim ID from content hash

    Args:
        content: String content to hash (e.g., JSON representation of claim)

    Returns:
        Claim ID in format: CLM_<hash>
    """
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    return f"CLM_{hash_obj.hexdigest()[:16].upper()}"


def generate_service_id(claim_id: str, line_number: int) -> str:
    """
    Generate service ID

    Args:
        claim_id: Parent claim ID
        line_number: Service line number

    Returns:
        Service ID in format: SVC_<claim_id>_<line_number>
    """
    return f"SVC_{claim_id}_{line_number}"


def generate_diagnosis_id(claim_id: str, sequence: int) -> str:
    """
    Generate diagnosis ID

    Args:
        claim_id: Parent claim ID
        sequence: Diagnosis sequence number

    Returns:
        Diagnosis ID in format: DX_<claim_id>_<sequence>
    """
    return f"DX_{claim_id}_{sequence}"


def generate_denial_id(payment_id: str, timestamp: str, sequence: int) -> str:
    """
    Generate denial ID

    Args:
        payment_id: Payment trace number
        timestamp: ISO timestamp
        sequence: Sequence number within payment

    Returns:
        Denial ID in format: DNL_<payment_id>_<timestamp>_<seq>
    """
    # Simplify timestamp for ID (remove special chars)
    simple_ts = timestamp.replace('-', '').replace(':', '').replace('T', '').replace('.', '')[:14]
    return f"DNL_{payment_id}_{simple_ts}_{sequence}"


def format_edi_date(edi_date: Optional[str]) -> Optional[str]:
    """
    Convert EDI date format (YYYYMMDD or CCYYMMDD) to ISO date (YYYY-MM-DD)

    Args:
        edi_date: Date in EDI format (YYYYMMDD or CCYYMMDD)

    Returns:
        Date in ISO format (YYYY-MM-DD) or None if invalid
    """
    if not edi_date or len(edi_date) < 8:
        return None

    # Handle both YYYYMMDD and CCYYMMDD formats
    date_str = edi_date[-8:] if len(edi_date) > 8 else edi_date

    try:
        year = date_str[0:4]
        month = date_str[4:6]
        day = date_str[6:8]

        # Validate
        datetime(int(year), int(month), int(day))

        return f"{year}-{month}-{day}"
    except (ValueError, IndexError):
        return None


def current_timestamp() -> str:
    """
    Get current timestamp in ISO format

    Returns:
        ISO timestamp string
    """
    return datetime.utcnow().isoformat() + 'Z'


def add_days_to_date(iso_date: Optional[str], days: int) -> Optional[str]:
    """
    Add days to an ISO date

    Args:
        iso_date: Date in ISO format (YYYY-MM-DD)
        days: Number of days to add

    Returns:
        New date in ISO format or None if invalid
    """
    if not iso_date:
        return None

    try:
        date_obj = datetime.fromisoformat(iso_date)
        new_date = date_obj + timedelta(days=days)
        return new_date.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def validate_npi(npi: Optional[str]) -> bool:
    """
    Validate NPI format (10 digits)

    Args:
        npi: NPI string

    Returns:
        True if valid NPI format
    """
    if not npi:
        return False
    return len(npi) == 10 and npi.isdigit()


def safe_int(value: Any) -> Optional[int]:
    """
    Safely convert value to int

    Args:
        value: Value to convert

    Returns:
        Integer value or None if conversion fails
    """
    if value is None or value == '':
        return None

    try:
        # Handle strings with decimals
        if isinstance(value, str) and '.' in value:
            return int(float(value))
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_float(value: Any) -> Optional[float]:
    """
    Safely convert value to float

    Args:
        value: Value to convert

    Returns:
        Float value or None if conversion fails
    """
    if value is None or value == '':
        return None

    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_bool(value: Any) -> bool:
    """
    Safely convert value to bool

    Args:
        value: Value to convert

    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', 'yes', '1', 'y')
    return bool(value)


def join_strings(values: list, separator: str = ',') -> str:
    """
    Join list of strings with separator, filtering out None/empty values

    Args:
        values: List of string values
        separator: Separator string

    Returns:
        Joined string
    """
    if not values:
        return ''

    filtered = [str(v) for v in values if v is not None and v != '']
    return separator.join(filtered)


def find_segment(data: Dict[str, Any], segment_id: str, qualifier: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    Find first segment by ID and optional qualifier fields

    Args:
        data: Parsed EDI JSON
        segment_id: Segment ID (e.g., 'CLM', 'NM1')
        qualifier: Optional dict of field qualifiers (e.g., {'NM101': '85'})

    Returns:
        First matching segment or None
    """
    if isinstance(data, dict):
        # Check if this is the segment
        if data.get('BOTSID') == segment_id:
            # Check qualifiers if provided
            if qualifier:
                for key, value in qualifier.items():
                    if data.get(key) != value:
                        return None
            return data

        # Recursively search children
        for key in ['_children', 'children']:
            if key in data and isinstance(data[key], list):
                for child in data[key]:
                    result = find_segment(child, segment_id, qualifier)
                    if result:
                        return result

    return None


def find_all_segments(data: Dict[str, Any], segment_id: str, qualifier: Optional[Dict[str, str]] = None) -> list:
    """
    Find all segments by ID and optional qualifier fields

    Args:
        data: Parsed EDI JSON
        segment_id: Segment ID (e.g., 'SV1', 'CAS')
        qualifier: Optional dict of field qualifiers

    Returns:
        List of matching segments
    """
    results = []

    def search(node):
        if isinstance(node, dict):
            # Check if this is a matching segment
            if node.get('BOTSID') == segment_id:
                # Check qualifiers if provided
                if qualifier:
                    match = all(node.get(k) == v for k, v in qualifier.items())
                    if match:
                        results.append(node)
                else:
                    results.append(node)

            # Recursively search children
            for key in ['_children', 'children']:
                if key in node and isinstance(node[key], list):
                    for child in node[key]:
                        search(child)

    search(data)
    return results

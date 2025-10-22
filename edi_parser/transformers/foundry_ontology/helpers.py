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


def generate_object_id() -> str:
    """
    Generate a MongoDB-style object ID (24 hex characters)

    Returns:
        Object ID string
    """
    import time
    import random

    # Timestamp (4 bytes)
    timestamp = int(time.time()).to_bytes(4, 'big')
    # Random (5 bytes)
    random_bytes = random.getrandbits(40).to_bytes(5, 'big')
    # Counter (3 bytes)
    counter = random.getrandbits(24).to_bytes(3, 'big')

    return (timestamp + random_bytes + counter).hex()


def create_code_object(
    subtype: str,
    code: str,
    desc: Optional[str] = None,
    formatted_code: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized code object

    Args:
        subtype: Code subtype (e.g., 'CARC', 'ICD_10', 'CPT', 'NDC')
        code: Code value
        desc: Code description (optional)
        formatted_code: Formatted version of code (optional)
        **kwargs: Additional fields to include

    Returns:
        Code object dict
    """
    obj = {
        'subType': subtype,
        'code': code
    }

    if desc:
        obj['desc'] = desc

    if formatted_code:
        obj['formattedCode'] = formatted_code

    # Add any additional fields
    obj.update(kwargs)

    return obj


def create_entity_object(
    entity_role: str,
    entity_type: str,
    identification_type: Optional[str] = None,
    identifier: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized entity/person object

    Args:
        entity_role: Entity role (e.g., 'PAYER', 'SUBSCRIBER', 'BILLING_PROVIDER')
        entity_type: Entity type ('INDIVIDUAL' or 'BUSINESS')
        identification_type: ID type (e.g., 'NPI', 'MEMBER_ID', 'PAYOR_ID')
        identifier: Identifier value
        **kwargs: Additional fields (firstName, lastName, address, etc.)

    Returns:
        Entity object dict
    """
    obj = {
        'entityRole': entity_role,
        'entityType': entity_type
    }

    if identification_type:
        obj['identificationType'] = identification_type

    if identifier:
        obj['identifier'] = identifier

    # Add any additional fields
    obj.update(kwargs)

    return obj


def format_icd10_code(code: str) -> str:
    """
    Format ICD-10 code with decimal separator

    Examples:
        J0300 -> J03.00
        Z1159 -> Z11.59

    Args:
        code: Unformatted ICD-10 code

    Returns:
        Formatted code with decimal
    """
    if not code or len(code) < 4:
        return code

    # ICD-10 format: category (3 chars) + subcategory (decimal)
    # Example: J03.00
    category = code[:3]
    subcategory = code[3:]

    if subcategory:
        return f"{category}.{subcategory}"

    return code


def format_ndc_code(code: str) -> str:
    """
    Format NDC (National Drug Code) with dashes

    Examples:
        00002143481 -> 0002-1434-81

    Args:
        code: Unformatted 11-digit NDC code

    Returns:
        Formatted NDC code
    """
    if not code or len(code) != 11:
        return code

    # NDC format: labeler (4-5 digits) - product (3-4 digits) - package (1-2 digits)
    # Most common: 5-4-2 format
    return f"{code[:4]}-{code[4:8]}-{code[8:]}"


def lookup_carc_description(code: str) -> str:
    """
    Lookup CARC (Claim Adjustment Reason Code) description

    Args:
        code: CARC code

    Returns:
        Description string
    """
    # Common CARC codes - in production this would be a full database lookup
    carc_codes = {
        '1': 'Deductible Amount',
        '2': 'Coinsurance Amount',
        '3': 'Co-payment Amount',
        '4': 'The procedure code is inconsistent with the modifier used',
        '20': 'This injury/illness is covered by the liability carrier.',
        '22': 'This care may be covered by another payer per coordination of benefits.',
        '26': 'Expenses incurred prior to coverage.',
        '45': 'Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement.',
        '70': 'Cost outlier - Adjustment to compensate for additional costs.',
        '75': 'Direct Medical Education Adjustment.',
        '90': 'Ingredient cost adjustment. Usage: To be used for pharmaceuticals only.',
        '102': 'Major Medical Adjustment.',
        '131': 'Claim specific negotiated discount.',
        '132': 'Prearranged demonstration project adjustment.',
        '197': 'Precertification/authorization/notification/pre-treatment absent.'
    }

    return carc_codes.get(code, f'Reason Code {code}')


def lookup_rarc_description(code: str) -> str:
    """
    Lookup RARC (Remittance Advice Remark Code) description

    Args:
        code: RARC code

    Returns:
        Description string
    """
    # Common RARC codes
    rarc_codes = {
        'M1': "X-ray not taken within the past 12 months or near enough to the start of treatment.",
        'M2': "Not paid separately when the patient is an inpatient.",
        'MA01': "If you do not agree with what we approved for these services, you may appeal our decision. To make sure that we are fair to you, we require another individual that did not process your initial claim to conduct the appeal. However, in order to be eligible for an appeal, you must write to us within 120 days of the date you received this notice, unless you have a good reason for being late.",
        'MA07': "The claim information has also been forwarded to Medicaid for review."
    }

    return rarc_codes.get(code, f'Remark Code {code}')


def lookup_place_of_service(code: str) -> str:
    """
    Lookup place of service description

    Args:
        code: Place of service code

    Returns:
        Description string
    """
    pos_codes = {
        '11': 'OFFICE',
        '21': 'INPATIENT',
        '22': 'OUTPATIENT',
        '23': 'EMERGENCY_ROOM'
    }

    return pos_codes.get(code, 'UNKNOWN')


def lookup_frequency_description(code: str) -> str:
    """
    Lookup claim frequency code description

    Args:
        code: Frequency code

    Returns:
        Description string
    """
    freq_codes = {
        '1': 'Original claim',
        '6': 'Corrected claim',
        '7': 'Replacement claim',
        '8': 'Void claim'
    }

    return freq_codes.get(code, f'Frequency {code}')

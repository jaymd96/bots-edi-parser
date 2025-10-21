"""
835 Electronic Remittance Advice Transformer

Transforms parsed 835 EDI JSON into Palantir Foundry ontology schemas.
"""

import json
from typing import Dict, List, Any, Optional

from .helpers import (
    generate_denial_id,
    format_edi_date,
    current_timestamp,
    add_days_to_date,
    safe_int,
    safe_float,
    join_strings,
    find_segment,
    find_all_segments,
)


# Reason code to typical action mapping
REASON_CODE_ACTIONS = {
    range(1, 16): "Verify eligibility and resubmit",
    range(16, 50): "Correct billing information",
    range(50, 100): "Provide medical records",
    range(100, 150): "Obtain authorization",
    range(150, 200): "Review coding",
    197: "Obtain prior authorization",
}


def get_typical_action(reason_code: int) -> str:
    """Get typical action for a reason code"""
    if reason_code == 197:
        return "Obtain prior authorization"

    for code_range, action in REASON_CODE_ACTIONS.items():
        if isinstance(code_range, range) and reason_code in code_range:
            return action

    return "Manual review required"


def transform_835(
    parsed_json: Dict[str, Any],
    payer_metadata: Optional[Dict[str, Any]] = None,
    claim_index: Optional[Dict[str, str]] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform 835 parsed EDI JSON to Foundry ontology schemas

    Args:
        parsed_json: Parsed 835 EDI JSON (with human-readable names applied)
        payer_metadata: Optional payer name to payer_id mapping
        claim_index: Optional mapping of client_claim_id to claim_id

    Returns:
        Dict with keys: denials, reason_codes
    """
    payer_metadata = payer_metadata or {}
    claim_index = claim_index or {}

    # Results
    denials = []
    reason_codes = {}  # Dict to track unique reason codes

    # Extract payment header info
    bpr = find_segment(parsed_json, 'BPR')
    trn = find_segment(parsed_json, 'TRN')

    if not bpr or not trn:
        # Missing required segments
        return {'denials': [], 'reason_codes': []}

    payment_id = trn.get('TRN02', '')
    payment_date_raw = bpr.get('BPR16', '')
    payment_date = format_edi_date(payment_date_raw)
    total_payment = safe_float(bpr.get('BPR02', ''))

    # Find all claim payment loops (CLP segments)
    clp_segments = find_all_segments(parsed_json, 'CLP')

    denial_sequence = 1

    for clp in clp_segments:
        # Extract claim payment info
        client_claim_id = clp.get('CLP01', '')
        claim_status = clp.get('CLP02', '')
        claim_charge = safe_float(clp.get('CLP03', ''))
        claim_payment = safe_float(clp.get('CLP04', ''))
        payer_claim_number = clp.get('CLP07', '')

        # Look up claim_id from index
        claim_id = claim_index.get(client_claim_id, '')

        # Extract all CAS (Claim Adjustment) segments for this claim
        cas_segments = find_all_segments(clp, 'CAS')

        for cas in cas_segments:
            # Extract denial records from CAS segment
            denial_records = extract_denials_from_cas(
                cas,
                payment_id,
                payment_date,
                claim_id,
                client_claim_id,
                denial_sequence,
                reason_codes
            )

            denials.extend(denial_records)
            denial_sequence += len(denial_records)

        # Also check service-level adjustments (SVC/CAS)
        svc_segments = find_all_segments(clp, 'SVC')
        for svc in svc_segments:
            svc_cas_segments = find_all_segments(svc, 'CAS')
            for cas in svc_cas_segments:
                denial_records = extract_denials_from_cas(
                    cas,
                    payment_id,
                    payment_date,
                    claim_id,
                    client_claim_id,
                    denial_sequence,
                    reason_codes
                )

                denials.extend(denial_records)
                denial_sequence += len(denial_records)

    # Convert reason_codes dict to list
    reason_code_list = [
        {
            'reason_code': code,
            'description': data['description'],
            'typical_action': data['typical_action']
        }
        for code, data in reason_codes.items()
    ]

    return {
        'denials': denials,
        'reason_codes': reason_code_list
    }


def extract_denials_from_cas(
    cas_segment: Dict[str, Any],
    payment_id: str,
    payment_date: Optional[str],
    claim_id: str,
    client_claim_id: str,
    sequence_start: int,
    reason_codes: Dict[int, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Extract denial records from a CAS segment

    CAS segment structure:
    CAS01 - Claim Adjustment Group Code (CO, PR, OA, PI, CR)
    CAS02 - Reason Code 1
    CAS03 - Amount 1
    CAS04 - Quantity 1 (optional)
    CAS05 - Reason Code 2
    CAS06 - Amount 2
    ...up to CAS19

    Returns list of denial records (one per CAS segment typically)
    """
    denials = []

    # Extract denial type
    group_code = cas_segment.get('CAS01', '')
    denial_type_map = {
        'CO': 'Contractual Obligation',
        'PR': 'Patient Responsibility',
        'OA': 'Other Adjustment',
        'PI': 'Payer Initiated',
        'CR': 'Correction/Reversal'
    }
    denial_type = denial_type_map.get(group_code, group_code)

    # Extract all reason codes and amounts from the CAS segment
    all_reason_codes = []
    total_denied = 0.0
    primary_reason_code = None

    # CAS has up to 6 adjustment triplets (reason, amount, quantity)
    for i in range(1, 7):
        reason_field = f'CAS{i*3-1:02d}'  # CAS02, CAS05, CAS08, CAS11, CAS14, CAS17
        amount_field = f'CAS{i*3:02d}'     # CAS03, CAS06, CAS09, CAS12, CAS15, CAS18

        reason_code_str = cas_segment.get(reason_field, '')
        amount_str = cas_segment.get(amount_field, '')

        if not reason_code_str:
            break

        reason_code = safe_int(reason_code_str)
        amount = safe_float(amount_str) or 0.0

        if reason_code:
            all_reason_codes.append(reason_code)
            total_denied += amount

            # First reason code is primary
            if primary_reason_code is None:
                primary_reason_code = reason_code

            # Track reason code for reference
            if reason_code not in reason_codes:
                reason_codes[reason_code] = {
                    'description': f'Reason Code {reason_code}',  # Would lookup from CARC database
                    'typical_action': get_typical_action(reason_code)
                }

    if not primary_reason_code:
        return []  # No valid adjustments

    # Generate denial ID
    timestamp = current_timestamp()
    denial_id = generate_denial_id(payment_id, timestamp, sequence_start)

    # Calculate appeal deadline (30 days from payment date)
    appeal_deadline = add_days_to_date(payment_date, 30) if payment_date else None

    # Create title
    title = f"{denial_type} - Reason {primary_reason_code}"

    denial = {
        'denial_id': denial_id,
        'created_at': timestamp,
        'title': title,
        'client_id': '',  # To be populated from context
        'claim_id': claim_id,
        'payment_id': payment_id,
        'contract_id': '',  # Not available in 835
        'denial_type': denial_type,
        'primary_reason_code': primary_reason_code,
        'all_reason_codes': join_strings([str(c) for c in all_reason_codes]),
        'total_denied': total_denied,
        'expected_allowed': None,  # Would need to be calculated
        'contractual_variance': None,  # Would need to be calculated
        'denial_date': payment_date,
        'appeal_deadline': appeal_deadline,
        'client_notified_date': None  # To be populated by workflow
    }

    denials.append(denial)

    return denials


def extract_payer_from_835(parsed_json: Dict[str, Any], payer_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract payer information from 835"""

    # Find N1 segment with N101='PR' (Payer)
    n1_segments = find_all_segments(parsed_json, 'N1')

    for n1 in n1_segments:
        if n1.get('N101') == 'PR':
            payer_name = n1.get('N102', '')
            payer_id_from_edi = n1.get('N104', '')  # N103=qualifier, N104=ID

            # Look up in metadata
            payer_id = payer_id_from_edi
            for pid, pdata in payer_metadata.items():
                if pdata.get('name', '').upper() == payer_name.upper():
                    payer_id = pid
                    break

            if not payer_id:
                payer_id = payer_name

            payer = {
                'payer_id': payer_id,
                'payer_name': payer_name,
                'edi_endpoint': '',
                'remittance_format': 1,  # 835 format
                'active': True
            }

            return payer

    return None

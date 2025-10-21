"""
837P Professional Claims Transformer

Transforms parsed 837P EDI JSON into Palantir Foundry ontology schemas.
"""

import hashlib
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .helpers import (
    generate_claim_id,
    generate_service_id,
    generate_diagnosis_id,
    format_edi_date,
    current_timestamp,
    validate_npi,
    safe_int,
    safe_float,
    safe_bool,
    join_strings,
    find_segment,
    find_all_segments,
)


def transform_837p(
    parsed_json: Dict[str, Any],
    provider_metadata: Optional[Dict[str, Any]] = None,
    payer_metadata: Optional[Dict[str, Any]] = None,
    source_filename: str = ''
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Transform 837P parsed EDI JSON to Foundry ontology schemas

    Args:
        parsed_json: Parsed 837P EDI JSON (with human-readable names applied)
        provider_metadata: Optional provider NPI to provider_id mapping
        payer_metadata: Optional payer name to payer_id mapping
        source_filename: Source EDI filename

    Returns:
        Dict with keys: claims, services, diagnoses, providers, payers
    """
    provider_metadata = provider_metadata or {}
    payer_metadata = payer_metadata or {}

    # Results
    claims = []
    services = []
    diagnoses = []
    providers = []
    payers = []

    # Track unique providers and payers
    seen_providers = set()
    seen_payers = set()

    # Extract submission metadata
    isa = find_segment(parsed_json, 'ISA')
    gs = find_segment(parsed_json, 'GS')
    st = find_segment(parsed_json, 'ST')

    submission_batch = st.get('ST02', '') if st else ''
    submitted_at = current_timestamp()

    # Find all claim loops (2300 level CLM segments)
    clm_segments = find_all_segments(parsed_json, 'CLM')

    for clm in clm_segments:
        # Extract claim data
        claim = extract_claim(
            clm,
            submission_batch,
            submitted_at,
            source_filename,
            provider_metadata,
            payer_metadata
        )

        if claim:
            claims.append(claim)
            claim_id = claim['claim_id']

            # Extract services for this claim
            claim_services = extract_services(clm, claim_id)
            services.extend(claim_services)

            # Extract diagnoses for this claim
            claim_diagnoses = extract_diagnoses(clm, claim_id)
            diagnoses.extend(claim_diagnoses)

            # Extract providers for this claim
            billing_provider = extract_billing_provider(clm, claim_id, provider_metadata)
            if billing_provider and billing_provider['provider_id'] not in seen_providers:
                providers.append(billing_provider)
                seen_providers.add(billing_provider['provider_id'])

            rendering_provider = extract_rendering_provider(clm, claim_id, provider_metadata)
            if rendering_provider and rendering_provider['provider_id'] not in seen_providers:
                providers.append(rendering_provider)
                seen_providers.add(rendering_provider['provider_id'])

            # Extract payer
            payer = extract_payer(clm, payer_metadata)
            if payer and payer['payer_id'] not in seen_payers:
                payers.append(payer)
                seen_payers.add(payer['payer_id'])

    return {
        'claims': claims,
        'services': services,
        'diagnoses': diagnoses,
        'providers': providers,
        'payers': payers
    }


def extract_claim(
    clm_segment: Dict[str, Any],
    submission_batch: str,
    submitted_at: str,
    source_filename: str,
    provider_metadata: Dict[str, Any],
    payer_metadata: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Extract claim object from CLM segment and children"""

    # Generate claim ID from content hash
    content_str = json.dumps(clm_segment, sort_keys=True)
    claim_id = generate_claim_id(content_str)

    # Extract basic claim data
    client_claim_id = clm_segment.get('CLM01', '')
    total_charge = safe_int(clm_segment.get('CLM02', ''))

    # CLM05 composite field - place of service and claim frequency
    # Format: CLM05-1:place, CLM05-2:frequency, CLM05-3:provider signature
    place_of_service = safe_int(clm_segment.get('CLM05.01') or clm_segment.get('CLM0501'))
    claim_frequency = safe_int(clm_segment.get('CLM05.02') or clm_segment.get('CLM0502') or '1')

    # Extract statement dates from DTP segments
    statement_from_date = None
    statement_to_date = None

    dtp_segments = find_all_segments(clm_segment, 'DTP')
    for dtp in dtp_segments:
        qualifier = dtp.get('DTP01')
        if qualifier == '434':  # Statement dates
            date_value = dtp.get('DTP03', '')
            if dtp.get('DTP02') == 'RD8':  # Date range
                # Format: CCYYMMDD-CCYYMMDD
                if '-' in date_value:
                    from_date, to_date = date_value.split('-', 1)
                    statement_from_date = format_edi_date(from_date)
                    statement_to_date = format_edi_date(to_date)
            else:
                # Single date
                statement_from_date = format_edi_date(date_value)
                statement_to_date = statement_from_date

    # Extract patient info from subscriber/patient loops
    patient_first_name, patient_last_name, patient_mrn, subscriber_id = extract_patient_info(clm_segment)

    # Extract provider IDs
    billing_provider_id = extract_billing_provider_id(clm_segment, provider_metadata)
    rendering_provider_id = extract_rendering_provider_id(clm_segment, provider_metadata)

    # Extract payer ID
    payer_id = extract_payer_id(clm_segment, payer_metadata)

    # Create title
    title = f"Claim {patient_last_name or 'Unknown'} - {statement_from_date or 'No Date'}"

    claim = {
        'claim_id': claim_id,
        'submitted_at': submitted_at,
        'title': title,
        'client_claim_id': client_claim_id,
        'client_id': '',  # To be populated from provider metadata or context
        'billing_provider_id': billing_provider_id,
        'rendering_provider_id': rendering_provider_id,
        'subscriber_id': subscriber_id,
        'payer_id': payer_id,
        'patient_first_name': patient_first_name,
        'patient_last_name': patient_last_name,
        'speciality': '',  # To be populated from taxonomy code
        'patient_mrn': patient_mrn,
        'total_charge': total_charge,
        'place_of_service': place_of_service,
        'claim_frequency': claim_frequency,
        'statement_from_date': statement_from_date,
        'statement_to_date': statement_to_date,
        'submission_batch': submission_batch,
        'source_file': source_filename
    }

    return claim


def extract_patient_info(clm_segment: Dict[str, Any]) -> tuple:
    """Extract patient information from NM1 segments"""

    patient_first_name = ''
    patient_last_name = ''
    patient_mrn = ''
    subscriber_id = ''

    # Find subscriber loop (2010BA NM101=IL)
    nm1_segments = find_all_segments(clm_segment, 'NM1')

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101')

        # Subscriber
        if entity_id == 'IL':
            subscriber_id = nm1.get('NM109', '')
            # If patient is also subscriber
            if nm1.get('NM102') == '1':  # Person
                patient_last_name = nm1.get('NM103', '')
                patient_first_name = nm1.get('NM104', '')

            # Look for REF segment for MRN
            ref_segments = find_all_segments(nm1, 'REF')
            for ref in ref_segments:
                if ref.get('REF01') == 'EA':  # Medical Record Number
                    patient_mrn = ref.get('REF02', '')

        # Patient (if different from subscriber) (2010CA NM101=QC)
        elif entity_id == 'QC':
            patient_last_name = nm1.get('NM103', '')
            patient_first_name = nm1.get('NM104', '')

            # Look for REF segment for MRN
            ref_segments = find_all_segments(nm1, 'REF')
            for ref in ref_segments:
                if ref.get('REF01') == 'EA':
                    patient_mrn = ref.get('REF02', '')

    return patient_first_name, patient_last_name, patient_mrn, subscriber_id


def extract_billing_provider_id(clm_segment: Dict[str, Any], provider_metadata: Dict[str, Any]) -> str:
    """Extract billing provider ID"""
    # Find NM1 segment with NM101='85' (Billing Provider)
    nm1_segments = find_all_segments(clm_segment, 'NM1')

    for nm1 in nm1_segments:
        if nm1.get('NM101') == '85':
            npi = nm1.get('NM109', '')
            if npi and validate_npi(npi):
                # Look up in metadata or use NPI
                return provider_metadata.get(npi, npi)

    return ''


def extract_rendering_provider_id(clm_segment: Dict[str, Any], provider_metadata: Dict[str, Any]) -> str:
    """Extract rendering provider ID"""
    # Find NM1 segment with NM101='82' (Rendering Provider)
    nm1_segments = find_all_segments(clm_segment, 'NM1')

    for nm1 in nm1_segments:
        if nm1.get('NM101') == '82':
            npi = nm1.get('NM109', '')
            if npi and validate_npi(npi):
                return provider_metadata.get(npi, npi)

    return ''


def extract_payer_id(clm_segment: Dict[str, Any], payer_metadata: Dict[str, Any]) -> str:
    """Extract payer ID"""
    # Find NM1 segment with NM101='PR' (Payer)
    nm1_segments = find_all_segments(clm_segment, 'NM1')

    for nm1 in nm1_segments:
        if nm1.get('NM101') == 'PR':
            payer_name = nm1.get('NM103', '')
            payer_id_from_edi = nm1.get('NM109', '')

            # Look up in metadata by name
            for pid, pdata in payer_metadata.items():
                if pdata.get('name', '').upper() == payer_name.upper():
                    return pid

            # Fallback to EDI ID
            return payer_id_from_edi or payer_name

    return ''


def extract_services(clm_segment: Dict[str, Any], claim_id: str) -> List[Dict[str, Any]]:
    """Extract service line items from SV1 segments"""

    services = []

    # Find all service line loops (loop 2400)
    # Look for LX segments which mark service lines
    children = clm_segment.get('_children', [])

    for child in children:
        if child.get('BOTSID') == 'LX':
            line_number = safe_int(child.get('LX01', '0'))

            # Find SV1 segment under this LX
            sv1 = find_segment(child, 'SV1')
            if not sv1:
                continue

            # Extract service data
            service_id = generate_service_id(claim_id, line_number)

            # SV101 is composite: procedure code and modifiers
            procedure_code = sv1.get('SV101.02') or sv1.get('SV10102', '')

            # Modifiers are SV101-3 through SV101-6
            modifiers_list = [
                sv1.get('SV101.03') or sv1.get('SV10103', ''),
                sv1.get('SV101.04') or sv1.get('SV10104', ''),
                sv1.get('SV101.05') or sv1.get('SV10105', ''),
                sv1.get('SV101.06') or sv1.get('SV10106', '')
            ]
            modifiers = join_strings([m for m in modifiers_list if m])

            charge_amount = safe_float(sv1.get('SV102', ''))
            units = safe_float(sv1.get('SV104', ''))

            # Diagnosis pointers SV107
            diagnosis_pointers = sv1.get('SV107', '')

            # Service date from DTP segment
            service_date = ''
            dtp_segments = find_all_segments(child, 'DTP')
            for dtp in dtp_segments:
                if dtp.get('DTP01') == '472':  # Service date
                    service_date = format_edi_date(dtp.get('DTP03', ''))
                    break

            # Create title (procedure code description would come from lookup)
            title = f"Service Line {line_number} - {procedure_code}"

            service = {
                'service_id': service_id,
                'claim_id': claim_id,
                'line_number': line_number,
                'procedure_code': procedure_code,
                'modifiers': modifiers,
                'charge_amount': charge_amount,
                'units': units,
                'service_date': service_date,
                'diagnosis_pointers': diagnosis_pointers,
                'title': title
            }

            services.append(service)

    return services


def extract_diagnoses(clm_segment: Dict[str, Any], claim_id: str) -> List[Dict[str, Any]]:
    """Extract diagnosis codes from HI segments"""

    diagnoses = []

    # Find HI segments (Health Care Diagnosis Code)
    hi_segments = find_all_segments(clm_segment, 'HI')

    sequence = 1
    for hi in hi_segments:
        # HI segment can have up to 12 composite fields (HI01 through HI12)
        # Each composite has qualifier and code: HI01-1 (qualifier), HI01-2 (code)
        for i in range(1, 13):
            field_base = f'HI{i:02d}'

            # Try both formats: HI01.01 and HI0101
            qualifier = hi.get(f'{field_base}.01') or hi.get(f'{field_base}01', '')
            code = hi.get(f'{field_base}.02') or hi.get(f'{field_base}02', '')

            if not code:
                continue

            diagnosis_id = generate_diagnosis_id(claim_id, sequence)

            # Determine diagnosis type from qualifier
            diagnosis_type = ''
            if qualifier in ['ABK', 'BK']:
                diagnosis_type = 'Principal'
            elif qualifier in ['ABF', 'BF']:
                diagnosis_type = 'Secondary'
            elif qualifier == 'ABN':
                diagnosis_type = 'Admitting'
            else:
                diagnosis_type = 'Other'

            # Title would come from ICD-10 lookup
            title = f"{diagnosis_type} Diagnosis - {code}"

            diagnosis = {
                'diagnosis_id': diagnosis_id,
                'claim_id': claim_id,
                'sequence': sequence,
                'diagnosis_code': code,
                'diagnosis_type': diagnosis_type,
                'title': title,
                'cpt_code': '',  # Not applicable for diagnosis
                'hcpcs_code': ''  # Not applicable for diagnosis
            }

            diagnoses.append(diagnosis)
            sequence += 1

    return diagnoses


def extract_billing_provider(
    clm_segment: Dict[str, Any],
    claim_id: str,
    provider_metadata: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Extract billing provider object"""

    nm1_segments = find_all_segments(clm_segment, 'NM1')

    for nm1 in nm1_segments:
        if nm1.get('NM101') == '85':  # Billing Provider
            npi = nm1.get('NM109', '')

            if not npi or not validate_npi(npi):
                continue

            # Get provider_id from metadata or use NPI
            provider_id = provider_metadata.get(npi, npi)

            # Extract provider details
            entity_type = nm1.get('NM102')  # 1=Person, 2=Organization
            organization_name = ''
            first_name = ''
            last_name = ''

            if entity_type == '2':  # Organization
                organization_name = nm1.get('NM103', '')
            else:  # Person
                last_name = nm1.get('NM103', '')
                first_name = nm1.get('NM104', '')

            # Extract address from N3/N4 segments
            address = ''
            city = ''
            state = ''
            zip_code = None

            n3 = find_segment(nm1, 'N3')
            if n3:
                address = n3.get('N301', '')

            n4 = find_segment(nm1, 'N4')
            if n4:
                city = n4.get('N401', '')
                state = n4.get('N402', '')
                zip_code = safe_int(n4.get('N403', ''))

            # Extract taxonomy from PRV segment
            taxonomy_code = ''
            prv = find_segment(nm1, 'PRV')
            if prv:
                taxonomy_code = prv.get('PRV03', '')

            provider = {
                'provider_id': provider_id,
                'client_id': '',  # To be populated from context
                'npi': npi,
                'provider_type': 'Billing Provider',
                'organization_name': organization_name,
                'first_name': first_name,
                'last_name': last_name,
                'taxonomy_code': taxonomy_code,
                'address': address,
                'city': city,
                'state': state,
                'zip': zip_code,
                'active': True
            }

            return provider

    return None


def extract_rendering_provider(
    clm_segment: Dict[str, Any],
    claim_id: str,
    provider_metadata: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Extract rendering provider object"""

    nm1_segments = find_all_segments(clm_segment, 'NM1')

    for nm1 in nm1_segments:
        if nm1.get('NM101') == '82':  # Rendering Provider
            npi = nm1.get('NM109', '')

            if not npi or not validate_npi(npi):
                continue

            provider_id = provider_metadata.get(npi, npi)

            # Extract provider details
            entity_type = nm1.get('NM102')
            organization_name = ''
            first_name = ''
            last_name = ''

            if entity_type == '2':
                organization_name = nm1.get('NM103', '')
            else:
                last_name = nm1.get('NM103', '')
                first_name = nm1.get('NM104', '')

            # Extract taxonomy
            taxonomy_code = ''
            prv = find_segment(nm1, 'PRV')
            if prv:
                taxonomy_code = prv.get('PRV03', '')

            provider = {
                'provider_id': provider_id,
                'client_id': '',
                'npi': npi,
                'provider_type': 'Rendering Provider',
                'organization_name': organization_name,
                'first_name': first_name,
                'last_name': last_name,
                'taxonomy_code': taxonomy_code,
                'address': '',  # Usually not included for rendering provider
                'city': '',
                'state': '',
                'zip': None,
                'active': True
            }

            return provider

    return None


def extract_payer(clm_segment: Dict[str, Any], payer_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract payer object"""

    nm1_segments = find_all_segments(clm_segment, 'NM1')

    for nm1 in nm1_segments:
        if nm1.get('NM101') == 'PR':  # Payer
            payer_name = nm1.get('NM103', '')
            payer_id_from_edi = nm1.get('NM109', '')

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
                'edi_endpoint': '',  # Not in 837P
                'remittance_format': 1,  # Assume 835
                'active': True
            }

            return payer

    return None

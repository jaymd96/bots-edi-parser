"""
837P Professional Claims Transformer

Transforms parsed 837P EDI JSON into structured ontology schemas.
Outputs a single comprehensive CLAIM object matching the target schema.
"""

import json
from typing import Dict, List, Any, Optional

from .helpers import (
    generate_object_id,
    format_edi_date,
    safe_int,
    safe_float,
    find_segment,
    find_all_segments,
    create_code_object,
    create_entity_object,
    lookup_carc_description,
    lookup_place_of_service,
    lookup_frequency_description,
    format_icd10_code,
    format_ndc_code,
)


# Group code to adjustment group mapping
GROUP_CODE_MAP = {
    'CO': 'CONTRACTUAL',
    'PR': 'PATIENT_RESPONSIBILITY',
    'OA': 'OTHER',
    'PI': 'PAYOR_INITIATED',
    'CR': 'CORRECTION'
}


def transform_837p(
    parsed_json: Dict[str, Any],
    source_filename: str = ''
) -> List[Dict[str, Any]]:
    """
    Transform 837P parsed EDI JSON to structured CLAIM ontology schema

    Args:
        parsed_json: Parsed 837P EDI JSON (with human-readable names applied)
        source_filename: Source EDI filename

    Returns:
        List containing single CLAIM object
    """
    # Extract transaction-level info first
    transaction = extract_transaction(parsed_json, source_filename)

    # Find all claim loops (CLM segments)
    clm_segments = find_all_segments(parsed_json, 'CLM')

    if not clm_segments:
        return []

    # For now, process first CLM (in production might process all)
    # Target schema shows single claim object
    clm = clm_segments[0]

    # Find the parent hierarchical level (HL) to get subscriber/patient context
    # In 837P, CLM is within a 2300 loop under a subscriber (2000B) HL loop
    claim = extract_claim(clm, parsed_json, transaction)

    return [claim]


def extract_transaction(parsed_json: Dict[str, Any], source_filename: str) -> Dict[str, Any]:
    """Extract transaction-level metadata"""

    st = find_segment(parsed_json, 'ST')
    bht = find_segment(parsed_json, 'BHT')

    transaction = {
        'id': generate_object_id(),
        'controlNumber': st.get('ST02', '') if st else '',
        'transactionType': 'PROF',
        'transactionSetIdentifierCode': '837'
    }

    if bht:
        transaction['purposeCode'] = bht.get('BHT02', '')
        transaction['originatorApplicationTransactionId'] = bht.get('BHT03', '')

        # Parse creation date/time
        creation_date = bht.get('BHT04', '')
        creation_time = bht.get('BHT05', '')

        transaction['creationDate'] = format_edi_date(creation_date)
        transaction['creationTime'] = creation_time if creation_time else ''

        # Combine into datetime if both present
        if creation_date and creation_time:
            formatted_date = format_edi_date(creation_date)
            # Format time from HHMM to HH:MM:SS
            if len(creation_time) >= 4:
                formatted_time = f"{creation_time[:2]}:{creation_time[2:4]}:00"
                transaction['creationDateTime'] = f"{formatted_date}T{formatted_time}"

        transaction['claimOrEncounterIdentifierType'] = 'CHARGEABLE' if bht.get('BHT06') == 'CH' else 'REPORTING'

    # Extract implementation convention reference from ST
    if st:
        transaction['implementationConventionReference'] = st.get('ST03', '') or '005010X222'

    # Extract submitter and receiver from NM1 loops
    extract_submitter_receiver(parsed_json, transaction)

    # File info
    if source_filename:
        transaction['fileInfo'] = {
            'name': source_filename,
            'url': f'file://{source_filename}',
            'lastModifiedDateTime': '',
            'fileType': 'EDI'
        }

    return transaction


def extract_submitter_receiver(root: Dict[str, Any], transaction: Dict[str, Any]):
    """Extract submitter and receiver entities"""

    nm1_segments = find_all_segments(root, 'NM1')

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101', '')

        # Submitter (41)
        if entity_id == '41':
            submitter = create_entity_object(
                'SUBMITTER',
                'BUSINESS',
                'ETIN',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )

            # Extract contacts
            per_segments = find_all_segments(nm1, 'PER')
            if per_segments:
                contacts = []
                for per in per_segments:
                    contact = {
                        'name': per.get('PER02', ''),
                        'contactNumbers': []
                    }

                    comm_type_map = {'TE': 'PHONE', 'EX': 'EXTENSION', 'EM': 'EMAIL'}
                    if per.get('PER03'):
                        contact['contactNumbers'].append({
                            'type': comm_type_map.get(per.get('PER03'), 'PHONE'),
                            'number': per.get('PER04', '')
                        })
                    if per.get('PER05'):
                        contact['contactNumbers'].append({
                            'type': comm_type_map.get(per.get('PER05'), 'PHONE'),
                            'number': per.get('PER06', '')
                        })

                    if contact['contactNumbers']:
                        contacts.append(contact)

                if contacts:
                    submitter['contacts'] = contacts

            transaction['sender'] = submitter

        # Receiver (40)
        elif entity_id == '40':
            receiver = create_entity_object(
                'RECEIVER',
                'BUSINESS',
                'ETIN',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )

            transaction['receiver'] = receiver


def extract_claim(clm: Dict[str, Any], root: Dict[str, Any], transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comprehensive CLAIM object from CLM loop"""

    claim = {
        'id': generate_object_id(),
        'objectType': 'CLAIM',
        'transaction': transaction
    }

    # Basic claim info from CLM
    claim['patientControlNumber'] = clm.get('CLM01', '')
    claim['chargeAmount'] = safe_float(clm.get('CLM02'))

    # CLM05 composite field - place of service, frequency, etc.
    # Format: CLM05-1:place, CLM05-2:frequency, CLM05-3:provider signature, etc.
    place_code = clm.get('CLM0501', '') or clm.get('CLM05.01', '')
    freq_code = clm.get('CLM0502', '') or clm.get('CLM05.02', '') or '1'
    provider_sig = clm.get('CLM0503', '') or clm.get('CLM05.03', '')
    assignment = clm.get('CLM0506', '') or clm.get('CLM05.06', '')

    if place_code:
        claim['placeOfServiceCode'] = place_code
        claim['placeOfServiceType'] = lookup_place_of_service(place_code)
        claim['facilityCode'] = create_code_object('PLACE_OF_SERVICE', place_code)

    if freq_code:
        claim['frequencyCode'] = create_code_object(
            'FREQUENCY_CODE',
            freq_code,
            desc=lookup_frequency_description(freq_code)
        )

    # Provider signature indicator
    if provider_sig:
        claim['providerSignatureIndicator'] = provider_sig

    # Assignment/participation code
    if assignment:
        claim['assignmentParticipationCode'] = assignment

    # CLM09 - Release of information code
    release_code = clm.get('CLM09', '')
    if release_code:
        claim['releaseOfInformationCode'] = release_code

    # CLM10 - Assignment certification indicator
    assignment_cert = clm.get('CLM10', '')
    if assignment_cert:
        claim['assignmentCertificationIndicator'] = assignment_cert

    # CLM19 - Special program code
    special_program = clm.get('CLM19', '')
    if special_program:
        claim['specialProgramCode'] = special_program

    # CLM20 - Delay reason code
    delay_reason = clm.get('CLM20', '')
    if delay_reason:
        claim['delayReasonCode'] = delay_reason

    # Extract dates
    extract_dates(clm, claim)

    # Extract reference numbers
    extract_reference_numbers(clm, claim)

    # Extract claim note
    extract_claim_note(clm, claim)

    # Extract subscriber and patient info
    extract_subscriber_patient(clm, root, claim)

    # Extract billing provider
    extract_billing_provider(root, claim)

    # Extract other providers
    extract_providers(clm, root, claim)

    # Extract diagnoses
    extract_diagnoses(clm, claim)

    # Extract procedures
    extract_procedures(clm, claim)

    # Extract conditions
    extract_conditions(clm, claim)

    # Extract attachments
    extract_attachments(clm, claim)

    # Extract service lines
    extract_service_lines(clm, claim)

    return claim


def extract_dates(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract various claim dates"""

    dtp_segments = find_all_segments(clm, 'DTP')

    date_map = {
        '431': 'onsetOfCurrentIllnessOrInjuryDate',
        '454': 'initialTreatmentDate',
        '304': 'lastSeenDate',
        '453': 'acuteManifestationDate',
        '439': 'accidentDate',
        '484': 'lastMenstrualPeriodDate',
        '455': 'lastXRayDate',
        '090': 'assumedCareDate',
        '091': 'relinquishedCareDate',
        '360': 'disabilityDateFrom',
        '361': 'disabilityDateTo',
        '435': 'admissionDate',
        '096': 'dischargeDate',
        '050': 'repricerReceivedDate',
        '434': ('serviceDateFrom', 'serviceDateTo')  # Range
    }

    for dtp in dtp_segments:
        qualifier = dtp.get('DTP01', '')
        date_format = dtp.get('DTP02', '')
        date_value = dtp.get('DTP03', '')

        if qualifier in date_map:
            field_name = date_map[qualifier]

            if isinstance(field_name, tuple):  # Date range
                if date_format == 'RD8' and '-' in date_value:
                    from_date, to_date = date_value.split('-', 1)
                    claim[field_name[0]] = format_edi_date(from_date)
                    claim[field_name[1]] = format_edi_date(to_date)
                else:
                    claim[field_name[0]] = format_edi_date(date_value)
            else:
                claim[field_name] = format_edi_date(date_value)


def extract_reference_numbers(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract claim reference numbers"""

    ref_segments = find_all_segments(clm, 'REF')

    ref_map = {
        '9F': 'referralNumber',
        'G1': 'priorAuthorizationNumber',
        '9A': 'repricedReferenceNumber',
        '9C': 'adjustedRepricedReferenceNumber',
        'EA': 'medicalRecordNumber',
        'P4': 'demonstrationProjectIdentifier',
        'D9': 'clearinghouseTraceNumber',
        'F8': 'originalReferenceNumber',
        '4N': 'serviceAuthorizationExceptionCode'
    }

    for ref in ref_segments:
        qualifier = ref.get('REF01', '')
        ref_value = ref.get('REF02', '')

        if qualifier in ref_map:
            claim[ref_map[qualifier]] = ref_value


def extract_claim_note(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract claim-level note"""

    nte = find_segment(clm, 'NTE')
    if nte:
        note = nte.get('NTE02', '')
        if note:
            claim['claimNote'] = note


def extract_subscriber_patient(clm: Dict[str, Any], root: Dict[str, Any], claim: Dict[str, Any]):
    """Extract subscriber and patient information"""

    # Need to find the parent hierarchical loops
    # Look for HL segments and SBR segments at the claim level

    # Extract subscriber (primary insurance)
    sbr = find_segment(clm, 'SBR')
    if sbr:
        subscriber = {}

        subscriber['payerResponsibilitySequence'] = {
            'P': 'PRIMARY',
            'S': 'SECONDARY',
            'T': 'TERTIARY'
        }.get(sbr.get('SBR01', ''), 'PRIMARY')

        subscriber['relationshipType'] = {
            '01': 'SPOUSE',
            '18': 'SELF',
            '19': 'CHILD',
            '20': 'EMPLOYEE',
            '21': 'UNKNOWN',
            '39': 'ORGAN_DONOR',
            '40': 'CADAVER_DONOR',
            '53': 'LIFE_PARTNER'
        }.get(sbr.get('SBR02', ''), 'SELF')

        subscriber['groupOrPolicyNumber'] = sbr.get('SBR03', '')
        subscriber['claimFilingIndicatorCode'] = sbr.get('SBR09', '')

        filing_map = {
            'CI': 'COMMERCIAL', 'MB': 'MEDICARE_B', 'MC': 'MEDICAID',
            '11': 'OTHER', '12': 'PPO', '13': 'POS', '14': 'EPO',
            '15': 'INDEMNITY', '16': 'HMO'
        }
        subscriber['insurancePlanType'] = filing_map.get(subscriber['claimFilingIndicatorCode'], 'COMMERCIAL')

        # Extract subscriber person info
        nm1_segments = find_all_segments(clm, 'NM1')
        for nm1 in nm1_segments:
            if nm1.get('NM101') == 'IL':  # Insured/subscriber
                person = create_entity_object(
                    'SUBSCRIBER',
                    'INDIVIDUAL',
                    'MEMBER_ID',
                    nm1.get('NM109', ''),
                    lastNameOrOrgName=nm1.get('NM103', ''),
                    firstName=nm1.get('NM104', '')
                )

                # Add address
                address = {}
                n3 = find_segment(nm1, 'N3')
                if n3:
                    address['line'] = n3.get('N301', '')

                n4 = find_segment(nm1, 'N4')
                if n4:
                    address['city'] = n4.get('N401', '')
                    address['stateCode'] = n4.get('N402', '')
                    address['zipCode'] = n4.get('N403', '')

                if address:
                    person['address'] = address

                # Add demographic info
                dmg = find_segment(nm1, 'DMG')
                if dmg:
                    birth_date = format_edi_date(dmg.get('DMG02', ''))
                    if birth_date:
                        person['birthDate'] = birth_date

                    gender_code = dmg.get('DMG03', '')
                    gender_map = {'M': 'MALE', 'F': 'FEMALE', 'U': 'UNKNOWN'}
                    if gender_code:
                        person['gender'] = gender_map.get(gender_code, 'UNKNOWN')

                # Extract tax ID from REF
                ref_segments = find_all_segments(nm1, 'REF')
                for ref in ref_segments:
                    if ref.get('REF01') == 'SY':  # SSN
                        person['taxId'] = ref.get('REF02', '')

                subscriber['person'] = person

                # Extract death date, weight, pregnancy indicator
                # These would be in additional segments if present
                # (Not typically in 837P subscriber loop)

        # Extract payer info
        for nm1 in nm1_segments:
            if nm1.get('NM101') == 'PR':  # Payer
                payer = create_entity_object(
                    'PAYER',
                    'BUSINESS',
                    'PAYOR_ID',
                    nm1.get('NM109', ''),
                    lastNameOrOrgName=nm1.get('NM103', '')
                )

                # Add tax ID
                ref_segments = find_all_segments(nm1, 'REF')
                for ref in ref_segments:
                    if ref.get('REF01') == 'EI':  # EIN
                        payer['taxId'] = ref.get('REF02', '')
                    elif ref.get('REF01') == 'G2':  # Provider commercial number
                        if 'additionalIds' not in payer:
                            payer['additionalIds'] = []
                        payer['additionalIds'].append({
                            'qualifierCode': 'G2',
                            'type': 'PROVIDER_COMMERCIAL_NUMBER',
                            'identification': ref.get('REF02', '')
                        })

                # Add address
                address = {}
                n3 = find_segment(nm1, 'N3')
                if n3:
                    address['line'] = n3.get('N301', '')

                n4 = find_segment(nm1, 'N4')
                if n4:
                    address['city'] = n4.get('N401', '')
                    address['stateCode'] = n4.get('N402', '')
                    address['zipCode'] = n4.get('N403', '')

                if address:
                    payer['address'] = address

                subscriber['payer'] = payer

        claim['subscriber'] = subscriber

    # Extract patient info
    for nm1 in nm1_segments:
        if nm1.get('NM101') == 'QC':  # Patient
            patient = {}

            # Relationship type from PAT segment
            pat = find_segment(nm1, 'PAT')
            if pat:
                rel_code = pat.get('PAT01', '')
                rel_map = {
                    '01': 'SPOUSE',
                    '18': 'SELF',
                    '19': 'CHILD',
                    '20': 'EMPLOYEE',
                    '21': 'UNKNOWN'
                }
                patient['relationshipType'] = rel_map.get(rel_code, 'CHILD')

            person = create_entity_object(
                'PATIENT',
                'INDIVIDUAL',
                lastNameOrOrgName=nm1.get('NM103', ''),
                firstName=nm1.get('NM104', '')
            )

            # Add address
            address = {}
            n3 = find_segment(nm1, 'N3')
            if n3:
                address['line'] = n3.get('N301', '')

            n4 = find_segment(nm1, 'N4')
            if n4:
                address['city'] = n4.get('N401', '')
                address['stateCode'] = n4.get('N402', '')
                address['zipCode'] = n4.get('N403', '')

            if address:
                person['address'] = address

            # Add demographic info
            dmg = find_segment(nm1, 'DMG')
            if dmg:
                birth_date = format_edi_date(dmg.get('DMG02', ''))
                if birth_date:
                    person['birthDate'] = birth_date

                gender_code = dmg.get('DMG03', '')
                gender_map = {'M': 'MALE', 'F': 'FEMALE', 'U': 'UNKNOWN'}
                if gender_code:
                    person['gender'] = gender_map.get(gender_code, 'UNKNOWN')

            patient['person'] = person

            # Extract death date from DTP
            dtp_segments = find_all_segments(nm1, 'DTP')
            for dtp in dtp_segments:
                if dtp.get('DTP01') == '434':  # Date of death
                    patient['deathDate'] = format_edi_date(dtp.get('DTP03', ''))

            claim['patient'] = patient

    # Extract other subscribers (COB - coordination of benefits)
    extract_other_subscribers(clm, claim)


def extract_other_subscribers(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract other insurance/subscribers for COB"""

    # Other subscribers would be in additional SBR loops
    # For now, placeholder - would need hierarchical loop parsing
    # This is complex in 837P structure

    other_subscribers = []

    # In the target schema, otherSubscribers has adjustments, payer info, providers
    # This would require parsing additional 2320/2330 loops

    if other_subscribers:
        claim['otherSubscribers'] = other_subscribers


def extract_billing_provider(root: Dict[str, Any], claim: Dict[str, Any]):
    """Extract billing provider information"""

    # Billing provider is at 2000A loop level (hierarchical)
    nm1_segments = find_all_segments(root, 'NM1')

    for nm1 in nm1_segments:
        if nm1.get('NM101') == '85':  # Billing provider
            entity_type = nm1.get('NM102')  # 1=Person, 2=Organization

            billing_provider = create_entity_object(
                'BILLING_PROVIDER',
                'BUSINESS' if entity_type == '2' else 'INDIVIDUAL',
                'NPI',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )

            # Add first/middle name if person
            if entity_type == '1':
                billing_provider['firstName'] = nm1.get('NM104', '')
                billing_provider['middleName'] = nm1.get('NM105', '')

            # Tax ID from REF
            ref_segments = find_all_segments(nm1, 'REF')
            for ref in ref_segments:
                if ref.get('REF01') == 'EI':
                    billing_provider['taxId'] = ref.get('REF02', '')
                elif ref.get('REF01') == '0B':
                    if 'additionalIds' not in billing_provider:
                        billing_provider['additionalIds'] = []
                    billing_provider['additionalIds'].append({
                        'qualifierCode': '0B',
                        'type': 'STATE_LICENSE_NUMBER',
                        'identification': ref.get('REF02', '')
                    })

            # Address
            address = {}
            n3 = find_segment(nm1, 'N3')
            if n3:
                address['line'] = n3.get('N301', '')

            n4 = find_segment(nm1, 'N4')
            if n4:
                address['city'] = n4.get('N401', '')
                address['stateCode'] = n4.get('N402', '')
                address['zipCode'] = n4.get('N403', '')

            if address:
                billing_provider['address'] = address

            # Provider taxonomy from PRV
            prv = find_segment(nm1, 'PRV')
            if prv:
                taxonomy_code = prv.get('PRV03', '')
                if taxonomy_code:
                    billing_provider['providerTaxonomy'] = create_code_object(
                        'PROVIDER_TAXONOMY',
                        taxonomy_code
                    )

            # Contacts
            per_segments = find_all_segments(nm1, 'PER')
            if per_segments:
                contacts = []
                for per in per_segments:
                    contact = {
                        'name': per.get('PER02', ''),
                        'contactNumbers': []
                    }

                    comm_type_map = {'TE': 'PHONE', 'EX': 'EXTENSION'}
                    if per.get('PER03'):
                        contact['contactNumbers'].append({
                            'type': comm_type_map.get(per.get('PER03'), 'PHONE'),
                            'number': per.get('PER04', '')
                        })
                    if per.get('PER05'):
                        contact['contactNumbers'].append({
                            'type': comm_type_map.get(per.get('PER05'), 'EXTENSION'),
                            'number': per.get('PER06', '')
                        })

                    if contact['contactNumbers']:
                        contacts.append(contact)

                if contacts:
                    billing_provider['contacts'] = contacts

            claim['billingProvider'] = billing_provider
            break


def extract_providers(clm: Dict[str, Any], root: Dict[str, Any], claim: Dict[str, Any]):
    """Extract other providers (referring, rendering, service facility, supervising)"""

    providers = []

    nm1_segments = find_all_segments(clm, 'NM1')

    provider_type_map = {
        'DN': 'REFERRING',
        '82': 'RENDERING',
        '77': 'SERVICE_FACILITY',
        'DQ': 'SUPERVISING'
    }

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101', '')

        if entity_id in provider_type_map:
            entity_type = nm1.get('NM102')

            provider = create_entity_object(
                provider_type_map[entity_id],
                'BUSINESS' if entity_type == '2' else 'INDIVIDUAL',
                'NPI',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )

            if entity_type == '1':
                provider['firstName'] = nm1.get('NM104', '')
                provider['middleName'] = nm1.get('NM105', '')

            # Taxonomy from PRV
            prv = find_segment(nm1, 'PRV')
            if prv:
                taxonomy_code = prv.get('PRV03', '')
                if taxonomy_code:
                    provider['providerTaxonomy'] = create_code_object(
                        'PROVIDER_TAXONOMY',
                        taxonomy_code
                    )

            # Address (for service facility)
            if entity_id == '77':
                address = {}
                n3 = find_segment(nm1, 'N3')
                if n3:
                    address['line'] = n3.get('N301', '')

                n4 = find_segment(nm1, 'N4')
                if n4:
                    address['city'] = n4.get('N401', '')
                    address['stateCode'] = n4.get('N402', '')
                    address['zipCode'] = n4.get('N403', '')

                if address:
                    provider['address'] = address

            # Additional IDs
            ref_segments = find_all_segments(nm1, 'REF')
            if ref_segments:
                additional_ids = []
                for ref in ref_segments:
                    qualifier = ref.get('REF01', '')
                    type_map = {
                        'G2': 'PROVIDER_COMMERCIAL_NUMBER',
                        'LU': 'LOCATION_NUMBER'
                    }

                    additional_ids.append({
                        'qualifierCode': qualifier,
                        'type': type_map.get(qualifier, qualifier),
                        'identification': ref.get('REF02', '')
                    })

                if additional_ids:
                    provider['additionalIds'] = additional_ids

            providers.append(provider)

    if providers:
        claim['providers'] = providers


def extract_diagnoses(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract diagnosis codes"""

    hi_segments = find_all_segments(clm, 'HI')

    diags = []

    for hi in hi_segments:
        # HI segment can have up to 12 composite fields
        for i in range(1, 13):
            field_base = f'HI{i:02d}'

            # Try both formats
            qualifier = hi.get(f'{field_base}.01') or hi.get(f'{field_base}01', '')
            code = hi.get(f'{field_base}.02') or hi.get(f'{field_base}02', '')

            if not code:
                continue

            # Determine subtype from qualifier
            subtype_map = {
                'ABK': 'ICD_10_PRINCIPAL',
                'BK': 'ICD_10_PRINCIPAL',
                'ABF': 'ICD_10',
                'BF': 'ICD_10',
                'ABN': 'ICD_10'  # Admitting diagnosis
            }

            subtype = subtype_map.get(qualifier, 'ICD_10')

            # Format ICD-10 code
            formatted_code = format_icd10_code(code)

            diag = create_code_object(
                subtype,
                code,
                # Would lookup description from ICD-10 database
                desc='',
                formattedCode=formatted_code
            )

            diags.append(diag)

    if diags:
        claim['diags'] = diags


def extract_procedures(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract procedure codes (principal procedures)"""

    # Principal procedures are in HI segments with different qualifiers
    hi_segments = find_all_segments(clm, 'HI')

    procs = []

    for hi in hi_segments:
        for i in range(1, 13):
            field_base = f'HI{i:02d}'

            qualifier = hi.get(f'{field_base}.01') or hi.get(f'{field_base}01', '')
            code = hi.get(f'{field_base}.02') or hi.get(f'{field_base}02', '')

            if not code:
                continue

            # Principal procedure qualifiers
            if qualifier in ['BP', 'BR']:
                subtype = 'HCPCS_PRINCIPAL' if qualifier == 'BP' else 'HCPCS'

                proc = create_code_object(
                    subtype,
                    code,
                    desc=''  # Would lookup from HCPCS database
                )

                procs.append(proc)

    if procs:
        claim['procs'] = procs


def extract_conditions(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract condition codes"""

    # Condition codes are in HI segments with qualifier BG
    hi_segments = find_all_segments(clm, 'HI')

    conditions = []

    for hi in hi_segments:
        for i in range(1, 13):
            field_base = f'HI{i:02d}'

            qualifier = hi.get(f'{field_base}.01') or hi.get(f'{field_base}01', '')
            code = hi.get(f'{field_base}.02') or hi.get(f'{field_base}02', '')

            if qualifier == 'BG' and code:
                condition = create_code_object(
                    'CONDITION',
                    code,
                    desc='',  # Would lookup from condition code database
                    instructionDesc=''
                )

                conditions.append(condition)

    if conditions:
        claim['conditions'] = conditions


def extract_attachments(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract claim attachments"""

    pwk_segments = find_all_segments(clm, 'PWK')

    attachments = []

    for pwk in pwk_segments:
        attachment = {
            'reportTypeCode': pwk.get('PWK01', ''),
            'reportTransmissionCode': pwk.get('PWK02', '')
        }

        # Control number from PWK06
        control_number = pwk.get('PWK06', '')
        if control_number:
            attachment['controlNumber'] = control_number

        attachments.append(attachment)

    if attachments:
        claim['attachments'] = attachments


def extract_service_lines(clm: Dict[str, Any], claim: Dict[str, Any]):
    """Extract service line items"""

    # Service lines are in LX loops (2400)
    children = clm.get('_children', [])

    service_lines = []

    for child in children:
        if child.get('BOTSID') == 'LX':
            line = {}

            # Line number
            line_num = child.get('LX01', '')
            if line_num:
                line['sourceLineId'] = line_num

            # Find SV1 segment
            sv1 = find_segment(child, 'SV1')
            if not sv1:
                continue

            # SV101 composite - procedure code
            # Format: HC:code:modifier1:modifier2...
            procedure_composite = sv1.get('SV101', '')
            if not isinstance(procedure_composite, str):
                # Try component access
                code_qual = sv1.get('SV10101', '')
                code = sv1.get('SV10102', '')
                modifiers = [
                    sv1.get('SV10103', ''),
                    sv1.get('SV10104', ''),
                    sv1.get('SV10105', ''),
                    sv1.get('SV10106', '')
                ]
            else:
                parts = procedure_composite.split(':')
                code_qual = parts[0] if len(parts) > 0 else ''
                code = parts[1] if len(parts) > 1 else ''
                modifiers = parts[2:] if len(parts) > 2 else []

            if code:
                subtype_map = {'HC': 'CPT', 'AD': 'ADA', 'ER': 'CPT', 'IV': 'CPT'}
                subtype = subtype_map.get(code_qual, 'CPT')

                procedure = create_code_object(subtype, code, desc='')

                if modifiers:
                    procedure['modifiers'] = [
                        create_code_object('HCPCS_MODIFIER', m) for m in modifiers if m
                    ]

                line['procedure'] = procedure

            # Amounts
            line['chargeAmount'] = safe_float(sv1.get('SV102'))

            # Units
            unit_basis = sv1.get('SV103', '')
            unit_count = safe_float(sv1.get('SV104'))

            line['unitType'] = unit_basis if unit_basis else 'UNIT'
            line['unitCount'] = unit_count

            # Place of service
            pos_code = sv1.get('SV105', '')
            if pos_code:
                line['placeOfServiceCode'] = pos_code
                line['placeOfServiceType'] = lookup_place_of_service(pos_code)

            # Diagnosis pointers (SV107)
            diag_pointers = sv1.get('SV107', '')
            if diag_pointers:
                # Parse pointer list (e.g., "1:2" or "1" or "1,2")
                if ':' in diag_pointers:
                    pointers = [int(p) for p in diag_pointers.split(':') if p.isdigit()]
                else:
                    pointers = [int(diag_pointers)] if diag_pointers.isdigit() else []

                line['diagPointers'] = pointers

                # Copy referenced diagnoses into line
                if 'diags' in claim and pointers:
                    line_diags = []
                    for ptr in pointers:
                        if ptr <= len(claim['diags']):
                            line_diags.append(claim['diags'][ptr - 1])

                    if line_diags:
                        line['diags'] = line_diags

            # Extract line-level dates
            extract_line_dates(child, line)

            # Extract line-level references
            extract_line_references(child, line)

            # Extract line-level notes
            nte = find_segment(child, 'NTE')
            if nte:
                note = nte.get('NTE02', '')
                if note:
                    line['lineNote'] = note

            # Extract drug information (LIN segment)
            extract_drug_info(child, line)

            # Extract line-level providers
            extract_line_providers(child, line)

            # Extract line-level attachments
            extract_line_attachments(child, line)

            # Extract adjudications (if claim was adjudicated)
            extract_adjudications(child, line)

            # Extract EPSDT indicators
            extract_epsdt_info(child, line)

            service_lines.append(line)

    if service_lines:
        claim['serviceLines'] = service_lines


def extract_line_dates(line_loop: Dict[str, Any], line: Dict[str, Any]):
    """Extract service line dates"""

    dtp_segments = find_all_segments(line_loop, 'DTP')

    date_map = {
        '472': 'serviceDateFrom',
        '150': 'serviceDateTo',
        '471': 'prescriptionDate',
        '463': 'beginTherapyDate',
        '304': 'lastSeenDate',
        '738': 'testPerformedDate',
        '455': 'lastXRayDate',
        '454': 'initialTreatmentDate'
    }

    for dtp in dtp_segments:
        qualifier = dtp.get('DTP01', '')
        date_format = dtp.get('DTP02', '')
        date_value = dtp.get('DTP03', '')

        if qualifier == '472' and date_format == 'RD8' and '-' in date_value:
            # Service date range
            from_date, to_date = date_value.split('-', 1)
            line['serviceDateFrom'] = format_edi_date(from_date)
            line['serviceDateTo'] = format_edi_date(to_date)
        elif qualifier in date_map:
            line[date_map[qualifier]] = format_edi_date(date_value)


def extract_line_references(line_loop: Dict[str, Any], line: Dict[str, Any]):
    """Extract service line reference numbers"""

    ref_segments = find_all_segments(line_loop, 'REF')

    ref_map = {
        '9A': 'repricedReferenceNumber',
        '9C': 'adjustedRepricedReferenceNumber',
        'G1': 'priorAuthorization',
        '9F': 'referralNumber'
    }

    for ref in ref_segments:
        qualifier = ref.get('REF01', '')
        ref_value = ref.get('REF02', '')

        if qualifier in ref_map:
            line[ref_map[qualifier]] = ref_value


def extract_drug_info(line_loop: Dict[str, Any], line: Dict[str, Any]):
    """Extract drug/prescription information"""

    lin = find_segment(line_loop, 'LIN')
    if lin:
        # LIN03 is NDC code
        ndc_code = lin.get('LIN03', '')
        if ndc_code and len(ndc_code) == 11:
            formatted_ndc = format_ndc_code(ndc_code)

            line['drug'] = create_code_object(
                'NDC',
                ndc_code,
                desc='',  # Would lookup from NDC database
                formattedCode=formatted_ndc
            )

    # Extract drug quantity from CTP
    ctp = find_segment(line_loop, 'CTP')
    if ctp:
        drug_qty = safe_float(ctp.get('CTP04', ''))
        if drug_qty:
            line['drugQuantity'] = drug_qty

        unit_basis = ctp.get('CTP05', '')
        if unit_basis:
            line['drugUnitType'] = unit_basis

    # Extract prescription number from REF
    ref_segments = find_all_segments(line_loop, 'REF')
    for ref in ref_segments:
        if ref.get('REF01') == 'XZ':  # Prescription number
            line['prescriptionNumber'] = ref.get('REF02', '')


def extract_line_providers(line_loop: Dict[str, Any], line: Dict[str, Any]):
    """Extract line-level providers"""

    nm1_segments = find_all_segments(line_loop, 'NM1')

    providers = []

    provider_type_map = {
        '82': 'RENDERING',
        'QB': 'PURCHASE_SERVICE',
        'DQ': 'SUPERVISING'
    }

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101', '')

        if entity_id in provider_type_map:
            entity_type = nm1.get('NM102')

            provider = create_entity_object(
                provider_type_map[entity_id],
                'BUSINESS' if entity_type == '2' else 'INDIVIDUAL',
                'NPI',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )

            if entity_type == '1':
                provider['firstName'] = nm1.get('NM104', '')
                provider['middleName'] = nm1.get('NM105', '')

            # Additional IDs
            ref_segments = find_all_segments(nm1, 'REF')
            if ref_segments:
                additional_ids = []
                for ref in ref_segments:
                    qualifier = ref.get('REF01', '')
                    additional_ids.append({
                        'qualifierCode': qualifier,
                        'type': 'PROVIDER_COMMERCIAL_NUMBER' if qualifier == 'G2' else qualifier,
                        'identification': ref.get('REF02', '')
                    })

                if additional_ids:
                    provider['additionalIds'] = additional_ids

            providers.append(provider)

    if providers:
        line['providers'] = providers


def extract_line_attachments(line_loop: Dict[str, Any], line: Dict[str, Any]):
    """Extract line-level attachments"""

    pwk_segments = find_all_segments(line_loop, 'PWK')

    attachments = []

    for pwk in pwk_segments:
        attachment = {
            'reportTypeCode': pwk.get('PWK01', ''),
            'reportTransmissionCode': pwk.get('PWK02', '')
        }

        control_number = pwk.get('PWK06', '')
        if control_number:
            attachment['controlNumber'] = control_number

        attachments.append(attachment)

    if attachments:
        line['attachments'] = attachments


def extract_adjudications(line_loop: Dict[str, Any], line: Dict[str, Any]):
    """Extract line-level adjudication info (if present)"""

    # SVD segments contain adjudication details
    svd_segments = find_all_segments(line_loop, 'SVD')

    adjudications = []

    for svd in svd_segments:
        adjudication = {}

        # Payer identifier
        payer_id = svd.get('SVD01', '')
        if payer_id:
            adjudication['payerIdentifier'] = payer_id

        # Paid amount
        paid_amount = safe_float(svd.get('SVD02'))
        if paid_amount:
            adjudication['paidAmount'] = paid_amount

        # Procedure info (SVD03 composite)
        proc_composite = svd.get('SVD03', '')
        if isinstance(proc_composite, str) and ':' in proc_composite:
            parts = proc_composite.split(':')
            if len(parts) >= 2:
                adjudication['procedure'] = create_code_object(
                    'CPT' if parts[0] == 'HC' else parts[0],
                    parts[1],
                    desc=''
                )

        # Units
        units = safe_float(svd.get('SVD05'))
        if units:
            adjudication['unitCount'] = units

        adjudications.append(adjudication)

    if adjudications:
        line['adjudications'] = adjudications


def extract_epsdt_info(line_loop: Dict[str, Any], line: Dict[str, Any]):
    """Extract EPSDT (Early Periodic Screening Diagnosis Treatment) indicators"""

    # EPSDT info is in various segments
    # CR1-3 for emergency indicator
    # CR5 for family planning

    cr1 = find_segment(line_loop, 'CR1')
    if cr1:
        emergency = cr1.get('CR103', '')
        if emergency:
            line['emergencyIndicator'] = emergency

    cr5 = find_segment(line_loop, 'CR5')
    if cr5:
        # EPSDT indicator
        epsdt = cr5.get('CR501', '')
        if epsdt:
            line['epsdtIndicator'] = epsdt

        # Family planning
        family_planning = cr5.get('CR502', '')
        if family_planning:
            line['familyPlanningIndicator'] = family_planning

    # Copay status from CR6
    cr6 = find_segment(line_loop, 'CR6')
    if cr6:
        copay_status = cr6.get('CR602', '')
        if copay_status:
            line['copayStatusCode'] = copay_status

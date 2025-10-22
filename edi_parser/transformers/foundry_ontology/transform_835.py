"""
835 Electronic Remittance Advice Transformer

Transforms parsed 835 EDI JSON into structured ontology schemas.
Outputs a single comprehensive PAYMENT object matching the target schema.
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
    lookup_rarc_description,
    lookup_place_of_service,
    lookup_frequency_description,
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


def transform_835(
    parsed_json: Dict[str, Any],
    source_filename: str = ''
) -> List[Dict[str, Any]]:
    """
    Transform 835 parsed EDI JSON to structured PAYMENT ontology schema

    Args:
        parsed_json: Parsed 835 EDI JSON (with human-readable names applied)
        source_filename: Source EDI filename

    Returns:
        List containing single PAYMENT object
    """
    # Extract transaction-level info first
    transaction = extract_transaction(parsed_json, source_filename)

    # Find all claim payment loops (CLP segments)
    clp_segments = find_all_segments(parsed_json, 'CLP')

    if not clp_segments:
        return []

    # For now, process first CLP (in production might process all)
    # Target schema shows single payment object
    clp = clp_segments[0]

    payment = extract_payment(clp, parsed_json, transaction)

    return [payment]


def extract_transaction(parsed_json: Dict[str, Any], source_filename: str) -> Dict[str, Any]:
    """Extract transaction-level metadata"""

    st = find_segment(parsed_json, 'ST')
    bpr = find_segment(parsed_json, 'BPR')
    trn = find_segment(parsed_json, 'TRN')
    dtm = find_segment(parsed_json, 'DTM')

    transaction = {
        'id': generate_object_id(),
        'controlNumber': st.get('ST02', '') if st else '',
        'transactionType': 'PAYMENT',
        'transactionSetIdentifierCode': '835'
    }

    # Extract BPR payment info
    if bpr:
        transaction['productionDate'] = format_edi_date(bpr.get('BPR16', ''))
        transaction['transactionHandlingType'] = 'INFORMATION_ONLY' if bpr.get('BPR01') == 'I' else 'PAYMENT'
        transaction['totalPaymentAmount'] = safe_float(bpr.get('BPR02'))
        transaction['creditOrDebitFlagCode'] = bpr.get('BPR03', '')
        transaction['paymentMethodType'] = bpr.get('BPR04', '') # ACH, CHK, etc
        transaction['paymentFormatCode'] = bpr.get('BPR05', '')
        transaction['senderBankRoutingNumber'] = bpr.get('BPR08', '')
        transaction['senderAccountNumber'] = bpr.get('BPR10', '')
        transaction['originatingCompanyId'] = bpr.get('BPR11', '')
        transaction['receiverBankRoutingNumber'] = bpr.get('BPR13', '')
        transaction['receiverAccountNumber'] = bpr.get('BPR15', '')
        transaction['paymentDate'] = format_edi_date(bpr.get('BPR16', ''))

    # Extract TRN trace info
    if trn:
        transaction['checkOrEftTraceNumber'] = trn.get('TRN02', '')
        transaction['payerIdentifier'] = trn.get('TRN03', '')

    # Receiver identifier
    transaction['receiverIdentifier'] = 'CLEARINGHOUSE'

    # File info
    if source_filename:
        transaction['fileInfo'] = {
            'name': source_filename,
            'url': f'file://{source_filename}',
            'lastModifiedDateTime': '',
            'fileType': 'EDI'
        }

    return transaction


def extract_payment(clp: Dict[str, Any], root: Dict[str, Any], transaction: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comprehensive PAYMENT object from CLP loop"""

    payment = {
        'id': generate_object_id(),
        'objectType': 'PAYMENT',
        'transaction': transaction
    }

    # Basic claim info from CLP
    payment['patientControlNumber'] = clp.get('CLP01', '')
    payment['claimStatusCode'] = clp.get('CLP02', '')
    payment['chargeAmount'] = safe_float(clp.get('CLP03'))
    payment['paymentAmount'] = safe_float(clp.get('CLP04'))
    payment['patientResponsibilityAmount'] = safe_float(clp.get('CLP05'))
    payment['claimFilingIndicatorCode'] = clp.get('CLP06', '')
    payment['payerControlNumber'] = clp.get('CLP07', '')

    # Map claim status code to status name
    status_map = {'1': 'PRIMARY', '2': 'SECONDARY', '3': 'TERTIARY'}
    payment['claimStatus'] = status_map.get(payment['claimStatusCode'], 'PRIMARY')

    # Map claim filing indicator to insurance plan type
    filing_map = {
        '11': 'OTHER', '12': 'PPO', '13': 'POS', '14': 'EPO',
        '15': 'INDEMNITY', '16': 'HMO', 'AM': 'AUTO', 'CH': 'CHAMPUS',
        'CI': 'COMMERCIAL', 'MB': 'MEDICARE_B', 'MC': 'MEDICAID'
    }
    payment['insurancePlanType'] = filing_map.get(payment['claimFilingIndicatorCode'], 'COMMERCIAL')

    # Extract dates
    extract_dates(clp, payment)

    # Extract facility/place of service codes
    extract_facility_codes(clp, payment)

    # Extract subscriber and patient
    extract_subscriber_patient(clp, payment)

    # Extract payer and payee from root
    extract_payer_payee(root, payment)

    # Extract service provider / rendering provider
    extract_service_provider(clp, payment)

    # Extract crossover carrier, corrected payer/insured
    extract_corrected_entities(clp, payment)

    # Extract claim-level reference IDs
    extract_claim_refs(clp, payment)

    # Extract supplemental amounts and quantities
    extract_supplemental_info(clp, payment)

    # Extract DRG info (for institutional claims)
    extract_drg_info(clp, payment)

    # Extract outpatient adjudication
    extract_outpatient_adj(clp, payment)

    # Extract claim-level adjustments
    extract_adjustments(clp, payment)

    # Extract claim contacts
    extract_claim_contacts(clp, payment)

    # Extract service lines
    extract_service_lines(clp, payment)

    return payment


def extract_dates(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract various dates"""

    dtp_segments = find_all_segments(clp, 'DTM')

    for dtp in dtp_segments:
        qualifier = dtp.get('DTM01', '')
        date_value = format_edi_date(dtp.get('DTM02', ''))

        if qualifier == '232':  # Claim statement period start
            payment['statementDateFrom'] = date_value
        elif qualifier == '233':  # Claim statement period end
            payment['statementDateTo'] = date_value
        elif qualifier == '050':  # Received date
            payment['claimReceivedDate'] = date_value
        elif qualifier == '036':  # Expiration date
            payment['coverageExpirationDate'] = date_value
        elif qualifier == '472':  # Service date
            if 'serviceDateFrom' not in payment:
                payment['serviceDateFrom'] = date_value
        elif qualifier == 'D8':  # Service end date
            payment['serviceDateTo'] = date_value


def extract_facility_codes(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract facility code, place of service, frequency code"""

    # These might be in CAS or MIA/MOA segments
    mia = find_segment(clp, 'MIA')
    moa = find_segment(clp, 'MOA')

    # Facility code (typically institutional)
    if mia:
        facility_code = mia.get('MIA01', '')
        if facility_code:
            payment['facilityCode'] = create_code_object(
                'FACILITY_TYPE',
                facility_code,
                desc='Hospital; inpatient' if facility_code == '11' else ''
            )
            payment['placeOfServiceType'] = lookup_place_of_service(facility_code)

    # Frequency code
    # Usually from CLM05-2 in 837, but in 835 might need to infer
    payment['frequencyCode'] = create_code_object(
        'FREQUENCY_CODE',
        '1',
        desc='Original claim'
    )


def extract_subscriber_patient(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract subscriber and patient person objects"""

    nm1_segments = find_all_segments(clp, 'NM1')

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101', '')

        # Insured/Subscriber (IL)
        if entity_id == 'IL':
            person = create_entity_object(
                'INSURED_SUBSCRIBER',
                'INDIVIDUAL',
                'MEMBER_ID',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', ''),
                firstName=nm1.get('NM104', '')
            )
            payment['subscriber'] = {'person': person}

        # Patient (QC)
        elif entity_id == 'QC':
            person = create_entity_object(
                'PATIENT',
                'INDIVIDUAL',
                lastNameOrOrgName=nm1.get('NM103', ''),
                firstName=nm1.get('NM104', '')
            )
            payment['patient'] = {'person': person}


def extract_payer_payee(root: Dict[str, Any], payment: Dict[str, Any]):
    """Extract payer and payee entities from root level"""

    nm1_segments = find_all_segments(root, 'NM1')

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101', '')

        # Payer (PR)
        if entity_id == 'PR':
            payer = create_entity_object(
                'PAYER',
                'BUSINESS',
                'PAYOR_ID',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
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
                payer['address'] = address

            # Add contacts
            contacts = []
            per_segments = find_all_segments(nm1, 'PER')
            for per in per_segments:
                contact = {
                    'functionCode': per.get('PER01', ''),
                    'name': per.get('PER02', ''),
                    'contactNumbers': []
                }

                # Extract phone/email/url
                if per.get('PER03'):  # Communication qualifier
                    comm_type_map = {'TE': 'PHONE', 'EX': 'EXTENSION', 'EM': 'EMAIL', 'UR': 'URL'}
                    contact['contactNumbers'].append({
                        'type': comm_type_map.get(per.get('PER03'), 'PHONE'),
                        'number': per.get('PER04', '')
                    })

                if per.get('PER05'):
                    comm_type_map = {'TE': 'PHONE', 'EX': 'EXTENSION', 'EM': 'EMAIL', 'UR': 'URL'}
                    contact['contactNumbers'].append({
                        'type': comm_type_map.get(per.get('PER05'), 'PHONE'),
                        'number': per.get('PER06', '')
                    })

                if contact['contactNumbers']:
                    contacts.append(contact)

            if contacts:
                payer['contacts'] = contacts

            # Add additional IDs
            additional_ids = []
            ref_segments = find_all_segments(nm1, 'REF')
            for ref in ref_segments:
                qualifier = ref.get('REF01', '')
                id_value = ref.get('REF02', '')

                type_map = {
                    '2U': 'PAYER_IDENTIFICATION_NUMBER',
                    'HI': 'HEALTH_INDUSTRY_NUMBER'
                }

                additional_ids.append({
                    'qualifierCode': qualifier,
                    'type': type_map.get(qualifier, qualifier),
                    'identification': id_value
                })

            if additional_ids:
                payer['additionalIds'] = additional_ids

            payment['payer'] = payer

        # Payee (PE)
        elif entity_id == 'PE':
            payee = create_entity_object(
                'PAYEE',
                'BUSINESS',
                'EIN',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )

            # Tax ID
            ref = find_segment(nm1, 'REF', {'REF01': 'TJ'})
            if ref:
                payee['taxId'] = ref.get('REF02', '')

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
                payee['address'] = address

            # Additional IDs
            additional_ids = []
            ref_segments = find_all_segments(nm1, 'REF')
            for ref in ref_segments:
                if ref.get('REF01') != 'TJ':  # Skip tax ID, already extracted
                    additional_ids.append({
                        'qualifierCode': ref.get('REF01', ''),
                        'type': 'PAYEE_IDENTIFICATION_NUMBER',
                        'identification': ref.get('REF02', '')
                    })

            if additional_ids:
                payee['additionalIds'] = additional_ids

            payment['payee'] = payee


def extract_service_provider(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract rendering/service provider"""

    nm1_segments = find_all_segments(clp, 'NM1')

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101', '')

        # Rendering provider (82)
        if entity_id == '82':
            provider = create_entity_object(
                'RENDERING',
                'INDIVIDUAL',
                'NPI',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', ''),
                firstName=nm1.get('NM104', '')
            )

            # Additional IDs
            additional_ids = []
            ref_segments = find_all_segments(nm1, 'REF')
            for ref in ref_segments:
                qualifier = ref.get('REF01', '')
                type_map = {
                    '1C': 'MEDICARE_PROVIDER_NUMBER',
                    '1G': 'PROVIDER_UPIN_NUMBER'
                }

                additional_ids.append({
                    'qualifierCode': qualifier,
                    'type': type_map.get(qualifier, qualifier),
                    'identification': ref.get('REF02', '')
                })

            if additional_ids:
                provider['additionalIds'] = additional_ids

            payment['serviceProvider'] = provider


def extract_corrected_entities(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract crossover carrier, corrected payer, corrected insured"""

    nm1_segments = find_all_segments(clp, 'NM1')

    for nm1 in nm1_segments:
        entity_id = nm1.get('NM101', '')

        # Crossover carrier (TT)
        if entity_id == 'TT':
            payment['crossoverCarrier'] = create_entity_object(
                'CROSSOVER_CARRIER',
                'INDIVIDUAL',
                'CMS_PLAN_ID',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )

        # Corrected payer (PR with specific context)
        # This would need more context to distinguish from primary payer

        # Corrected insured (74)
        elif entity_id == '74':
            payment['correctedInsured'] = create_entity_object(
                'CORRECTED_INSURED',
                'INDIVIDUAL',
                'INSURED_CHANGED_ID',
                nm1.get('NM109', ''),
                lastNameOrOrgName=nm1.get('NM103', '')
            )


def extract_claim_refs(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract claim-related reference IDs"""

    ref_segments = find_all_segments(clp, 'REF')

    other_claim_ids = []

    for ref in ref_segments:
        qualifier = ref.get('REF01', '')
        identification = ref.get('REF02', '')

        # Map qualifier to type
        type_map = {
            'F8': 'ORIGINAL_REFERENCE_NUMBER',
            'EA': 'MEDICAL_RECORD_NUMBER',
            '1L': 'GROUP_OR_POLICY_NUMBER',
            '1W': 'MEMBER_IDENTIFICATION_NUMBER',
            '28': 'EMPLOYEE_IDENTIFICATION_NUMBER',
            '6P': 'GROUP_NUMBER',
            '9A': 'REPRICED_REFERENCE_NUMBER',
            '9C': 'ADJUSTED_REPRICED_REFERENCE_NUMBER',
            'BB': 'AUTHORIZATION_NUMBER',
            'CE': 'CLASS_OF_CONTRACT_CODE',
            'G1': 'PRIOR_AUTHORIZATION_NUMBER',
            'G3': 'PREDETERMINATION_OF_BENEFITS_NUMBER',
            'SY': 'SSN'
        }

        other_claim_ids.append({
            'qualifierCode': qualifier,
            'type': type_map.get(qualifier, qualifier),
            'identification': identification
        })

    if other_claim_ids:
        payment['otherClaimRelatedIds'] = other_claim_ids


def extract_supplemental_info(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract supplemental amounts and quantities"""

    amt_segments = find_all_segments(clp, 'AMT')
    qty_segments = find_all_segments(clp, 'QTY')

    supplemental_amounts = []
    supplemental_quantities = []

    for amt in amt_segments:
        qualifier = amt.get('AMT01', '')
        amount = safe_float(amt.get('AMT02'))

        type_map = {
            'AU': 'COVERAGE_AMOUNT',
            'D8': 'DISCOUNT_AMOUNT'
        }

        supplemental_amounts.append({
            'qualifierCode': qualifier,
            'type': type_map.get(qualifier, qualifier),
            'amount': amount
        })

    for qty in qty_segments:
        qualifier = qty.get('QTY01', '')
        quantity = safe_float(qty.get('QTY02'))

        type_map = {
            'CA': 'COVERED'
        }

        supplemental_quantities.append({
            'qualifierCode': qualifier,
            'type': type_map.get(qualifier, qualifier),
            'quantity': quantity
        })

    if supplemental_amounts:
        payment['supplementalAmounts'] = supplemental_amounts
    if supplemental_quantities:
        payment['supplementalQuantities'] = supplemental_quantities


def extract_drg_info(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract DRG (Diagnosis Related Group) information"""

    mia = find_segment(clp, 'MIA')

    if mia:
        drg_code = mia.get('MIA15', '')
        if drg_code:
            payment['drg'] = create_code_object('DRG', drg_code)

        drg_weight = safe_float(mia.get('MIA16'))
        if drg_weight:
            payment['drgWeight'] = drg_weight

        discharge_fraction = safe_float(mia.get('MIA17'))
        if discharge_fraction:
            payment['dischargeFraction'] = discharge_fraction


def extract_outpatient_adj(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract outpatient adjudication info"""

    moa = find_segment(clp, 'MOA')

    if moa:
        outpatient_adj = {}

        reimbursement_rate = safe_float(moa.get('MOA01'))
        if reimbursement_rate:
            outpatient_adj['reimbursementRate'] = reimbursement_rate

        hcpcs_payable = safe_float(moa.get('MOA02'))
        if hcpcs_payable:
            outpatient_adj['hcpcsPayableAmount'] = hcpcs_payable

        esrd_payment = safe_float(moa.get('MOA05'))
        if esrd_payment:
            outpatient_adj['esrdPaymentAmount'] = esrd_payment

        non_payable_prof = safe_float(moa.get('MOA06'))
        if non_payable_prof:
            outpatient_adj['nonPayableProfessionalComponentAmount'] = non_payable_prof

        # Extract remark codes
        remarks = []
        remark_codes = [moa.get('MOA08'), moa.get('MOA09'), moa.get('MOA10'), moa.get('MOA11')]
        for code in remark_codes:
            if code:
                remarks.append(create_code_object(
                    'RARC',
                    code,
                    desc=lookup_rarc_description(code)
                ))

        if remarks:
            outpatient_adj['remarks'] = remarks

        if outpatient_adj:
            payment['outpatientAdjudication'] = outpatient_adj


def extract_adjustments(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract claim-level adjustments (CAS segments)"""

    cas_segments = find_all_segments(clp, 'CAS')

    adjustments = []

    for cas in cas_segments:
        group_code = cas.get('CAS01', '')
        group = GROUP_CODE_MAP.get(group_code, group_code)

        # Extract up to 6 adjustment triplets (reason, amount, quantity)
        for i in range(1, 7):
            reason_field = f'CAS{i*3-1:02d}'  # CAS02, CAS05, CAS08, CAS11, CAS14, CAS17
            amount_field = f'CAS{i*3:02d}'     # CAS03, CAS06, CAS09, CAS12, CAS15, CAS18
            qty_field = f'CAS{i*3+1:02d}'      # CAS04, CAS07, CAS10, CAS13, CAS16, CAS19

            reason_code = cas.get(reason_field, '')
            amount = safe_float(cas.get(amount_field))
            quantity = safe_float(cas.get(qty_field))

            if not reason_code:
                break

            adjustment = {
                'group': group,
                'reasonCode': reason_code,
                'reason': create_code_object(
                    'CARC',
                    reason_code,
                    desc=lookup_carc_description(reason_code)
                ),
                'amount': amount
            }

            if quantity:
                adjustment['quantity'] = quantity

            adjustments.append(adjustment)

    if adjustments:
        payment['adjustments'] = adjustments


def extract_claim_contacts(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract claim-level contacts"""

    per_segments = find_all_segments(clp, 'PER')

    contacts = []

    for per in per_segments:
        contact = {
            'functionCode': per.get('PER01', ''),
            'contactNumbers': []
        }

        # Extract contact numbers
        comm_type_map = {'TE': 'PHONE', 'EX': 'EXTENSION', 'EM': 'EMAIL', 'UR': 'URL'}

        if per.get('PER03'):
            contact['contactNumbers'].append({
                'type': comm_type_map.get(per.get('PER03'), 'PHONE'),
                'number': per.get('PER04', '')
            })

        if contact['contactNumbers']:
            contacts.append(contact)

    if contacts:
        payment['claimContacts'] = contacts


def extract_service_lines(clp: Dict[str, Any], payment: Dict[str, Any]):
    """Extract service line items (SVC segments)"""

    svc_segments = find_all_segments(clp, 'SVC')

    service_lines = []

    for svc in svc_segments:
        line = {}

        # SVC01 composite - procedure code
        # Format: HC:code:modifier1:modifier2...
        svc01 = svc.get('SVC01', '') or svc.get('SVC0101', '') or ''
        if isinstance(svc01, str) and ':' in svc01:
            parts = svc01.split(':')
            if len(parts) >= 2:
                code_qual = parts[0]
                code = parts[1]
                modifiers = parts[2:] if len(parts) > 2 else []

                # Determine subtype from qualifier
                subtype_map = {'HC': 'HCPCS', 'AD': 'ADA', 'NU': 'NDC', 'RB': 'REVENUE_CODE'}
                subtype = subtype_map.get(code_qual, 'HCPCS')

                if subtype == 'ADA':
                    line['procedure'] = create_code_object(
                        'ADA',
                        code,
                        # Would lookup description from ADA code database
                    )

                    if modifiers:
                        line['procedure']['modifiers'] = [
                            create_code_object('HCPCS_MODIFIER', m) for m in modifiers if m
                        ]

                elif subtype == 'REVENUE_CODE':
                    line['revenueCode'] = create_code_object(
                        'REVENUE_CODE',
                        code
                    )

        # Amounts
        line['chargeAmount'] = safe_float(svc.get('SVC02'))
        line['paidAmount'] = safe_float(svc.get('SVC03'))

        # Units
        line['unitCount'] = safe_float(svc.get('SVC05'))

        # Original procedure (SVC06 composite)
        svc06 = svc.get('SVC06', '') or svc.get('SVC0601', '') or ''
        if isinstance(svc06, str) and ':' in svc06:
            parts = svc06.split(':')
            if len(parts) >= 2:
                line['originalProcedure'] = create_code_object(
                    'ADA',
                    parts[1]
                )
                if len(parts) > 2:
                    line['originalProcedure']['modifiers'] = [
                        create_code_object('HCPCS_MODIFIER', m) for m in parts[2:] if m
                    ]

        # Original units
        original_units = safe_float(svc.get('SVC07'))
        if original_units:
            line['originalUnitCount'] = original_units

        # Extract service dates
        dtp_segments = find_all_segments(svc, 'DTM')
        for dtp in dtp_segments:
            if dtp.get('DTM01') == '472':
                line['serviceDateFrom'] = format_edi_date(dtp.get('DTM02', ''))
            elif dtp.get('DTM01') == 'D8':
                line['serviceDateTo'] = format_edi_date(dtp.get('DTM02', ''))

        # Extract service-level adjustments
        svc_cas = find_all_segments(svc, 'CAS')
        svc_adjustments = []

        for cas in svc_cas:
            group_code = cas.get('CAS01', '')
            group = GROUP_CODE_MAP.get(group_code, group_code)

            for i in range(1, 7):
                reason_field = f'CAS{i*3-1:02d}'
                amount_field = f'CAS{i*3:02d}'

                reason_code = cas.get(reason_field, '')
                amount = safe_float(cas.get(amount_field))

                if not reason_code:
                    break

                svc_adjustments.append({
                    'group': group,
                    'reasonCode': reason_code,
                    'reason': create_code_object('CARC', reason_code, desc=lookup_carc_description(reason_code)),
                    'amount': amount
                })

        if svc_adjustments:
            line['adjustments'] = svc_adjustments

        # Extract supplemental amounts
        amt_segments = find_all_segments(svc, 'AMT')
        if amt_segments:
            supplemental_amounts = []
            for amt in amt_segments:
                qualifier = amt.get('AMT01', '')
                amount = safe_float(amt.get('AMT02'))

                type_map = {
                    'B6': 'ALLOWED_ACTUAL',
                    'KH': 'DEDUCTION'
                }

                supplemental_amounts.append({
                    'qualifierCode': qualifier,
                    'type': type_map.get(qualifier, qualifier),
                    'amount': amount
                })

            line['supplementalAmounts'] = supplemental_amounts

        # Extract supplemental quantities
        qty_segments = find_all_segments(svc, 'QTY')
        if qty_segments:
            supplemental_quantities = []
            for qty in qty_segments:
                qualifier = qty.get('QTY01', '')
                quantity = safe_float(qty.get('QTY02'))

                type_map = {
                    'ZL': 'MEDICARE_MEDICAID_CAT_2'
                }

                supplemental_quantities.append({
                    'qualifierCode': qualifier,
                    'type': type_map.get(qualifier, qualifier),
                    'quantity': quantity
                })

            line['supplementalQuantities'] = supplemental_quantities

        # Extract line-level reference IDs
        ref_segments = find_all_segments(svc, 'REF')
        if ref_segments:
            service_ids = []
            for ref in ref_segments:
                qualifier = ref.get('REF01', '')
                identification = ref.get('REF02', '')

                type_map = {
                    'RB': 'RATE_CODE_NUMBER',
                    '1S': 'APG_NUMBER',
                    'APC': 'AMBULATORY_PAYMENT'
                }

                service_ids.append({
                    'qualifierCode': qualifier,
                    'type': type_map.get(qualifier, qualifier),
                    'identification': identification
                })

            line['serviceIds'] = service_ids

        # Extract remark codes (LQ segments)
        lq_segments = find_all_segments(svc, 'LQ')
        if lq_segments:
            remark_codes = []
            remarks = []

            for lq in lq_segments:
                code = lq.get('LQ02', '')
                if code:
                    remark_codes.append(code)
                    remarks.append(create_code_object(
                        'RARC',
                        code,
                        desc=lookup_rarc_description(code)
                    ))

            if remark_codes:
                line['remarkCodes'] = remark_codes
            if remarks:
                line['remarks'] = remarks

        # Extract rendering provider IDs at line level
        # (NM1 with 82 under SVC, or REF segments)
        rendering_ids = []
        ref_segments = find_all_segments(svc, 'REF')
        for ref in ref_segments:
            qualifier = ref.get('REF01', '')
            if qualifier in ['HPI', '1C']:
                type_map = {
                    'HPI': 'CMS_NPI',
                    '1C': 'MEDICARE_PROVIDER_NUMBER'
                }

                rendering_ids.append({
                    'qualifierCode': qualifier,
                    'type': type_map.get(qualifier, qualifier),
                    'identification': ref.get('REF02', '')
                })

        if rendering_ids:
            line['renderingProviderIds'] = rendering_ids

        service_lines.append(line)

    if service_lines:
        payment['serviceLines'] = service_lines

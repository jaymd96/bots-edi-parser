"""
Browser-based EDI Parser using PyScript
"""
import json
from js import document, console
from pyodide.ffi import create_proxy

# Sample EDI data
SAMPLE_837 = """ISA*00*          *00*          *ZZ*SUBMITTERS.ID  *ZZ*RECEIVERS.ID   *050516*0932*^*00501*000000001*0*T*:~
GS*HC*SENDER*RECEIVER*20050516*0932*1*X*005010X222A1~
ST*837*0001*005010X222A1~
BHT*0019*00*36463774*20050516*1200*CH~
NM1*41*2*PREMIER BILLING SERVICE*****46*TGJ23~
PER*IC*JERRY*TE*3055552222*EX*231~
NM1*40*2*KEY INSURANCE COMPANY*****46*66783JJT~
HL*1**20*1~
PRV*BI*PXC*203BF0100Y~
NM1*85*2*PREMIER BILLING SERVICE*****XX*1234567893~
N3*1234 SEAWAY ST~
N4*MIAMI*FL*33111~
REF*EI*587654321~
HL*2*1*22*0~
SBR*P*18*******CI~
NM1*IL*1*SMITH*JOHN****MI*JS00111223999~
N3*236 N MAIN ST~
N4*MIAMI*FL*33413~
DMG*D8*19430501*M~
NM1*PR*2*KEY INSURANCE COMPANY*****PI*999996666~
CLM*36463774*100***11:B:1*Y*A*Y*Y~
HI*ABK:J0300*ABF:J0310*ABF:J0320*ABF:J0330*ABF:J0340~
LX*1~
SV1*HC:99299:26:27:28:29*40*UN*1***1~
DTP*472*D8*20050325~
LX*2~
SV1*HC:87070*15*UN*1***1~
DTP*472*D8*20050325~
LX*3~
SV1*HC:99213*35*UN*1***1~
DTP*472*D8*20050325~
LX*4~
SV1*HC:86663*10*UN*1***2~
DTP*472*D8*20050325~
NM1*82*1*DOE*JANE****XX*1234567804~
PRV*PE*PXC*000000000X~
SE*39*0001~
GE*1*1~
IEA*1*000000001~"""

SAMPLE_835 = """ISA*00*          *00*          *ZZ*PAYER ID       *ZZ*RECEIVER ID    *250409*1200*^*00501*000000001*0*P*:~
GS*HP*PAYER*RECEIVER*20250409*1200*1*X*005010X221A1~
ST*835*0001*005010X221A1~
BPR*I*132*C*ACH*CCP*01*011900449*DA*0000009999*0106609999**01*107001235*DA*2200008888*20250409~
TRN*1*882509401093167*1234567890~
DTM*405*20250409~
N1*PR*INSURANCE COMPANY~
N3*PO BOX 12345~
N4*CITY*ST*12345~
REF*2U*99999~
N1*PE*PROVIDER NAME*XX*1234567890~
LX*1~
CLP*CLAIM001*1*100000*68000*32000**12345678901234567*11~
CAS*CO*197*30000*45*2000~
NM1*QC*1*PATIENT*JOHN~
DTM*232*20250101~
AMT*AU*100000~
SVC*HC:99213*100*68*32**1~
CAS*CO*132*30~
CAS*PR*3*2~
DTM*472*20250101~
LX*2~
CLP*CLAIM002*1*50*40*10**12345678901234568*11~
CAS*OA*131*10~
NM1*QC*1*DOE*JANE~
AMT*AU*50~
SVC*HC:87070*50*40*10**1~
CAS*OA*131*10~
DTM*472*20250102~
SE*28*0001~
GE*1*1~
IEA*1*000000001~"""


def parse_edi():
    """Parse EDI and transform to Foundry ontology"""
    try:
        # Show loading
        output_content = document.getElementById('output-content')
        output_content.innerHTML = '<div class="loading"><h3>⚙️ Parsing EDI...</h3></div>'

        # Get input
        edi_input = document.getElementById('edi-input').value.strip()
        transaction_type = document.getElementById('transaction-type').value

        if not edi_input:
            output_content.innerHTML = '<div class="error">❌ Please paste EDI content first</div>'
            return

        # For now, show a simple parse of the structure
        # We'll implement full parsing once we load the edi_parser module
        result = simple_parse(edi_input, transaction_type)

        # Show results
        display_results(result, transaction_type)

    except Exception as e:
        console.error(str(e))
        output_content = document.getElementById('output-content')
        output_content.innerHTML = f'<div class="error">❌ Error: {str(e)}</div>'


def simple_parse(edi_content, transaction_type):
    """Simple EDI parser that extracts segments"""
    lines = edi_content.strip().split('~')
    segments = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split('*')
        if parts:
            segment_id = parts[0]
            fields = parts[1:] if len(parts) > 1 else []
            segments.append({
                'id': segment_id,
                'fields': fields,
                'raw': line
            })

    # Extract basic info based on transaction type
    if transaction_type == '837':
        return parse_837_simple(segments)
    else:
        return parse_835_simple(segments)


def parse_837_simple(segments):
    """Simple 837P parser"""
    result = {
        'claims': [],
        'services': [],
        'diagnoses': [],
        'providers': [],
        'payers': [],
        'segments': segments
    }

    claim = {}
    services = []

    for seg in segments:
        sid = seg['id']
        fields = seg['fields']

        if sid == 'CLM' and len(fields) >= 2:
            if claim:  # Save previous claim
                result['claims'].append(claim)
            claim = {
                'claim_id': fields[0],
                'total_charge': fields[1],
                'services': []
            }

        elif sid == 'SV1' and claim and len(fields) >= 2:
            service = {
                'procedure_code': fields[0].split(':')[1] if ':' in fields[0] else fields[0],
                'charge': fields[1]
            }
            claim['services'].append(service)
            result['services'].append(service)

        elif sid == 'HI' and claim:
            for i, field in enumerate(fields):
                if ':' in field:
                    parts = field.split(':')
                    result['diagnoses'].append({
                        'type': parts[0],
                        'code': parts[1] if len(parts) > 1 else ''
                    })

        elif sid == 'NM1' and len(fields) >= 3:
            entity_type = fields[0]
            if entity_type in ['82', '85']:  # Provider
                result['providers'].append({
                    'type': 'Rendering' if entity_type == '82' else 'Billing',
                    'name': fields[2] if len(fields) > 2 else '',
                    'npi': fields[8] if len(fields) > 8 else ''
                })
            elif entity_type == 'PR':  # Payer
                result['payers'].append({
                    'name': fields[2] if len(fields) > 2 else '',
                    'id': fields[8] if len(fields) > 8 else ''
                })

    if claim:
        result['claims'].append(claim)

    return result


def parse_835_simple(segments):
    """Simple 835 parser"""
    result = {
        'denials': [],
        'reason_codes': set(),
        'segments': segments,
        'payment_info': {}
    }

    for seg in segments:
        sid = seg['id']
        fields = seg['fields']

        if sid == 'BPR' and len(fields) >= 2:
            result['payment_info'] = {
                'amount': fields[1],
                'method': fields[3] if len(fields) > 3 else '',
                'date': fields[15] if len(fields) > 15 else ''
            }

        elif sid == 'CAS' and len(fields) >= 3:
            denial_type = fields[0]
            denial_type_map = {
                'CO': 'Contractual Obligation',
                'PR': 'Patient Responsibility',
                'OA': 'Other Adjustment',
                'PI': 'Payer Initiated'
            }

            # Extract reason codes and amounts
            i = 1
            while i < len(fields) - 1:
                reason = fields[i] if i < len(fields) else ''
                amount = fields[i+1] if i+1 < len(fields) else '0'

                if reason:
                    result['denials'].append({
                        'type': denial_type_map.get(denial_type, denial_type),
                        'reason_code': reason,
                        'amount': amount
                    })
                    result['reason_codes'].add(reason)

                i += 3  # Skip to next triplet (reason, amount, quantity)

    result['reason_codes'] = sorted(list(result['reason_codes']))
    return result


def display_results(result, transaction_type):
    """Display parsed results in the UI"""
    # Show tabs
    tabs = document.getElementById('output-tabs')
    tabs.style.display = 'flex'

    # Create summary
    summary_html = create_summary(result, transaction_type)
    document.getElementById('tab-summary').innerHTML = summary_html

    # Create JSON view
    json_html = f'<pre>{json.dumps(result, indent=2, default=str)}</pre>'
    document.getElementById('tab-json').innerHTML = json_html

    # Create tables view
    tables_html = create_tables(result, transaction_type)
    document.getElementById('tab-tables').innerHTML = tables_html

    # Show summary tab by default
    document.getElementById('tab-summary').classList.add('active')
    document.getElementById('output-content').innerHTML = ''


def create_summary(result, transaction_type):
    """Create summary statistics"""
    if transaction_type == '837':
        return f"""
        <div class="stat-card">
            <h3>📋 Claims</h3>
            <div class="value">{len(result.get('claims', []))}</div>
        </div>
        <div class="stat-card">
            <h3>💉 Services</h3>
            <div class="value">{len(result.get('services', []))}</div>
        </div>
        <div class="stat-card">
            <h3>🏥 Diagnoses</h3>
            <div class="value">{len(result.get('diagnoses', []))}</div>
        </div>
        <div class="stat-card">
            <h3>👨‍⚕️ Providers</h3>
            <div class="value">{len(result.get('providers', []))}</div>
        </div>
        <div class="stat-card">
            <h3>💳 Payers</h3>
            <div class="value">{len(result.get('payers', []))}</div>
        </div>
        """
    else:
        total_denied = sum(float(d.get('amount', 0)) for d in result.get('denials', []))
        return f"""
        <div class="stat-card">
            <h3>💰 Payment Amount</h3>
            <div class="value">${result.get('payment_info', {}).get('amount', '0')}</div>
        </div>
        <div class="stat-card">
            <h3>❌ Total Denials</h3>
            <div class="value">{len(result.get('denials', []))}</div>
        </div>
        <div class="stat-card">
            <h3>💸 Total Denied Amount</h3>
            <div class="value">${total_denied:.2f}</div>
        </div>
        <div class="stat-card">
            <h3>📝 Unique Reason Codes</h3>
            <div class="value">{len(result.get('reason_codes', []))}</div>
        </div>
        """


def create_tables(result, transaction_type):
    """Create table views of the data"""
    html = ""

    if transaction_type == '837':
        # Claims table
        if result.get('claims'):
            html += '<h3>Claims</h3><table><thead><tr><th>Claim ID</th><th>Total Charge</th><th>Services</th></tr></thead><tbody>'
            for claim in result['claims']:
                html += f"<tr><td>{claim.get('claim_id', '')}</td><td>${claim.get('total_charge', '0')}</td><td>{len(claim.get('services', []))}</td></tr>"
            html += '</tbody></table>'

        # Services table
        if result.get('services'):
            html += '<h3 style="margin-top: 20px;">Services</h3><table><thead><tr><th>Procedure Code</th><th>Charge</th></tr></thead><tbody>'
            for svc in result['services']:
                html += f"<tr><td>{svc.get('procedure_code', '')}</td><td>${svc.get('charge', '0')}</td></tr>"
            html += '</tbody></table>'

        # Diagnoses table
        if result.get('diagnoses'):
            html += '<h3 style="margin-top: 20px;">Diagnoses</h3><table><thead><tr><th>Type</th><th>Code</th></tr></thead><tbody>'
            for dx in result['diagnoses']:
                html += f"<tr><td>{dx.get('type', '')}</td><td>{dx.get('code', '')}</td></tr>"
            html += '</tbody></table>'

    else:  # 835
        # Denials table
        if result.get('denials'):
            html += '<h3>Denials</h3><table><thead><tr><th>Type</th><th>Reason Code</th><th>Amount</th></tr></thead><tbody>'
            for denial in result['denials']:
                html += f"<tr><td>{denial.get('type', '')}</td><td>{denial.get('reason_code', '')}</td><td>${denial.get('amount', '0')}</td></tr>"
            html += '</tbody></table>'

    return html if html else '<p>No data to display</p>'


def load_sample_837():
    """Load sample 837P data"""
    document.getElementById('edi-input').value = SAMPLE_837
    document.getElementById('transaction-type').value = '837'


def load_sample_835():
    """Load sample 835 data"""
    document.getElementById('edi-input').value = SAMPLE_835
    document.getElementById('transaction-type').value = '835'


def clear_all():
    """Clear all inputs and outputs"""
    document.getElementById('edi-input').value = ''
    document.getElementById('output-content').innerHTML = '<div class="loading"><h3>Ready to parse!</h3><p>Paste EDI content and click Transform</p></div>'
    tabs = document.getElementById('output-tabs')
    tabs.style.display = 'none'


# Make functions available to HTML onclick handlers
import builtins
builtins.parse_edi = parse_edi
builtins.load_sample_837 = load_sample_837
builtins.load_sample_835 = load_sample_835
builtins.clear_all = clear_all

"""
Browser-based EDI Parser using PyScript

Transforms EDI files into structured ontology schemas using the real edi_parser library.
"""
import json
from js import document, console

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
    """Parse EDI and transform to structured ontology"""
    try:
        # Import the actual edi_parser library
        try:
            from edi_parser import parse_edi, add_human_readable_names, transform_837p, transform_835
        except ImportError as e:
            console.error(f"Failed to import edi_parser: {e}")
            output_content = document.getElementById('output-content')
            output_content.innerHTML = f'<div class="error">❌ Failed to load edi_parser library: {str(e)}</div>'
            return

        # Show loading
        output_content = document.getElementById('output-content')
        output_content.innerHTML = '<div class="loading"><h3>⚙️ Parsing EDI...</h3></div>'

        # Get input
        edi_input = document.getElementById('edi-input').value.strip()
        transaction_type = document.getElementById('transaction-type').value

        if not edi_input:
            output_content.innerHTML = '<div class="error">❌ Please paste EDI content first</div>'
            return

        # Parse with actual edi_parser
        console.log("Parsing EDI with edi_parser library...")
        result = parse_edi(
            content=edi_input.encode('utf-8'),
            editype='x12',
            messagetype='envelope',
            charset='utf-8'
        )

        if not result.get('success'):
            errors = result.get('errors', ['Unknown error'])
            output_content.innerHTML = f'<div class="error">❌ Parse error: {", ".join(errors)}</div>'
            return

        console.log("Adding human-readable names...")
        readable = add_human_readable_names(
            result['data'],
            transaction=transaction_type,
            version='5010',
            mode='dual'
        )

        # Transform to ontology
        console.log("Transforming to ontology...")
        if transaction_type == '837':
            ontology = transform_837p(readable, source_filename='browser_input.txt')
        else:
            ontology = transform_835(readable)

        # Show results
        display_results(ontology, transaction_type)

    except Exception as e:
        console.error(f"Error: {e}")
        import traceback
        console.error(traceback.format_exc())
        output_content = document.getElementById('output-content')
        output_content.innerHTML = f'<div class="error">❌ Error: {str(e)}</div>'


def display_results(ontology, transaction_type):
    """Display ontology results in the UI"""
    # Show tabs
    tabs = document.getElementById('output-tabs')
    tabs.style.display = 'flex'

    # Create summary
    summary_html = create_summary(ontology, transaction_type)
    document.getElementById('tab-summary').innerHTML = summary_html

    # Create JSON view
    json_html = f'<pre>{json.dumps(ontology, indent=2, default=str)}</pre>'
    document.getElementById('tab-json').innerHTML = json_html

    # Create tables view
    tables_html = create_tables(ontology, transaction_type)
    document.getElementById('tab-tables').innerHTML = tables_html

    # Show summary tab by default
    document.getElementById('tab-summary').classList.add('active')
    document.getElementById('output-content').innerHTML = ''


def create_summary(ontology, transaction_type):
    """Create summary statistics"""
    if transaction_type == '837':
        return f"""
        <div class="stat-card">
            <h3>📋 Claims</h3>
            <div class="value">{len(ontology.get('claims', []))}</div>
        </div>
        <div class="stat-card">
            <h3>💉 Services</h3>
            <div class="value">{len(ontology.get('services', []))}</div>
        </div>
        <div class="stat-card">
            <h3>🏥 Diagnoses</h3>
            <div class="value">{len(ontology.get('diagnoses', []))}</div>
        </div>
        <div class="stat-card">
            <h3>👨‍⚕️ Providers</h3>
            <div class="value">{len(ontology.get('providers', []))}</div>
        </div>
        <div class="stat-card">
            <h3>💳 Payers</h3>
            <div class="value">{len(ontology.get('payers', []))}</div>
        </div>
        """
    else:
        total_denied = sum(float(d.get('total_denied', 0)) for d in ontology.get('denials', []))
        return f"""
        <div class="stat-card">
            <h3>❌ Total Denials</h3>
            <div class="value">{len(ontology.get('denials', []))}</div>
        </div>
        <div class="stat-card">
            <h3>💸 Total Denied Amount</h3>
            <div class="value">${total_denied:.2f}</div>
        </div>
        <div class="stat-card">
            <h3>📝 Unique Reason Codes</h3>
            <div class="value">{len(ontology.get('reason_codes', []))}</div>
        </div>
        """


def create_tables(ontology, transaction_type):
    """Create table views of the data"""
    html = ""

    if transaction_type == '837':
        # Claims table
        if ontology.get('claims'):
            html += '<h3>Claims</h3><table><thead><tr><th>Claim ID</th><th>Patient</th><th>Total Charge</th><th>Services</th></tr></thead><tbody>'
            for claim in ontology['claims'][:10]:  # Limit to 10 for display
                patient = f"{claim.get('patient_first_name', '')} {claim.get('patient_last_name', '')}"
                html += f"<tr><td>{claim.get('claim_id', '')[:16]}...</td><td>{patient}</td><td>${claim.get('total_charge', 0)}</td><td>{len([s for s in ontology.get('services', []) if s.get('claim_id') == claim.get('claim_id')])}</td></tr>"
            html += '</tbody></table>'

        # Services table
        if ontology.get('services'):
            html += '<h3 style="margin-top: 20px;">Services (showing first 10)</h3><table><thead><tr><th>Procedure Code</th><th>Charge</th><th>Units</th><th>Date</th></tr></thead><tbody>'
            for svc in ontology['services'][:10]:
                html += f"<tr><td>{svc.get('procedure_code', '')}</td><td>${svc.get('charge_amount', 0)}</td><td>{svc.get('units', 0)}</td><td>{svc.get('service_date', '')}</td></tr>"
            html += '</tbody></table>'

        # Diagnoses table
        if ontology.get('diagnoses'):
            html += '<h3 style="margin-top: 20px;">Diagnoses (showing first 10)</h3><table><thead><tr><th>Type</th><th>Code</th></tr></thead><tbody>'
            for dx in ontology['diagnoses'][:10]:
                html += f"<tr><td>{dx.get('diagnosis_type', '')}</td><td>{dx.get('diagnosis_code', '')}</td></tr>"
            html += '</tbody></table>'

    else:  # 835
        # Denials table
        if ontology.get('denials'):
            html += '<h3>Denials</h3><table><thead><tr><th>Type</th><th>Reason Code</th><th>Amount</th><th>Appeal Deadline</th></tr></thead><tbody>'
            for denial in ontology['denials']:
                html += f"<tr><td>{denial.get('denial_type', '')}</td><td>{denial.get('primary_reason_code', '')}</td><td>${denial.get('total_denied', 0)}</td><td>{denial.get('appeal_deadline', '')}</td></tr>"
            html += '</tbody></table>'

        # Reason codes
        if ontology.get('reason_codes'):
            html += '<h3 style="margin-top: 20px;">Reason Codes</h3><table><thead><tr><th>Code</th><th>Description</th><th>Typical Action</th></tr></thead><tbody>'
            for rc in ontology['reason_codes']:
                html += f"<tr><td>{rc.get('reason_code', '')}</td><td>{rc.get('description', '')}</td><td>{rc.get('typical_action', '')}</td></tr>"
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

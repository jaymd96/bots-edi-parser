"""
Browser-based EDI Parser using PyScript

Transforms EDI files into structured ontology schemas using the real edi_parser library.
"""
import json
from js import document, console

# Try to import the package - it should be pre-installed by PyScript
try:
    from edi_parser import parse_edi as parse_edi_content, add_human_readable_names, transform_837p, transform_835
    console.log("edi_parser loaded successfully!")
except ImportError as e:
    console.error(f"Failed to import edi_parser: {e}")
    console.log("Package should be installed via pyscript.toml")

# Sample EDI data - Real 837P that parses correctly
SAMPLE_837 = """ISA*00*          *00*          *ZZ*123456789012345*ZZ*123456789012346*061015*1705*>*00501*000010216*0*T*:~
GS*HC*1234567890*9876543210*20061015*1705*20213*X*005010X222A1~
ST*837*0031*005010X222A1~
BHT*0019*00*0031*20061015*1023*CH~
NM1*41*2*PREMIER BILLING SERVICE*****46*TGJ23~
PER*IC*JERRY*TE*3055552222*EX*231~
NM1*40*2*KEY INSURANCE COMPANY*****46*66783JJT~
HL*1**20*1~
PRV*BI*PXC*203BF0100Y~
NM1*85*2*BEN KILDARE SERVICE*****XX*9876543210~
N3*234 SEAWAY ST~
N4*MIAMI*FL*33111~
REF*EI*587654321~
HL*2*1*22*1~
SBR*P**2222-SJ******CI~
NM1*IL*1*SMITH*JANE****MI*JS00111223333~
N3*236 N MAIN ST~
N4*MIAMI*FL*33413~
DMG*D8*19430501*F~
NM1*PR*2*KEY INSURANCECOMPANY*****PI*999996666~
HL*3*2*23*0~
NM1*QC*1*SMITH*TED~
CLM*36463774*100***11:B:1*Y*A*Y*Y~
HI*ABK:J0300*ABF:Z1159~
LX*1~
SV1*HC:99299:26:27:28:29*40*UN*1*11**1:2~
DTP*472*RD8*20050314-20050325~
LX*2~
SV1*HC:87099*15*UN*1***1~
DTP*472*D8*20061003~
LX*3~
SV1*HC:99214*35*UN*1***2~
LX*4~
SV1*HC:86663*10*UN*1***2~
DTP*472*D8*20061010~
SE*34*0031~
GE*1*20213~
IEA*1*000010216~"""

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
SVC*HC:99213*100*68*32**1:2~
CAS*CO*132*30~
CAS*PR*3*2~
DTM*472*20250101~
LX*2~
CLP*CLAIM002*1*50*40*10**12345678901234568*11~
CAS*OA*131*10~
NM1*QC*1*DOE*JANE~
AMT*AU*50~
SVC*HC:87070*50*40*10**1:2~
CAS*OA*131*10~
DTM*472*20250102~
SE*28*0001~
GE*1*1~
IEA*1*000000001~"""


def parse_edi():
    """Parse EDI and transform to structured ontology"""
    try:
        # Get input
        edi_input = document.getElementById('edi-input').value.strip()
        transaction_type = document.getElementById('transaction-type').value

        if not edi_input:
            document.getElementById('tab-parsed').innerHTML = '<article class="error"><p>Please paste EDI content first</p></article>'
            return

        # Show loading in first tab
        document.getElementById('tab-parsed').innerHTML = '<article><p>Parsing EDI...</p></article>'

        # Parse with actual edi_parser - use lenient validation
        console.log("Parsing EDI with edi_parser library...")
        result = parse_edi_content(
            content=edi_input.encode('utf-8'),
            editype='x12',
            messagetype='envelope',
            charset='utf-8',
            field_validation_mode='lenient',  # Continue on field validation errors
            checkunknownentities=False  # Don't fail on unknown fields
        )

        # Collect warnings
        warnings = result.get('warnings', [])
        errors = result.get('errors', [])

        if not result.get('success'):
            # Show error but also show any partial data if available
            error_html = '<article class="error"><header><strong>Parse Errors</strong></header><ul>'
            for err in errors:
                error_html += f'<li>{err}</li>'
            error_html += '</ul></article>'

            # If we have warnings, show them too
            if warnings:
                error_html += '<article class="warning"><header><strong>Warnings</strong></header><ul>'
                for warn in warnings:
                    error_html += f'<li>{warn}</li>'
                error_html += '</ul></article>'

            document.getElementById('tab-parsed').innerHTML = error_html
            return

        # Show warnings if any
        warning_html = ''
        if warnings:
            warning_html = '<article class="warning"><header><strong>Parsing Warnings</strong></header><ul>'
            for warn in warnings:
                warning_html += f'<li>{warn}</li>'
            warning_html += '</ul></article>'

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

        # Show results (with warnings if any)
        display_results(result['data'], readable, ontology, transaction_type, warning_html)

    except Exception as e:
        console.error(f"Error: {e}")
        import traceback
        console.error(traceback.format_exc())
        document.getElementById('tab-parsed').innerHTML = f'<article class="error"><header><strong>Error</strong></header><p>{str(e)}</p></article>'


def display_results(parsed_data, readable_data, ontology, transaction_type, warning_html=''):
    """Display the three JSON outputs in the UI"""
    # Create Parsed JSON view
    parsed_html = warning_html + f'<pre>{json.dumps(parsed_data, indent=2, default=str)}</pre>'
    document.getElementById('tab-parsed').innerHTML = parsed_html

    # Create Human-Readable JSON view
    readable_html = warning_html + f'<pre>{json.dumps(readable_data, indent=2, default=str)}</pre>'
    document.getElementById('tab-readable').innerHTML = readable_html

    # Create Ontology JSON view
    ontology_html = warning_html + f'<pre>{json.dumps(ontology, indent=2, default=str)}</pre>'
    document.getElementById('tab-ontology').innerHTML = ontology_html


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
    document.getElementById('tab-parsed').innerHTML = '<article><p>Paste your 837P or 835 EDI file in the left panel and click "Transform" to see the structured output.</p></article>'
    document.getElementById('tab-readable').innerHTML = ''
    document.getElementById('tab-ontology').innerHTML = ''

    # Show first tab
    document.getElementById('tab-parsed').classList.add('active')
    document.getElementById('tab-readable').classList.remove('active')
    document.getElementById('tab-ontology').classList.remove('active')


# Make functions available to HTML onclick handlers
from pyscript import when

# Set up event listeners
@when("click", "#parse-btn")
def on_parse_click(event):
    parse_edi()

@when("click", "#clear-btn")
def on_clear_click(event):
    clear_all()

@when("click", ".sample-link")
def on_sample_click(event):
    event.preventDefault()
    link_text = event.target.textContent
    if "837" in link_text:
        load_sample_837()
    elif "835" in link_text:
        load_sample_835()

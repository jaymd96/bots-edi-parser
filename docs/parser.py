"""
Browser-based EDI Parser using PyScript

Transforms EDI files into structured ontology schemas using the real edi_parser library.
"""
import json
from js import document, console, fetch
from pyodide.ffi import to_js

# Try to import the package - it should be pre-installed by PyScript
try:
    from edi_parser import (
        parse_edi as parse_edi_content,
        validate_edi as validate_edi_content,
        add_human_readable_names,
        transform_837p,
        transform_835
    )
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
    """Parse EDI with validation and transform to structured ontology"""
    try:
        # Get input
        edi_input = document.getElementById('edi-input').value.strip()
        transaction_type = document.getElementById('transaction-type').value

        if not edi_input:
            document.getElementById('tab-validation').innerHTML = '<article class="error"><p>Please paste EDI content first</p></article>'
            return

        # Show loading
        document.getElementById('tab-validation').innerHTML = '<article><p>Validating and parsing EDI...</p></article>'

        # Determine messagetype from content
        messagetype = f'{transaction_type}005010'

        console.log(f"Step 1: Validating with messagetype {messagetype}...")

        # First run validation to get structured errors (lenient mode - warnings don't fail)
        validation_result = validate_edi_content(
            content=edi_input.encode('utf-8'),
            editype='x12',
            messagetype=messagetype,
            charset='utf-8',
            validation_mode='lenient'  # Allow warnings to pass
        )

        console.log("Step 2: Parsing in lenient mode...")

        # Then parse in lenient mode to extract data regardless
        parse_result = parse_edi_content(
            content=edi_input.encode('utf-8'),
            editype='x12',
            messagetype=messagetype,
            charset='utf-8',
            field_validation_mode='lenient',
            continue_on_error=True
        )

        # Display validation results
        display_validation(validation_result, parse_result)

        # If parse succeeded, also show transformed data
        if parse_result.get('success') and parse_result.get('data'):
            console.log("Step 3: Adding human-readable names...")
            readable = add_human_readable_names(
                parse_result['data'],
                transaction=transaction_type,
                version='5010',
                mode='dual'
            )

            console.log("Step 4: Transforming to ontology...")
            if transaction_type == '837':
                ontology = transform_837p(readable, source_filename='browser_input.txt')
            else:
                ontology = transform_835(readable)

            # Display data tabs
            display_data_tabs(parse_result['data'], readable, ontology)
        else:
            # Clear data tabs if parse failed
            document.getElementById('tab-parsed').innerHTML = '<article><p>Parse failed - no data extracted</p></article>'
            document.getElementById('tab-readable').innerHTML = ''
            document.getElementById('tab-ontology').innerHTML = ''

    except Exception as e:
        console.error(f"Error: {e}")
        import traceback
        console.error(traceback.format_exc())
        document.getElementById('tab-validation').innerHTML = f'<article class="error"><header><strong>Error</strong></header><p>{str(e)}</p><pre>{traceback.format_exc()}</pre></article>'


def display_validation(validation_result, parse_result):
    """Display validation errors and parse status"""
    html = ''

    # Parse status
    if parse_result.get('success'):
        html += '<article class="success"><header><strong>✓ Parse Successful (Lenient Mode)</strong></header>'
        html += '<p>Data was successfully extracted from the EDI file. Check the other tabs for parsed data.</p>'
        html += '</article>'
    else:
        html += '<article class="error"><header><strong>✗ Parse Failed</strong></header>'
        html += '<p>Unable to extract data from the EDI file even in lenient mode.</p>'
        if parse_result.get('errors'):
            html += '<ul>'
            for err in parse_result.get('errors', [])[:5]:
                html += f'<li>{err}</li>'
            html += '</ul>'
        html += '</article>'

    # Validation status
    if validation_result.get('valid'):
        # Check if there are warnings even though validation passed
        total_issues = len(validation_result.get('errors', []))
        if total_issues > 0:
            html += f'<article class="warning"><header><strong>✓ Validation Passed (Lenient Mode)</strong></header>'
            html += f'<p>The EDI file passed validation in lenient mode with {total_issues} warning(s). These warnings are informational and do not block processing.</p>'
            html += '</article>'
        else:
            html += '<article class="success"><header><strong>✓ Validation Passed</strong></header>'
            html += '<p>The EDI file is valid with no errors or warnings.</p>'
            html += '</article>'
    else:
        error_count = validation_result.get('error_count', 0)
        html += f'<article class="error"><header><strong>✗ Found {error_count} Validation Error(s)</strong></header>'
        html += '<p>The file has critical errors or validation issues that prevent processing.</p>'
        html += '</article>'

    # Show structured errors/warnings (for both pass and fail)
    errors = validation_result.get('errors', [])
    if errors:
        # Label changes based on validation result
        issues_label = 'Warnings' if validation_result.get('valid') else 'Validation Errors'
        html += f'<h3>{issues_label}:</h3>'

        # Group by category
        errors_by_category = {}
        for error in errors:
            cat = error.get('category', 'unknown')
            if cat not in errors_by_category:
                errors_by_category[cat] = []
            errors_by_category[cat].append(error)

        # Display by category
        for category, cat_errors in sorted(errors_by_category.items()):
            html += f'<h4>{category.replace("_", " ").title()} ({len(cat_errors)} issue(s))</h4>'

            for i, error in enumerate(cat_errors[:10], 1):  # Show max 10 per category
                html += '<div class="validation-error">'
                html += f'<h4>Issue {i}: [{error.get("code", "N/A")}] {error.get("severity", "error").upper()}</h4>'
                html += '<dl class="error-details">'

                if error.get('description'):
                    html += f'<dt>Description:</dt><dd>{error["description"]}</dd>'

                location = error.get('location', {})
                if location.get('segment'):
                    loc_parts = []
                    if location.get('line'):
                        loc_parts.append(f"Line {location['line']}")
                    if location.get('segment'):
                        loc_parts.append(f"Segment {location['segment']}")
                    if location.get('field'):
                        loc_parts.append(f"Field {location['field']}")
                    html += f'<dt>Location:</dt><dd>{", ".join(loc_parts)}</dd>'

                if location.get('path'):
                    html += f'<dt>Path:</dt><dd>{location["path"]}</dd>'

                if error.get('value'):
                    html += f'<dt>Value:</dt><dd>"{error["value"]}"</dd>'

                if error.get('expected'):
                    html += f'<dt>Expected:</dt><dd>{error["expected"]}</dd>'

                if error.get('actual'):
                    html += f'<dt>Actual:</dt><dd>{error["actual"]}</dd>'

                if error.get('suggestion'):
                    html += f'<dt>💡 Suggestion:</dt><dd>{error["suggestion"]}</dd>'

                html += '</dl></div>'

            if len(cat_errors) > 10:
                html += f'<p><small>... and {len(cat_errors) - 10} more {category} issues</small></p>'

    document.getElementById('tab-validation').innerHTML = html


def display_data_tabs(parsed_data, readable_data, ontology):
    """Display the three JSON outputs in the data tabs"""
    # Create Parsed JSON view
    parsed_html = f'<pre>{json.dumps(parsed_data, indent=2, default=str)}</pre>'
    document.getElementById('tab-parsed').innerHTML = parsed_html

    # Create Human-Readable JSON view
    readable_html = f'<pre>{json.dumps(readable_data, indent=2, default=str)}</pre>'
    document.getElementById('tab-readable').innerHTML = readable_html

    # Create Ontology JSON view
    ontology_html = f'<pre>{json.dumps(ontology, indent=2, default=str)}</pre>'
    document.getElementById('tab-ontology').innerHTML = ontology_html


async def load_test_file():
    """Load a test file from the repository"""
    try:
        selected = document.getElementById('file-selector').value
        if not selected:
            return

        # GitHub raw URL for test files
        base_url = 'https://raw.githubusercontent.com/jaymd96/bots-edi-parser/main/test_files/'
        file_url = base_url + selected

        console.log(f"Loading file from: {file_url}")

        # Fetch the file
        response = await fetch(file_url)
        if response.ok:
            content = await response.text()
            document.getElementById('edi-input').value = content

            # Set transaction type based on file
            if selected.startswith('835'):
                document.getElementById('transaction-type').value = '835'
            else:
                document.getElementById('transaction-type').value = '837'

            console.log(f"Loaded {len(content)} characters")
        else:
            console.error(f"Failed to load file: {response.status}")
            document.getElementById('edi-input').value = f"Error loading file: {response.status}"

    except Exception as e:
        console.error(f"Error loading file: {e}")
        document.getElementById('edi-input').value = f"Error: {str(e)}"


def clear_all():
    """Clear all inputs and outputs"""
    document.getElementById('edi-input').value = ''
    document.getElementById('file-selector').value = ''
    document.getElementById('tab-validation').innerHTML = '<article><p>Select a test file or paste your EDI content in the left panel, then click "Transform" to see validation results and structured output.</p></article>'
    document.getElementById('tab-parsed').innerHTML = ''
    document.getElementById('tab-readable').innerHTML = ''
    document.getElementById('tab-ontology').innerHTML = ''

    # Show first tab
    document.getElementById('tab-validation').classList.add('active')
    document.getElementById('tab-parsed').classList.remove('active')
    document.getElementById('tab-readable').classList.remove('active')
    document.getElementById('tab-ontology').classList.remove('active')


# Make functions available to HTML onclick handlers
from pyscript import when
import asyncio

# Set up event listeners
@when("click", "#parse-btn")
def on_parse_click(event):
    parse_edi()

@when("click", "#clear-btn")
def on_clear_click(event):
    clear_all()

@when("click", "#load-file-btn")
def on_load_file_click(event):
    asyncio.ensure_future(load_test_file())

console.log("Event listeners registered - ready to parse!")

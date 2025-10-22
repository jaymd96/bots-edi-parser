# EDI Parser

Standalone EDI parsing library extracted from Bots EDI Translator.
Supports X12, EDIFACT, CSV, XML, JSON, TRADACOMS, IDOC and more.

## Installation

```bash
pip install -e .
```

## Quick Start

### Using the Demo CLI

```bash
# List available test files
python3 demo.py list 835
python3 demo.py list 837

# Validate a single file
python3 demo.py validate 835 test_files/835/835-all-fields.dat

# Parse a single file (lenient mode)
python3 demo.py parse 837 test_files/837/commercial.dat --lenient

# Run all files in a directory
python3 demo.py validate-all 835
python3 demo.py parse-all 837 --lenient

# Verbose mode (shows function entry/exit logging)
python3 demo.py --verbose validate 835 test_files/835/835-denial.dat
```

### Using the Python API

```python
import edi_parser

# Validate a file (strict)
result = edi_parser.validate_file(
    filepath='payment.835',
    editype='x12',
    messagetype='835005010'
)

if result['valid']:
    print("✓ Valid")
else:
    print(f"✗ {result['error_count']} errors")
    for error in result['errors']:
        print(f"  - {error['description']}")

# Parse a file (lenient - best effort)
result = edi_parser.parse_file(
    filepath='payment.835',
    editype='x12',
    messagetype='835005010',
    field_validation_mode='lenient',
    continue_on_error=True
)

if result['success']:
    data = result['data']  # Extracted EDI data
```

## Two Modes

### 1. Validation (Strict)
- Returns **ALL** errors with descriptions and suggestions
- Use before sending files to trading partners
- Function: `validate_file()`

### 2. Parsing (Lenient)
- Extracts data even from imperfect files
- Best-effort parsing for data extraction
- Function: `parse_file()` with `field_validation_mode='lenient'`

## Project Structure

```
edi_parser/
├── demo.py                      # Simple CLI demo
├── test_files/                  # Real-world test samples
│   ├── 835/                     # 7 EDI 835 test files
│   │   ├── 835-all-fields.dat
│   │   ├── 835-denial.dat
│   │   └── ...
│   └── 837/                     # 16 EDI 837 test files
│       ├── 837D-all-fields.dat
│       ├── 837I-all-fields.dat
│       ├── 837P-all-fields.dat
│       ├── commercial.dat
│       └── ...
├── edi_parser/                  # Source code
│   ├── api.py                   # Main API
│   ├── core/                    # Core parsing engine
│   ├── lib/
│   │   ├── utils.py
│   │   └── logging_utils.py     # Function logging utilities
│   ├── grammars/                # Transaction grammars
│   │   └── x12/
│   │       └── 5010/
│   │           ├── 835005010.py
│   │           └── 837005010.py
│   └── transformers/            # Data transformers
└── implementation_guides/       # XML implementation guides
    └── *.xml
```

### Test Files

The test files in `test_files/835/` and `test_files/837/` are sourced from the [Healthcare Data Insight API Examples](https://github.com/Healthcare-Data-Insight/api-examples/tree/main/edi_files) repository and represent real-world EDI scenarios:

**835 Test Files (7 files):**
- Payment/remittance advice scenarios
- Denials, provider adjustments, negotiated discounts
- Various adjustment reason codes

**837 Test Files (16 files):**
- Professional (837P), Institutional (837I), and Dental (837D) claims
- Specialized scenarios: ambulance, anesthesia, chiropractic, wheelchair
- Coordination of Benefits (COB), commercial insurance, PPO repricing

**Note:** The grammars now support full X12 interchange envelopes (ISA/GS/ST/SE/GE/IEA). Some test files may be malformed (missing GS/GE segments) and will fail validation, but properly formatted files with complete envelopes parse successfully.

## Logging

The parser uses Python's logging module (no print statements).

**Normal mode (INFO):**
```python
import edi_parser
result = edi_parser.parse_file(...)
# Shows: INFO, WARNING, ERROR
```

**Verbose mode (DEBUG):**
```bash
python3 demo.py --verbose validate 835 test_files/835_sample.edi
# Shows: Function entry/exit, detailed flow
```

**Programmatic:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# or
from edi_parser.lib.logging_utils import enable_verbose_logging
enable_verbose_logging()
```

## Supported Transactions

Common X12 healthcare transactions:
- **835** - Health Care Claim Payment/Advice
- **837** - Health Care Claim (Professional, Institutional, Dental)
- **270/271** - Eligibility Inquiry/Response
- **276/277** - Claim Status Inquiry/Response
- **834** - Benefit Enrollment
- And many more...

## Development

### Grammar Development

Hand-rolled grammars are preferred over auto-generated:

```bash
# Generate draft from XML (reference only)
python3 ../x12xml_to_bots_grammar.py \
    implementation_guides/835.5010.X221.A1.xml \
    835_draft.py

# Then hand-edit for simplicity and permissiveness
# Use existing grammars in grammars/x12/5010/ as templates
```

See `x12xml_to_bots_grammar.py` header for full SOP.

### Adding Function Logging

```python
from edi_parser.lib.logging_utils import log_function_call

@log_function_call
def my_function(x, y):
    return x + y

# In DEBUG mode, this logs:
#   → Entering my_function
#   ← Exiting my_function
```

Or use metaclass for entire classes:

```python
from edi_parser.lib.logging_utils import LoggedMeta

class MyClass(metaclass=LoggedMeta):
    def my_method(self):
        pass  # Automatically logged in DEBUG mode
```

## Philosophy

- **Minimal** - No bloat, no unnecessary files
- **Radical Simplicity** - One demo, one README, two test files
- **Functional** - Full parsing capability without compromise
- **Proper Logging** - No print statements, structured logging with levels
- **Real-World** - Handles imperfect files with lenient mode

## License

Based on Bots EDI Translator (GNU GPL v3)

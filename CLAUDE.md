# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a standalone EDI (Electronic Data Interchange) parsing library extracted from the Bots EDI Translator. It parses healthcare EDI files (X12 835, 837, etc.) and EDIFACT formats into structured JSON/dictionaries.

**Published PyPI Package:** `bots-edi-parser`

## Key Commands

### Development & Testing
```bash
# Install in development mode
pip install -e .

# Run demo CLI (primary development tool)
python3 demo.py list 835                                    # List test files
python3 demo.py validate 835 test_files/835/835-all-fields.dat
python3 demo.py parse 837 test_files/837/commercial.dat --lenient
python3 demo.py validate-all 835                            # Run all files
python3 demo.py --verbose validate 835 test_files/835/835-denial.dat

# Run tests (test files are in root)
pytest test_package.py
pytest test_transformer.py
pytest test_container.py

# Code formatting (configured in pyproject.toml)
black --line-length 100 edi_parser/
flake8 edi_parser/
```

### Build & Publish
```bash
# Build package
python3 -m build

# Install from local build
pip install dist/bots_edi_parser-*.whl

# Publish to PyPI (maintainers only)
python3 -m twine upload dist/*
```

## Core Architecture

### Two-Phase Design: Grammar + Parser

The library uses a two-phase approach inspired by compiler design:

1. **Grammar Phase** (`edi_parser/grammars/`): Defines message structure
   - Grammar files define the hierarchical structure of EDI transactions (which segments are allowed, in what order, how many times)
   - Hand-rolled Python files that define `structure` (segment hierarchy) and `recorddefs` (field definitions)
   - Located in `grammars/{editype}/{version}/` (e.g., `grammars/x12/5010/835005010.py`)

2. **Parser Phase** (`edi_parser/core/inmessage.py`): Reads and validates files
   - `inmessage.py` contains format-specific parsers (X12, EDIFACT, CSV, etc.) as subclasses
   - Reads raw EDI, lexes into segments/fields, parses according to grammar
   - Builds a tree of `Node` objects representing the message hierarchy

### Main Entry Points

**`edi_parser/api.py`** provides two high-level functions:

1. **`validate_file(filepath, editype, messagetype)`** - Strict validation
   - Returns ALL errors with human-readable descriptions and suggestions
   - Use before sending files to trading partners
   - Sets `field_validation_mode='lenient'` internally but collects all errors

2. **`parse_file(filepath, editype, messagetype, field_validation_mode='lenient')`** - Data extraction
   - Best-effort parsing for imperfect files
   - Returns structured JSON/dict of extracted data
   - Use `continue_on_error=True` for maximum data recovery

Both functions are also available as `validate_edi()` and `parse_edi()` which accept content strings instead of file paths.

### Key Modules

- **`edi_parser/core/grammar.py`**: Grammar loading and syntax handling. Dispatches to format-specific grammar classes (X12, EDIFACT, etc.)
- **`edi_parser/core/inmessage.py`**: Main parsing engine. Contains `Inmessage` base class and format-specific subclasses (X12, EDIFACT, CSV, JSON, XML, etc.)
- **`edi_parser/core/node.py`**: Node tree structure. Represents parsed EDI as hierarchical tree of segments/fields
- **`edi_parser/core/message.py`**: Message manipulation and navigation utilities
- **`edi_parser/core/error_formatter.py`**: Converts error codes to human-readable descriptions with suggestions
- **`edi_parser/core/error_metadata.py`**: Error code metadata (descriptions, severities, suggestions)
- **`edi_parser/transformers/`**: Data transformers that add human-readable field names to parsed output

### Field Mappings & Transformers

**`edi_parser/field_mappings/`** contains JSON files mapping EDI field codes to human-readable names:
- `x12/segments.json` - X12 segment names (e.g., BPR → "Financial Information")
- `x12/835_fields.json` - 835-specific field names
- `x12/837_fields.json` - 837-specific field names

**Transformer Usage:**
```python
result = edi_parser.parse_file('payment.835', editype='x12', messagetype='835005010')
enhanced = edi_parser.add_human_readable_names(result['data'])
# Now fields have both codes and names: {"BPR01": "C", "BPR01_name": "Transaction Handling Code"}
```

## Grammar Development

### Hand-Rolled vs. Auto-Generated

**ALWAYS prefer hand-rolled grammars** over auto-generated ones. Hand-rolled grammars are:
- Simpler and more permissive (handles real-world variations)
- Easier to debug and maintain
- Located in `grammars/x12/5010/*.py`

### Creating/Editing Grammars

1. **Generate a draft** (reference only):
   ```bash
   python3 ../x12xml_to_bots_grammar.py \
       implementation_guides/835.5010.X221.A1.xml \
       835_draft.py
   ```

2. **Hand-edit for production:**
   - Use existing grammars as templates (`835005010.py`, `837005010.py`)
   - Simplify structure (use high MAX values like 99999 for flexibility)
   - Make optional segments truly optional (MIN: 0)
   - See `x12xml_to_bots_grammar.py` header for full SOP

3. **Grammar structure:**
   ```python
   # grammars/x12/5010/835005010.py
   syntax = {
       'version': '00501',
       'functionalgroup': 'HP',
   }

   structure = [
       {ID: 'ISA', MIN: 1, MAX: 1, LEVEL: [  # Envelope
           {ID: 'GS', MIN: 1, MAX: 1, LEVEL: [
               {ID: 'ST', MIN: 1, MAX: 1, LEVEL: [  # Transaction
                   {ID: 'BPR', MIN: 1, MAX: 1},
                   {ID: 'TRN', MIN: 0, MAX: 1},
                   # ...
               ]},
               {ID: 'SE', MIN: 1, MAX: 1},
           ]},
           {ID: 'GE', MIN: 1, MAX: 1},
       ]},
       {ID: 'IEA', MIN: 1, MAX: 1},
   ]

   # Import shared record definitions
   from .records005010 import recorddefs
   ```

### Important Notes

- Grammars now support **full X12 interchange envelopes** (ISA/GS/ST/SE/GE/IEA)
- Some test files may be malformed (missing GS/GE) and will fail validation
- Field definitions (`recorddefs`) are shared across transaction types in `records005010.py`

## Logging System

The parser uses Python's `logging` module exclusively - **NO print statements**.

### Function-Level Logging

Use decorators from `edi_parser/lib/logging_utils.py` for automatic DEBUG-level logging:

```python
from edi_parser.lib.logging_utils import log_function_call

@log_function_call
def my_function(x, y):
    return x + y

# In DEBUG mode, logs:
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

### Logging Modes

- **Normal (INFO)**: Shows INFO, WARNING, ERROR
- **Verbose (DEBUG)**: Shows function entry/exit, detailed flow
- Enable via CLI: `python3 demo.py --verbose validate ...`
- Enable programmatically: `logging.basicConfig(level=logging.DEBUG)`

## Test Files

Real-world test files from [Healthcare Data Insight API Examples](https://github.com/Healthcare-Data-Insight/api-examples/tree/main/edi_files):

- **`test_files/835/`** (7 files): Payment/remittance scenarios (denials, adjustments, etc.)
- **`test_files/837/`** (16 files): Professional (837P), Institutional (837I), Dental (837D) claims

## PyScript Demo

`docs/index.html` contains a PyScript-based web demo that runs the parser in the browser using PyPI package.

## Philosophy

- **Minimal**: No bloat, no unnecessary documentation
- **Radical Simplicity**: Prefer simple code over complex abstractions
- **Functional**: Full EDI parsing capability without compromise
- **Proper Logging**: Structured logging with levels, no print statements
- **Real-World Ready**: Handles imperfect files with lenient mode

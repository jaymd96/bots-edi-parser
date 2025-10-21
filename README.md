# EDI Parser

A standalone Python library for parsing EDI (Electronic Data Interchange) files. Extracted from the excellent [Bots EDI Translator](https://github.com/bots-edi/bots) project, this library provides powerful EDI parsing capabilities without requiring the full Bots infrastructure (web server, database, job queue, etc.).

## Features

- **Multiple EDI Formats**: Support for EDIFACT, X12, CSV, XML, JSON, TRADACOMS, IDOC, and fixed-width formats
- **Comprehensive Grammar Library**: Includes extensive grammar definitions for various EDI message types
- **Full Validation**: Complete field validation, length checking, and structure verification
- **JSON Output**: Parsed EDI messages are returned as JSON-serializable Python dictionaries
- **Zero External Dependencies**: Uses only Python standard library
- **Simple API**: Easy-to-use interface for parsing EDI files or strings

## Installation

```bash
cd edi_parser
pip install -e .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Parse EDIFACT Message

```python
import edi_parser
import json

# EDIFACT ORDERS message
edifact_content = """UNB+UNOC:3+SENDER:14+RECEIVER:14+20231020:1430+1'
UNH+1+ORDERS:D:96A:UN'
BGM+220+ORDER123+9'
DTM+137:20231020:102'
NAD+BY+BUYER123::92'
UNS+D'
UNT+6+1'
UNZ+1+1'"""

result = edi_parser.parse_edi(
    content=edifact_content,
    editype='edifact',
    messagetype='ORDERS'
)

if result['success']:
    print(json.dumps(result['data'], indent=2))
else:
    print("Errors:", result['errors'])
```

### Parse X12 Message

```python
# X12 850 Purchase Order
x12_content = """ISA*00*          *00*          *ZZ*SENDER         *ZZ*RECEIVER       *231020*1430*U*00401*000000001*0*P*>~
GS*PO*SENDER*RECEIVER*20231020*1430*1*X*004010~
ST*850*0001~
BEG*00*SA*PO123456**20231020~
SE*3*0001~
GE*1*1~
IEA*1*000000001~"""

result = edi_parser.parse_edi(
    content=x12_content,
    editype='x12',
    messagetype='850'
)
```

### Parse from File

```python
result = edi_parser.parse_file(
    filepath='path/to/invoice.edi',
    editype='edifact',
    messagetype='INVOIC'
)
```

## Supported Formats

```python
formats = edi_parser.get_supported_formats()

# Returns:
# {
#     'edifact': 'UN/EDIFACT - United Nations Electronic Data Interchange',
#     'x12': 'ANSI X12 - American National Standards Institute X12',
#     'csv': 'CSV - Comma Separated Values',
#     'fixed': 'Fixed-width record format',
#     'xml': 'XML - Extensible Markup Language',
#     'json': 'JSON - JavaScript Object Notation',
#     'tradacoms': 'TRADACOMS - Trading Data Communications Standard',
#     'idoc': 'SAP IDOC - Intermediate Document',
# }
```

## API Reference

### `parse_edi(content, editype, messagetype, charset='utf-8', **options)`

Parse EDI content and return JSON representation.

**Parameters:**
- `content` (str|bytes): EDI file content
- `editype` (str): Type of EDI (e.g., 'edifact', 'x12', 'csv')
- `messagetype` (str): Message type/grammar name (e.g., 'ORDERS', 'INVOIC', '850')
- `charset` (str): Character encoding (default: 'utf-8')
- `**options`: Additional options:
  - `debug` (bool): Enable debug logging
  - `checkunknownentities` (bool): Check for unknown entities (default: True)
  - `continue_on_error` (bool): Continue parsing even with non-fatal errors

**Returns:**
```python
{
    'success': bool,          # Whether parsing succeeded
    'data': dict,            # Parsed EDI tree (if success=True)
    'errors': list,          # List of error messages (if any)
    'message_count': int,    # Number of messages found
    'editype': str,          # EDI type
    'messagetype': str       # Message type
}
```

### `parse_file(filepath, editype, messagetype, **options)`

Parse an EDI file from a file path. Same parameters as `parse_edi()` except `filepath` instead of `content`.

### `node_to_dict(node)`

Convert a Node tree to a dictionary (used internally).

### `get_supported_formats()`

Get list of supported EDI formats with descriptions.

## Output Structure

The parsed EDI data is returned as a nested dictionary:

```python
{
    'BOTSID': 'UNH',           # Record/segment ID
    'field1': 'value1',        # Field values
    'field2': 'value2',
    '_children': [             # Child records (if any)
        {
            'BOTSID': 'LIN',
            'field1': 'value',
            # ...
        }
    ]
}
```

## Examples

See the `examples/parse_edi.py` file for complete working examples including:
- Parsing EDIFACT messages
- Parsing X12 messages
- Parsing from files
- Using custom options
- Listing supported formats

Run the examples:

```bash
cd examples
python parse_edi.py
```

## Grammar Files

The library includes comprehensive grammar definitions in the `grammars/` directory:

```
grammars/
├── edifact/
│   ├── D96A/       # EDIFACT Directory D96A
│   ├── D01B/       # EDIFACT Directory D01B
│   └── ...
├── x12/
│   ├── 00401/      # X12 Version 4010
│   ├── 00501/      # X12 Version 5010
│   └── ...
└── ...
```

Each grammar defines:
- **Structure**: The hierarchical structure of segments/records
- **Record Definitions**: Field definitions including type, length, and validation rules
- **Syntax**: Separators, encoding, and format-specific rules

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
black edi_parser/

# Lint
pylint edi_parser/
```

## License

This library is extracted from the Bots EDI Translator project and maintains the same GPLv3 license.

## Credits

- **Original Bots Project**: https://github.com/bots-edi/bots
- **Bots Authors**: Many contributors to the Bots EDI Translator project

This library extracts and focuses solely on the EDI parsing functionality from Bots, removing dependencies on Django, databases, and other infrastructure components to create a lightweight, standalone parser.

## Differences from Bots

This library differs from the full Bots installation:

**Removed:**
- Web server and GUI
- Database (SQLite/PostgreSQL)
- Job queue and scheduler
- Communication channels (FTP, SFTP, AS2, etc.)
- Mapping/transformation engine
- Routing and partner management

**Kept:**
- Complete EDI parsing engine
- All grammar files for various EDI formats
- Full validation capabilities
- Error handling and reporting

**Use this library if you:**
- Only need to parse EDI files (not transform or route them)
- Want a lightweight solution without database dependencies
- Need EDI parsing in a larger application
- Want a simple API for EDI to JSON conversion

**Use full Bots if you:**
- Need complete EDI translation workflows
- Require partner management and routing
- Need communication channels for receiving/sending EDI
- Want a complete B2B integration platform

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## Support

For issues and questions:
- Open an issue on GitHub
- Refer to original Bots documentation for EDI concepts: http://bots.readthedocs.io/

## Changelog

### 1.0.0 (2025-01-21)
- Initial release
- Extracted from Bots 4.x
- Support for EDIFACT, X12, CSV, XML, JSON, TRADACOMS, IDOC
- Complete grammar library
- JSON output format
- Zero external dependencies

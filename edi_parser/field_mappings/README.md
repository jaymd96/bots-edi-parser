# Field Mappings Package

Human-readable field name mappings for EDI standards.

## Overview

This package provides access to structured definitions of EDI message formats, enabling conversion from technical field codes to human-readable names and descriptions.

## Supported Standards

### EDIFACT (Complete)

**Source**: UN/CEFACT UNTDID (United Nations Trade Data Interchange Directory)

**Versions Available**:
- **D96A** (1996 Release A) - 127 segments
- **D96B** (1996 Release B) - 136 segments
- **D01B** (2001 Release B) - 158 segments

### X12 (Planned)

Implementation guides from imsweb/x12-parser repository (37 transaction types downloaded, parser pending).

## Installation

The package is included with edi_parser:

```python
from edi_parser.field_mappings import edifact
```

## Usage

### Quick Start

```python
from edi_parser.field_mappings import edifact

# List available versions
versions = edifact.list_versions()
# Returns: ['D01B', 'D96A', 'D96B']

# Get segment definition
nad = edifact.get_segment('NAD', 'D96A')
print(nad['name'])  # 'NAME AND ADDRESS'
print(nad['function'])  # Description of segment purpose

# Get specific field
field = edifact.get_field('NAD', '010', 'D96A')
print(field['name'])  # 'PARTY QUALIFIER'
print(field['data_type'])  # 'an..3'
print(field['status'])  # 'Mandatory'

# List all segments in a version
segments = edifact.list_segments('D96A')
# Returns: ['ADR', 'AGR', 'AJT', 'ALC', ...]

# Search segments by name
results = edifact.search_segments('address', 'D96A')
# Returns: [{'code': 'NAD', 'name': 'NAME AND ADDRESS'}]
```

### Advanced Usage

```python
from edi_parser.field_mappings.edifact import SegmentDatabase

# Create database instance for advanced queries
db = SegmentDatabase()

# Get field by element code instead of position
field = db.get_field_by_code('NAD', '3035', 'D96A')
print(field['name'])  # 'PARTY QUALIFIER'

# Search segments
results = db.search_segments('monetary', 'D01B')
for result in results:
    print(f"{result['code']}: {result['name']}")
```

### Working with Composite Fields

EDIFACT composite fields (codes starting with 'C') contain sub-elements:

```python
segment = edifact.get_segment('NAD', 'D96A')

# Find composite field
for field in segment['fields']:
    if field['code'].startswith('C'):
        print(f"{field['code']}: {field['name']}")

        # Access sub-elements
        if 'sub_elements' in field:
            for sub in field['sub_elements']:
                print(f"  └─ {sub['code']}: {sub['name']}")
```

## API Reference

### Module Functions

#### `list_versions() -> List[str]`
List all available EDIFACT versions.

**Returns**: List of version strings (e.g., `['D96A', 'D96B', 'D01B']`)

#### `get_segment(segment_code: str, version: str = 'D01B') -> Optional[Dict]`
Get complete segment definition.

**Parameters**:
- `segment_code`: 3-letter segment code (e.g., 'NAD', 'BGM')
- `version`: EDIFACT version (default: 'D01B')

**Returns**: Dictionary with keys:
- `code`: Segment code
- `name`: Human-readable segment name
- `function`: Description of segment purpose
- `fields`: List of field definitions

#### `get_field(segment_code: str, position: str, version: str = 'D01B') -> Optional[Dict]`
Get specific field definition from a segment.

**Parameters**:
- `segment_code`: 3-letter segment code
- `position`: Field position (e.g., '010', '020')
- `version`: EDIFACT version

**Returns**: Dictionary with keys:
- `position`: Field position
- `code`: Data element code
- `name`: Human-readable field name
- `data_type`: Data type specification (e.g., 'an..3')
- `status`: 'Mandatory' or 'Conditional'
- `sub_elements`: List of sub-elements (for composites only)

#### `list_segments(version: str = 'D01B') -> List[str]`
List all segment codes for a version.

**Parameters**:
- `version`: EDIFACT version

**Returns**: Sorted list of 3-letter segment codes

#### `search_segments(name_pattern: str, version: str = 'D01B') -> List[Dict]`
Search segments by name pattern (case-insensitive).

**Parameters**:
- `name_pattern`: Substring to search for
- `version`: EDIFACT version

**Returns**: List of dictionaries with `code` and `name` keys

### SegmentDatabase Class

Advanced API for specialized queries:

```python
class SegmentDatabase:
    def list_versions() -> List[str]
    def get_segment(segment_code: str, version: str) -> Optional[Dict]
    def get_field(segment_code: str, position: str, version: str) -> Optional[Dict]
    def list_segments(version: str) -> List[str]
    def search_segments(name_pattern: str, version: str) -> List[Dict]
    def get_field_by_code(segment_code: str, element_code: str, version: str) -> Optional[Dict]
```

## Data Structure

### Segment Definition

```json
{
  "code": "NAD",
  "name": "NAME AND ADDRESS",
  "function": "To specify the name/address...",
  "fields": [...]
}
```

### Field Definition

```json
{
  "position": "010",
  "code": "3035",
  "name": "PARTY QUALIFIER",
  "data_type": "an..3",
  "status": "Mandatory"
}
```

### Composite Field

```json
{
  "position": "020",
  "code": "C082",
  "name": "PARTY IDENTIFICATION DETAILS",
  "data_type": "",
  "status": "Conditional",
  "sub_elements": [
    {
      "code": "3039",
      "name": "Party id. identification",
      "data_type": "an..35",
      "status": "Mandatory"
    }
  ]
}
```

## Data Type Notation

EDIFACT uses specific notation for data types:

| Notation | Meaning | Example Values |
|----------|---------|----------------|
| `an..3` | Alphanumeric, up to 3 chars | "ABC", "12", "A1" |
| `an..35` | Alphanumeric, up to 35 chars | "John Smith" |
| `a..35` | Alphabetic only, up to 35 chars | "London" |
| `n..9` | Numeric only, up to 9 digits | "123456789" |
| `n..2` | Numeric only, up to 2 digits | "01", "99" |

## Common EDIFACT Segments

### Commercial/Trade
- **BGM** - Beginning of Message
- **DTM** - Date/Time/Period
- **FTX** - Free Text
- **IMD** - Item Description
- **LIN** - Line Item
- **MOA** - Monetary Amount
- **PRI** - Price Details
- **QTY** - Quantity

### Parties
- **NAD** - Name and Address
- **CTA** - Contact Information
- **COM** - Communication Contact

### Transport/Logistics
- **LOC** - Place/Location Identification
- **TDT** - Transport Information
- **TOD** - Terms of Delivery or Transport

### Documents/References
- **DOC** - Document/Message Details
- **RFF** - Reference
- **PAC** - Package

## Directory Structure

```
field_mappings/
├── __init__.py              # Top-level exports
├── README.md                # This file
├── edifact/
│   ├── __init__.py          # EDIFACT exports
│   ├── segments.py          # Segment database API
│   ├── README.md            # EDIFACT-specific docs
│   └── data/
│       ├── __init__.py
│       ├── d96a_segments.json
│       ├── d96b_segments.json
│       └── d01b_segments.json
└── x12/                     # (Future)
    └── ...
```

## Examples

See `examples/edifact_segment_lookup.py` for comprehensive usage examples.

## Performance

- **Lazy loading**: Data files are only loaded when first accessed
- **Caching**: Loaded versions remain in memory for fast subsequent queries
- **Small footprint**: ~280KB per version, ~840KB total for all 3 versions

## Future Enhancements

1. **X12 Support**: Parse implementation guide XMLs (37 files downloaded)
2. **Field value translation**: Decode code values to descriptions
3. **Validation utilities**: Validate fields against definitions
4. **Message type mappings**: Link segments to specific message types

## License

EDIFACT segment data sourced from UN/CEFACT, which provides standards for public use.

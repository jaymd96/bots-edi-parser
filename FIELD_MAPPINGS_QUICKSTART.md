# Field Mappings Quick Start

Human-readable field names for EDIFACT segments.

## Basic Usage

```python
from edi_parser.field_mappings import edifact

# Get segment name
nad = edifact.get_segment('NAD', 'D96A')
print(nad['name'])
# Output: NAME AND ADDRESS

# Get field name
field = edifact.get_field('NAD', '010', 'D96A')
print(field['name'])
# Output: PARTY QUALIFIER

# List all segments
segments = edifact.list_segments('D96A')
# Output: ['ADR', 'AGR', 'AJT', ...]

# Search by name
results = edifact.search_segments('date')
# Output: [{'code': 'DTM', 'name': 'DATE/TIME/PERIOD'}]
```

## Available Versions

- **D96A**: 127 segments (1996 Release A)
- **D96B**: 136 segments (1996 Release B)
- **D01B**: 158 segments (2001 Release B) - **Default**

## Common Segments

```python
# Get common commercial segments
common = ['BGM', 'DTM', 'FTX', 'NAD', 'LIN', 'QTY', 'PRI', 'MOA']

for code in common:
    seg = edifact.get_segment(code)
    print(f"{code}: {seg['name']}")
```

Output:
```
BGM: BEGINNING OF MESSAGE
DTM: DATE/TIME/PERIOD
FTX: FREE TEXT
NAD: NAME AND ADDRESS
LIN: LINE ITEM
QTY: QUANTITY
PRI: PRICE DETAILS
MOA: MONETARY AMOUNT
```

## Accessing Field Details

```python
segment = edifact.get_segment('NAD', 'D96A')

# Iterate through fields
for field in segment['fields']:
    print(f"{field['position']} {field['name']}")
    print(f"  Type: {field['data_type']}")
    print(f"  Status: {field['status']}")

    # Check for composite sub-elements
    if 'sub_elements' in field:
        for sub in field['sub_elements']:
            print(f"    └─ {sub['code']}: {sub['name']}")
```

## Data Type Quick Reference

| Type | Meaning | Example |
|------|---------|---------|
| `an..3` | Alphanumeric, max 3 chars | "ABC" |
| `an..35` | Alphanumeric, max 35 chars | "John Smith" |
| `a..35` | Alphabetic only | "London" |
| `n..9` | Numeric only | "123456" |

## Full Documentation

See `edi_parser/field_mappings/README.md` for complete API reference and examples.

## Example Script

Run the full example:

```bash
python3 examples/edifact_segment_lookup.py
```

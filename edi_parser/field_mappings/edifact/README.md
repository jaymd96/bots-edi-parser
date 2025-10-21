# EDIFACT Segment Definitions

Downloaded from UN/CEFACT UNTDID (United Nations Trade Data Interchange Directory)

## Summary

**Source**: https://service.unece.org/trade/untdid/

**Downloaded**: October 2025

**Total Segments**: 421 across 3 versions

## Files

| File | Version | Segments | Size | Description |
|------|---------|----------|------|-------------|
| `d96a_segments.json` | D96A (1996 Release A) | 127 | 270KB | EDIFACT segments from 1996A directory |
| `d96b_segments.json` | D96B (1996 Release B) | 136 | 287KB | EDIFACT segments from 1996B directory |
| `d01b_segments.json` | D01B (2001 Release B) | 158 | 280KB | EDIFACT segments from 2001B directory |

## Structure

Each JSON file contains:

```json
{
  "version": "D96A",
  "segments": {
    "NAD": {
      "code": "NAD",
      "name": "NAME AND ADDRESS",
      "function": "To specify the name/address and their related function...",
      "fields": [
        {
          "position": "010",
          "code": "3035",
          "name": "PARTY QUALIFIER",
          "data_type": "an..3",
          "status": "Mandatory"
        },
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
      ]
    }
  }
}
```

## Field Attributes

### Segment Level
- **code**: 3-letter segment identifier (e.g., "NAD", "BGM")
- **name**: Human-readable segment name (e.g., "NAME AND ADDRESS")
- **function**: Description of segment purpose

### Field Level
- **position**: Field position in segment (010, 020, etc.)
- **code**: Data element code (e.g., "3035", "C082")
- **name**: Human-readable field name
- **data_type**: Data type specification (e.g., "an..3" = alphanumeric up to 3 chars)
- **status**: "Mandatory" or "Conditional"
- **sub_elements**: For composite fields (code starts with 'C'), array of sub-elements

## Data Type Notation

| Notation | Meaning | Example |
|----------|---------|---------|
| `an..3` | Alphanumeric, up to 3 characters | "ABC", "12", "A1" |
| `an..35` | Alphanumeric, up to 35 characters | "John Smith" |
| `a..35` | Alphabetic only, up to 35 characters | "London" |
| `n..9` | Numeric only, up to 9 digits | "123456789" |
| `n..2` | Numeric only, up to 2 digits | "01", "99" |

## Common Segments

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

### Financial
- **PAI** - Payment Instructions
- **TAX** - Duty/Tax/Fee Details
- **CUX** - Currencies

## Usage Example

```python
import json

# Load segment definitions
with open('d96a_segments.json', 'r') as f:
    edifact_d96a = json.load(f)

# Access NAD segment
nad_segment = edifact_d96a['segments']['NAD']

print(f"Segment: {nad_segment['code']} - {nad_segment['name']}")
print(f"Function: {nad_segment['function']}")

# Iterate fields
for field in nad_segment['fields']:
    print(f"{field['position']} {field['code']} {field['name']}")
    print(f"  Type: {field['data_type']}, Status: {field['status']}")

    # Check for composite sub-elements
    if 'sub_elements' in field:
        for sub in field['sub_elements']:
            print(f"    └─ {sub['code']} {sub['name']}")
```

## Version Differences

### D96A (127 segments)
- Base 1996 release
- Core commercial and transport segments

### D96B (136 segments, +9 from D96A)
**New segments in D96B**:
- CIN - Clinical Information
- CLI - Clinical Intervention
- DSG - Dosage Administration
- HYN - Hierarchy Information
- PAS - Attendance
- QUA - Qualification
- RSL - Result
- SPR - Organization Classification Details
- TRU - Technical Rules

### D01B (158 segments, +22 from D96B)
**New segments in D01B**:
- APP - Applicability
- BAS - Basis
- CLA - Clause Identification
- CPT - Account Identification
- DFN - Definition Function
- DRD - Data Representation Details
- EDT - Editing Details
- ELV - Element Value Definition
- EVE - Event
- EVT - Event (variant, marked for deletion)
- FOR - Formula
- FSQ - Formula Sequence
- GEI - Processing Information
- IFD - Information Detail
- MTD - Maintenance Operation Details
- PCC - Premium Calculation Component Details
- PER - Period Related Details
- POC - Purpose of Conveyance Call
- PRV - Proviso Details
- PYT - Payment Terms
- QRS - Query and Response
- RJL - Accounting Journal Identification
- ROD - Risk Object Type

## Segment Growth

| Version | Segments | Growth |
|---------|----------|--------|
| D96A | 127 | Base |
| D96B | 136 | +7% (9 segments) |
| D01B | 158 | +16% (22 segments) |

## Next Steps

These segment definitions can be used to:

1. **Build field mapping database** for human-readable EDIFACT parsing
2. **Validate EDIFACT messages** against official segment structures
3. **Generate documentation** for EDIFACT message types
4. **Create parser transformations** from technical codes to readable names

## Related Files

- `../EDIFACT_XML_SOURCES.md` - Documentation of EDIFACT sources and download strategy
- `../HUMAN_READABLE_MAPPING_PLAN.md` - Plan for implementing human-readable field mapping
- `../../download_edifact_segments.py` - Web scraper used to download these definitions

## License

Data sourced from UN/CEFACT, which provides EDIFACT standards for public use.

## Notes

- Some segments appear in multiple versions with updated field definitions
- Composite fields (code starting with 'C') contain sub-elements
- Data types use UN/EDIFACT notation (an = alphanumeric, n = numeric, a = alphabetic)
- Field positions are padded to 3 digits (010, 020, etc.)
- Status values: "Mandatory" = required, "Conditional" = optional/situational

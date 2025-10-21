# X12 Implementation Guide XMLs

Downloaded from: https://github.com/imsweb/x12-parser

## Summary

**Total Files**: 37
- **Transaction Set XMLs**: 28
- **Supporting Files**: 9

## Healthcare Transaction Sets

### Version 5010 (HIPAA Standard)

| Transaction | File | Description |
|-------------|------|-------------|
| 277 | 277.5010.X212.xml | Health Care Claim Status Response |
| 277 | 277.5010.X214.xml | Health Care Claim Status Response (alternate) |
| 820 | 820.5010.X218.xml | Payment Order/Remittance Advice |
| 820 | 820.5010.X218.v2.xml | Payment Order/Remittance Advice (v2) |
| 834 | 834.5010.X220.A1.xml | Benefit Enrollment and Maintenance |
| 834 | 834.5010.X220.A1.v2.xml | Benefit Enrollment and Maintenance (v2) |
| 835 | 835.5010.X221.A1.xml | Health Care Claim Payment/Advice |
| 835 | 835.5010.X221.A1.v2.xml | Health Care Claim Payment/Advice (v2) |
| 837 | 837.5010.X222.A1.xml | Health Care Claim (Professional) |
| 837I | 837Q3.I.5010.X223.A1.xml | Health Care Claim (Institutional) |
| 837I | 837Q3.I.5010.X223.A1.v2.xml | Health Care Claim (Institutional v2) |
| 999 | 999.5010.xml | Implementation Acknowledgment |

### Version 4010

| Transaction | File | Description |
|-------------|------|-------------|
| 270 | 270.4010.X092.A1.xml | Health Care Eligibility Inquiry |
| 271 | 271.4010.X092.A1.xml | Health Care Eligibility Response |
| 276 | 276.4010.X093.A1.xml | Health Care Claim Status Request |
| 277 | 277.4010.X093.A1.xml | Health Care Claim Status Response |
| 277U | 277U.4010.X070.xml | Health Care Claim Status (Unsolicited) |
| 278 | 278.4010.X094.A1.xml | Health Care Services Review |
| 278 | 278.4010.X094.27.A1.xml | Health Care Services Review (variant) |
| 820 | 820.4010.X061.A1.xml | Payment Order/Remittance Advice |
| 834 | 834.4010.X095.A1.xml | Benefit Enrollment and Maintenance |
| 835 | 835.4010.X091.A1.xml | Health Care Claim Payment/Advice |
| 837P | 837.4010.X096.A1.xml | Health Care Claim (Professional) |
| 837I | 837.4010.X097.A1.xml | Health Care Claim (Institutional) |
| 837D | 837.4010.X098.A1.xml | Health Care Claim (Dental) |
| 997 | 997.4010.xml | Functional Acknowledgment |

## Commercial Transaction Sets

| Transaction | File | Description |
|-------------|------|-------------|
| 830 | 830.4010.PS.xml | Planning Schedule |
| 841 | 841.4010.XXXC.xml | Specifications/Technical Information |

## Supporting Files

| File | Description |
|------|-------------|
| codes.xml | Code value definitions |
| dataele.xml | Data element definitions |
| maps.xml | Mapping configurations |
| x12.control.00401.xml | X12 control segments (version 4010) |
| x12.control.00501.xml | X12 control segments (version 5010) |
| map.xsd | XML schema for map files |
| map.v2.xsd | XML schema for map files (v2) |
| maps.xsd | XML schema for maps configuration |
| x12simple.dtd | DTD for simple X12 structure |

## Missing from Repository

The following HIPAA 5010 transactions are **not available** in the imsweb repository:

- ❌ 270.5010 - Health Care Eligibility Inquiry
- ❌ 271.5010 - Health Care Eligibility Response
- ❌ 276.5010 - Health Care Claim Status Request
- ❌ 278.5010 - Health Care Services Review

For these, we have 4010 versions that can be used as reference, but 5010 versions would need to be obtained from:
- X12.org (commercial purchase)
- Other vendors
- Created manually based on HIPAA specifications

## XML Structure

Each XML file contains:
- Loop definitions (hierarchical structure)
- Segment definitions
- Element definitions with:
  - `<name>` - Human-readable field name
  - `<data_ele>` - Data element code
  - `<usage>` - R (Required), S (Situational), N (Not Used)
  - `<valid_codes>` - Allowed values

## Usage

These XML files can be parsed to extract human-readable field names for the EDI parser.

Example element structure:
```xml
<element xid="BPR01">
  <data_ele>305</data_ele>
  <name>Transaction Handling Code</name>
  <usage>R</usage>
  <seq>01</seq>
</element>
```

This maps `BPR01` → "Transaction Handling Code"

## Next Steps

1. Parse these XML files to extract field name mappings
2. Create a field name database
3. Use it to transform JSON output with human-readable keys

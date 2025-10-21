# Human-Readable Field Mapping Plan

## Overview

Transform cryptic EDI field codes (like `BPR01`, `ISA06`) into human-readable names (like `transaction_handling_code`, `interchange_sender_id`) by extracting metadata from X12 implementation guide XML files.

## Goals

1. **Parse XML implementation guides** to extract field name mappings
2. **Build a comprehensive field mapping database** covering all available transaction types
3. **Create transformation functions** to convert parsed EDI JSON
4. **Support multiple output formats** (replace keys, add metadata, nested structure)
5. **Handle composite fields and sub-elements** (e.g., `SVC01.01`)
6. **Provide segment descriptions** in addition to field names

## Current State

### What We Have
- 37 XML implementation guide files covering healthcare and commercial transactions
- Existing EDI parser that outputs JSON with technical field codes
- Two working test files (835 and 837) that parse successfully

### Example Current Output
```json
{
  "BOTSID": "BPR",
  "BPR01": "I",
  "BPR02": "132",
  "BPR03": "C"
}
```

### Desired Output (Multiple Options)

**Option 1: Replace Keys**
```json
{
  "segment_id": "BPR",
  "transaction_handling_code": "I",
  "total_actual_provider_payment_amount": "132",
  "credit_debit_flag_code": "C"
}
```

**Option 2: Dual Keys (Recommended)**
```json
{
  "BOTSID": "BPR",
  "segment_name": "Financial Information",
  "BPR01": "I",
  "BPR01_name": "Transaction Handling Code",
  "BPR02": "132",
  "BPR02_name": "Total Actual Provider Payment Amount",
  "BPR03": "C",
  "BPR03_name": "Credit/Debit Flag Code"
}
```

**Option 3: Nested Structure (Most Complete)**
```json
{
  "segment": {
    "id": "BPR",
    "code": "BPR",
    "name": "Financial Information",
    "description": "Payment and financial information"
  },
  "fields": [
    {
      "id": "BPR01",
      "name": "Transaction Handling Code",
      "readable_name": "transaction_handling_code",
      "value": "I",
      "description": "Code indicating type of transaction",
      "data_element": "305",
      "usage": "R",
      "valid_codes": ["I", "P", "U", "X"]
    },
    {
      "id": "BPR02",
      "name": "Total Actual Provider Payment Amount",
      "readable_name": "total_actual_provider_payment_amount",
      "value": "132",
      "description": "Total payment amount",
      "data_element": "782",
      "usage": "R"
    }
  ]
}
```

## XML Structure Analysis

### Element Structure
```xml
<element xid="BPR01">
  <data_ele>305</data_ele>
  <name>Transaction Handling Code</name>
  <usage>R</usage>
  <seq>01</seq>
  <valid_codes>
    <code>I</code>
    <code>P</code>
    <code>U</code>
    <code>X</code>
  </valid_codes>
</element>
```

### Segment Structure
```xml
<segment xid="BPR">
  <name>Financial Information</name>
  <usage>R</usage>
  <pos>0200</pos>
  <max_use>1</max_use>
  <element xid="BPR01">...</element>
  <element xid="BPR02">...</element>
  <composite xid="BPR05">
    <element xid="BPR05-01">...</element>
    <element xid="BPR05-02">...</element>
  </composite>
</segment>
```

### Composite Structure
Composites contain sub-elements that may appear as:
- `BPR05.01` (dot notation in parsed JSON)
- `BPR05-01` (dash notation in XML)

## Implementation Plan

### Phase 1: XML Parser Module

**File**: `edi_parser/core/field_mapper.py`

**Components**:

1. **XML Parser Class**: `ImplementationGuideParser`
   - Parse XML files using ElementTree
   - Extract segment definitions
   - Extract element definitions
   - Extract composite definitions
   - Handle valid codes/enumerations

2. **Data Structures**:
   ```python
   FieldDefinition = {
       'field_id': 'BPR01',
       'name': 'Transaction Handling Code',
       'readable_name': 'transaction_handling_code',
       'data_element': '305',
       'usage': 'R',  # R=Required, C=Conditional, S=Situational
       'data_type': 'AN',
       'min_length': 1,
       'max_length': 1,
       'valid_codes': ['I', 'P', 'U', 'X'],
       'description': None  # If available in XML
   }

   SegmentDefinition = {
       'segment_id': 'BPR',
       'name': 'Financial Information',
       'description': None,
       'fields': [FieldDefinition, ...],
       'composites': {...}
   }
   ```

3. **Functions**:
   - `parse_xml_file(filepath)` → dict of segments
   - `extract_field_info(element_node)` → FieldDefinition
   - `extract_segment_info(segment_node)` → SegmentDefinition
   - `normalize_field_name(name)` → snake_case name

### Phase 2: Field Mapping Database Builder

**File**: `edi_parser/core/field_database.py`

**Purpose**: Build a consolidated database from all XML files

**Database Structure**:
```python
field_database = {
    'version': '5010',
    'segments': {
        'BPR': {
            'name': 'Financial Information',
            'fields': {
                'BPR01': {...},
                'BPR02': {...},
                'BPR05.01': {...}  # Composite sub-element
            }
        },
        'ISA': {...},
        'ST': {...}
    },
    'common_fields': {
        # Fields that appear in multiple segments
        'REF01': {...},
        'DTM01': {...}
    }
}
```

**Functions**:
- `build_database_from_xmls(xml_directory)` → field_database
- `merge_multiple_versions(databases)` → merged_database
- `save_database(database, output_path)` → JSON file
- `load_database(db_path)` → field_database

**Output Files**:
- `field_mappings_5010.json` - Healthcare 5010 mappings
- `field_mappings_4010.json` - Healthcare 4010 mappings
- `field_mappings_common.json` - Common commercial transaction mappings

### Phase 3: JSON Transformation Module

**File**: `edi_parser/core/json_transformer.py`

**Class**: `EDITransformer`

**Methods**:

1. **`transform_keys(edi_json, database, mode='replace')`**
   - mode='replace': Replace BPR01 with readable name
   - mode='dual': Keep both BPR01 and BPR01_name
   - mode='nested': Full nested structure
   - mode='metadata': Add all available metadata

2. **`add_field_descriptions(edi_json, database)`**
   - Add description fields for each element
   - Add segment descriptions

3. **`add_valid_codes(edi_json, database)`**
   - Include valid code lists where available
   - Validate current values against valid codes

4. **`transform_tree(node, database, mode)`**
   - Recursively transform entire EDI tree
   - Handle nested children
   - Preserve tree structure

### Phase 4: API Integration

**File**: `edi_parser/api.py`

**New Functions**:

```python
def parse_edi_human_readable(
    content: Union[str, bytes],
    editype: str,
    messagetype: str,
    readable_format: str = 'dual',  # 'replace', 'dual', 'nested', 'metadata'
    include_descriptions: bool = True,
    include_valid_codes: bool = False,
    **options
) -> Dict[str, Any]:
    """
    Parse EDI and return JSON with human-readable field names

    Args:
        content: EDI content
        editype: EDI type ('x12', 'edifact', etc.)
        messagetype: Message type ('835005010', etc.)
        readable_format: Output format style
        include_descriptions: Add field descriptions
        include_valid_codes: Include valid code lists

    Returns:
        dict with 'success', 'data', 'errors', plus readable field names
    """
```

**Update Existing Functions**:
```python
def parse_edi(..., human_readable=False, readable_format='dual', **options):
    """Add optional human_readable parameter to existing function"""
```

### Phase 5: Field Name Normalization

**Challenges**:
- XML names are verbose: "Total Actual Provider Payment Amount"
- Need consistent snake_case: "total_actual_provider_payment_amount"
- Handle special characters, abbreviations
- Resolve naming conflicts across segments

**Normalization Rules**:
```python
def normalize_field_name(xml_name):
    """
    Convert XML field name to snake_case identifier

    Examples:
        "Transaction Handling Code" → "transaction_handling_code"
        "Payer's Claim Number" → "payers_claim_number"
        "N1-01" → "n1_01"
        "Date/Time Qualifier" → "date_time_qualifier"
    """
    # 1. Convert to lowercase
    # 2. Replace spaces with underscores
    # 3. Remove special characters (keep alphanumeric and underscore)
    # 4. Remove possessives ('s)
    # 5. Replace multiple underscores with single
    # 6. Strip leading/trailing underscores
```

**Conflict Resolution**:
- When same field name appears in multiple segments with different meanings
- Prefix with segment ID: `bpr_transaction_handling_code` vs `st_transaction_handling_code`
- Maintain mapping of conflicts for disambiguation

### Phase 6: Composite Field Handling

**Challenge**: Composite fields have sub-elements

**Current Format**: `BPR05.01`, `BPR05.02`

**Options**:

1. **Flat structure** (current):
   ```json
   {
     "BPR05.01": "value",
     "BPR05.01_name": "Sub-element Name"
   }
   ```

2. **Nested composite**:
   ```json
   {
     "BPR05": {
       "composite_name": "Composite Name",
       "01": {"name": "...", "value": "..."},
       "02": {"name": "...", "value": "..."}
     }
   }
   ```

**Recommendation**: Support both, with flat as default for backward compatibility

## Data Files Structure

```
edi_parser/
├── field_mappings/
│   ├── x12/
│   │   ├── 5010/
│   │   │   ├── segments.json         # All segment definitions
│   │   │   ├── fields.json           # All field definitions
│   │   │   ├── composites.json       # Composite definitions
│   │   │   └── by_transaction/
│   │   │       ├── 835.json          # 835-specific mappings
│   │   │       ├── 837.json
│   │   │       └── ...
│   │   ├── 4010/
│   │   │   └── ...
│   │   └── common/
│   │       └── envelope.json         # ISA, GS, ST, SE, GE, IEA
│   └── edifact/
│       └── ...
└── implementation_guides/
    └── [XML files]
```

## Usage Examples

### Example 1: Parse with Dual Keys (Recommended)
```python
import edi_parser

result = edi_parser.parse_edi_human_readable(
    content=edi_content,
    editype='x12',
    messagetype='835005010',
    readable_format='dual'
)

# Access both ways:
bpr = result['data']['children'][0]['_children'][0]['_children'][0]['_children'][0]
print(bpr['BPR01'])        # "I"
print(bpr['BPR01_name'])   # "Transaction Handling Code"
```

### Example 2: Parse with Nested Structure
```python
result = edi_parser.parse_edi_human_readable(
    content=edi_content,
    editype='x12',
    messagetype='835005010',
    readable_format='nested',
    include_descriptions=True
)

# Navigate fields array:
bpr = result['data'][...]['fields']
for field in bpr:
    print(f"{field['name']}: {field['value']}")
    print(f"  Description: {field['description']}")
```

### Example 3: Add Readability to Existing Parsed Data
```python
# Parse normally first
result = edi_parser.parse_edi(content, 'x12', '835005010')

# Transform afterward
from edi_parser import make_human_readable

readable = make_human_readable(
    result['data'],
    editype='x12',
    version='5010',
    format='dual'
)
```

## Implementation Steps

### Step 1: Build XML Parser (1-2 days)
- [ ] Create `ImplementationGuideParser` class
- [ ] Parse segment definitions
- [ ] Parse element definitions
- [ ] Handle composites
- [ ] Extract valid codes
- [ ] Test with 835.5010.X221.A1.xml

### Step 2: Build Field Database (1 day)
- [ ] Create database builder
- [ ] Process all XML files in directory
- [ ] Merge definitions from multiple files
- [ ] Handle version differences (4010 vs 5010)
- [ ] Save as JSON files
- [ ] Test loading/accessing database

### Step 3: Create Transformer (1-2 days)
- [ ] Implement replace mode
- [ ] Implement dual mode
- [ ] Implement nested mode
- [ ] Handle tree traversal with _children
- [ ] Handle composite fields
- [ ] Test with 835 and 837 parsed JSON

### Step 4: API Integration (1 day)
- [ ] Add `parse_edi_human_readable()` function
- [ ] Add optional parameter to existing functions
- [ ] Update `__init__.py` exports
- [ ] Add backward compatibility checks

### Step 5: Testing & Documentation (1-2 days)
- [ ] Test with all available transaction types
- [ ] Test edge cases (missing fields, unknown segments)
- [ ] Create usage examples
- [ ] Update README with new API
- [ ] Add to validation example

### Step 6: Performance Optimization (optional)
- [ ] Cache loaded field databases
- [ ] Lazy load databases only when needed
- [ ] Optimize tree traversal
- [ ] Benchmark transformation speed

## Challenges & Solutions

### Challenge 1: Missing XML Files
**Problem**: We don't have 5010 XMLs for 270, 271, 276, 278

**Solutions**:
1. Use 4010 versions as fallback
2. Extract common segment definitions (ISA, GS, ST work across versions)
3. Allow manual addition of field mappings
4. Mark fields as "name unknown" when not in database

### Challenge 2: Field Name Conflicts
**Problem**: Same field ID (e.g., REF01) means different things in different contexts

**Solutions**:
1. Namespace by segment: `ref_reference_identification_qualifier`
2. Maintain context in nested structure
3. Include segment name in output
4. Document known conflicts

### Challenge 3: Composite Fields
**Problem**: Composites like `C003` have sub-elements that need mapping

**Solutions**:
1. Parse composite definitions from XML
2. Map both composite and sub-elements
3. Support both `C003.01` and nested structures
4. Handle optional composite elements

### Challenge 4: Performance
**Problem**: Loading large XML files and transforming JSON trees is slow

**Solutions**:
1. Pre-build JSON databases (one-time cost)
2. Cache loaded databases in memory
3. Only load databases for requested transaction types
4. Provide option to skip transformation for raw speed

### Challenge 5: Multiple Versions
**Problem**: Field meanings change between X12 versions

**Solutions**:
1. Separate databases per version
2. Auto-detect version from parsed ISA12 field
3. Allow explicit version override
4. Fall back to closest available version

## Future Enhancements

### 1. Web UI
Build a web interface to:
- Browse field mappings
- View segment structures
- Search for fields by name
- Compare versions

### 2. Field Value Translation
Not just field names, but translate code values:
```json
{
  "BPR01": "I",
  "BPR01_name": "Transaction Handling Code",
  "BPR01_decoded": "Remittance Information Only"
}
```

### 3. EDIFACT Support
Extend to EDIFACT transactions using similar XML/spec files

### 4. Validation Enhancement
Use field metadata for better validation:
- Check values against valid_codes lists
- Validate data types (numeric vs alphanumeric)
- Check lengths against min/max

### 5. Segment Descriptions
Add segment-level descriptions:
```json
{
  "segment_id": "BPR",
  "segment_name": "Financial Information",
  "segment_description": "To indicate the beginning of a Payment Order/Remittance Advice Transaction Set and total payment amount, or to enable related transfer of funds and/or information from payer to payee to occur"
}
```

### 6. Auto-Generate Documentation
Create HTML/PDF documentation from field database:
- Transaction structure diagrams
- Field reference tables
- Usage examples
- Code value lookups

## Success Metrics

- [ ] Successfully parse all 37 XML implementation guides
- [ ] Build complete field database for 5010 and 4010
- [ ] Transform 835 and 837 JSON with human-readable names
- [ ] Support all 3 output formats (replace, dual, nested)
- [ ] API remains backward compatible
- [ ] Transformation adds < 100ms overhead
- [ ] Database files < 10MB total
- [ ] 100% coverage of available XML fields

## Timeline Estimate

**Total**: 7-10 days

- XML Parser: 1-2 days
- Database Builder: 1 day
- JSON Transformer: 1-2 days
- API Integration: 1 day
- Testing: 1-2 days
- Documentation: 1 day
- Polish & Optimization: 1-2 days

## Next Steps

1. Review this plan and get approval
2. Choose preferred output format (recommend: dual mode)
3. Start with Phase 1: XML Parser
4. Build incrementally and test with 835/837 files
5. Expand to other transaction types once core is working

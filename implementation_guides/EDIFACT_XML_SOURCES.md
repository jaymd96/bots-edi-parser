# EDIFACT XML Implementation Guide Sources

## Summary

EDIFACT (UN/EDIFACT) XML schemas and implementation guides are available from multiple sources. Unlike X12 which has a single consolidated repository (imsweb/x12-parser), EDIFACT resources are distributed across several repositories and official sources.

## Primary Sources

### 1. Microsoft BizTalk Integration Repository (BEST OPTION)
**URL**: https://github.com/microsoft/Integration

**Path**: `BizTalk Server/Schema/EDIFACT/`

**License**: MIT License (free to use)

**Coverage**:
- **36 EDIFACT versions** from D00A through D99B
- Includes D93A, D94A, D94B, D95A, D95B, D96A, D96B, D97A, D97B, D98A, D98B, D99A, D99B
- Also includes D00-D10 series (D00A, D00B, D01A, D01B, D02A, D02B, etc.)
- **XSD schema format** (not plain XML like X12, but XML Schema Definition)
- **Hundreds of message types** per version

**Message Types Available**:

#### D96A (125 message types)
APERAK, AUTHOR, BANSTA, BAPLIE, BAPLTE, BOPBNK, BOPCUS, BOPDIR, BOPINF, CALINF, COARRI, CODECO, CODENO, COEDOR, COHAOR, COMDIS, CONAPW, CONDPV, CONDRA, CONDRO, CONEST, CONITT, CONPVA, CONQVA, CONRPW, CONTEN, CONWQD, COPARN, COPINO, COPRAR, COREOR, COSTCO, COSTOR, CREADV, CREEXT, CREMUL, CUSCAR, CUSDEC, CUSEXP, CUSREP, CUSRES, DEBADV, DEBMUL, DELFOR, DELJIT, DESADV, DIRDEB, DIRDEF, DOCADV, DOCAMA, DOCAMI, DOCAMR, DOCAPP, DOCARE, DOCINF, FINCAN, FINSTA, GENRAL, GESMES, HANMOV, IFCSUM, IFTCCA, IFTDGN, IFTFCC, IFTIAG, IFTMAN, IFTMBC, IFTMBF, IFTMBP, IFTMCS, IFTMIN, IFTRIN, IFTSAI, IFTSTA, IFTSTQ, INSPRE, INVOIC, INVRPT, JAPRES, JINFDE, JOBAPP, JOBCON, JOBMOD, JOBOFF, MEDPID, MOVINS, ORDCHG, ORDERS, ORDRSP, PARTIN, PAXLST, PAYDUC, PAYEXT, PAYMUL, PAYORD, PRICAT, PRODEX, PRPAID, QALITY, QUOTES, RDRMES, RECADV, RECECO, RECLAM, REMADV, REQDOC, REQOTE, RESETT, RESMSG, RETACC, SAFHAZ, SANCRT, SLSFCT, SLSRPT, SSIMOD, SSRECH, SSREGW, STATAC, SUPCOT, SUPMAN, SUPRES, TANSTA, VESDEP, WKGRDC, WKGRRE

#### D96B (136 message types)
All D96A messages PLUS: CASINT, CASRES, DESTIM, ITRRPT, MEDREQ, MEDRPT, PRODAT, REBORD, RECALC, REPREM, VATDEC

#### D01B (194 message types)
All D96B messages PLUS many more including: BALANC, BERMAN, BMISRM, BUSCRD, CHACCO, CLASET, CNTCND, COACSU, COLREQ, COPAYM, CUSPED, DEBREC, DGRECA, DMRDEF, DMSTAT, ENTREC, FINPAY, ICASRP, ICSOLI, IFTICL, IFTMCA, IMPDEF, INFCON, INFENT, INSDES, INSREQ, INSRPT, IPPOAD, IPPOMO, ISENDS, JUPREQ, LEDGER, LREACT, LRECLM, MEDPRE, MEDRUC, MEQPOS, MSCONS, OSTENQ, OSTRPT, PRIHIS, PROCST, PROINQ, PROSRV, PROTAP, RECORD, REGENT, RELIST, RETANN, RETINS, RPCALL, SOCADE, STLRPT, TAXCON, TPFREP, UTILMD, UTILTS, WASDIS

**Advantages**:
✅ Free and open source (MIT License)
✅ Comprehensive coverage of versions and message types
✅ Well-maintained Microsoft repository
✅ XSD format can be parsed to extract element definitions
✅ Covers the versions you have grammars for (D96A, D96B, D01B, etc.)

**Disadvantages**:
❌ XSD format is different from X12 XML implementation guides
❌ May not have element descriptions (just structure definitions)
❌ Designed for BizTalk, not general EDI parsing

### 2. php-edifact/edifact-mapping
**URL**: https://github.com/php-edifact/edifact-mapping

**License**: LGPL-3.0

**Coverage**:
- XML files for EDIFACT messages
- Rebuilt from UNECE UNTDID (UN Trade Data Interchange Directory)
- Unknown which versions are included (need to explore repository)

**Advantages**:
✅ Open source
✅ Rebuilt from official UN data
✅ XML format (not XSD)

**Disadvantages**:
❌ Unclear version coverage
❌ Less actively maintained than Microsoft repo
❌ Need to explore to understand structure

### 3. Official UN/CEFACT UNTDID (BEST FOR SEGMENT DESCRIPTIONS)
**URL**: https://service.unece.org/trade/untdid/

**Direct Access**:
- D96A: https://service.unece.org/trade/untdid/d96a/trsd/trsdi1.htm
- D96B: https://service.unece.org/trade/untdid/d96b/trsd/trsdi1.htm
- D01B: https://service.unece.org/trade/untdid/d01b/trsd/trsdi1.htm
- Latest (D24A): https://service.unece.org/trade/untdid/d24a/trsd/trsdi1.htm

**Coverage**:
- **D96A**: 118 segments
- **D96B**: 223 segments
- **D01B**: ~260 segments
- **D24A**: 204 segments
- All standard EDIFACT versions from 1990s to present

**Format**: HTML pages with structured segment definitions

**Content for Each Segment**:
- Segment code and human-readable name (e.g., NAD = "Name and Address")
- Function/description text
- Field elements with:
  - Position number (010, 020, etc.)
  - Data element code (3035, C082, etc.)
  - Human-readable field name (e.g., "Party Qualifier", "Party Identification Details")
  - Data type (an..3 = alphanumeric up to 3 chars, a..35 = alpha up to 35 chars)
  - Mandatory/Conditional status
  - Composite element sub-fields

**Example Segment Structure** (NAD from D96A):
```
NAD - Name and Address

010  3035  Party Qualifier                      an..3   Mandatory
020  C082  Party Identification Details         —       Conditional
        3039  Party ID identification           an..35  Mandatory
        1131  Code list qualifier               an..3   Conditional
        3055  Code list responsible agency      an..3   Conditional
030  C058  Name and Address (unstructured)      —       Conditional
040  C080  Party Name                           —       Conditional
050  C059  Street                               —       Conditional
060  3164  City Name                            an..35  Conditional
070  3229  Country sub-entity ID                an..9   Conditional
080  3251  Postcode ID                          an..9   Conditional
090  3207  Country Code                         an..3   Conditional
```

**Advantages**:
✅ Official authoritative source
✅ Human-readable segment names and descriptions
✅ Complete field-level details with data types
✅ Covers all versions you have grammars for (D96A, D96B, D01B)
✅ HTML format is easy to parse
✅ Free and publicly accessible
✅ Composite element hierarchies clearly defined

**Disadvantages**:
❌ HTML format requires web scraping
❌ Individual page per segment (118-260 pages per version)
❌ Not downloadable as bulk data files
❌ May need rate limiting to avoid server overload

### 4. DFDLSchemas/EDIFACT
**URL**: https://github.com/DFDLSchemas/EDIFACT

**Coverage**:
- DFDL schemas for EDIFACT syntax version 4.1
- Service segments and common elements
- XSD format

**Advantages**:
✅ Structured schema definitions
✅ Open source

**Disadvantages**:
❌ Limited to service segments
❌ Not full message type coverage
❌ Designed for DFDL processors

## Comparison with Your Grammars

You have EDIFACT grammars for these versions:
```bash
edi_parser/edi_parser/grammars/edifact/
├── D96A/
├── D96B/
├── D01B/
└── ... (possibly others)
```

**Microsoft BizTalk has XSD schemas for ALL these versions!**

## Common EDIFACT Message Types

### Commercial/Trade
- **INVOIC** - Invoice
- **ORDERS** - Purchase Order
- **ORDRSP** - Purchase Order Response
- **DESADV** - Despatch Advice
- **PRICAT** - Price/Sales Catalogue
- **QUOTES** - Quotation
- **DELFOR** - Delivery Schedule
- **REMADV** - Remittance Advice

### Financial
- **BANSTA** - Banking Status
- **PAYORD** - Payment Order
- **PAYMUL** - Multiple Payment Order
- **FINSTA** - Financial Statement

### Transport/Logistics
- **IFTMIN** - Instruction Message
- **IFTSTA** - Status Report
- **IFTMAN** - Arrival Notice
- **IFCSUM** - Forwarding and Consolidation Summary

### Healthcare (if applicable)
- **MEDPID** - Medical Product Information
- **MEDREQ** - Medical Service Request
- **MEDRPT** - Medical Service Report

## XSD vs Implementation Guide XML

### XSD (Microsoft BizTalk)
```xml
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="EFACT_D96A_INVOIC">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="UNH" type="..."/>
        <xs:element name="BGM" type="..."/>
        <!-- Structure definitions -->
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>
```

**Purpose**: Define valid XML structure for EDIFACT messages
**Content**: Element structure, data types, cardinality
**Missing**: Human-readable descriptions, field names

### Implementation Guide XML (like X12 imsweb)
```xml
<segment xid="BGM">
  <name>Beginning of Message</name>
  <element xid="BGM01">
    <name>Document/message name, coded</name>
    <usage>R</usage>
  </element>
</segment>
```

**Purpose**: Document message structure with descriptions
**Content**: Field names, descriptions, usage codes
**Better for**: Human-readable mapping

## Extraction Strategy

### For Microsoft BizTalk XSDs

**Challenge**: XSD files define structure but may lack element descriptions

**Approach**:
1. Parse XSD to extract element IDs (BGM01, BGM02, etc.)
2. Cross-reference with UNECE UNTDID for element descriptions
3. Build mapping database from both sources

**Alternative**: Use php-edifact/edifact-mapping if it has better descriptions

### For UN/CEFACT Official Specs

**Challenge**: Text-based format, not XML

**Approach**:
1. Download official directories
2. Parse text specifications
3. Extract segment and element definitions
4. Convert to structured format

## Recommended Download Strategy

### Priority 1: UN/CEFACT UNTDID (Human-Readable Names) ⭐
**Download segment definitions from official UN source for:**
- D96A (118 segments)
- D96B (223 segments)
- D01B (~260 segments)

**What to extract:**
- Segment codes and human-readable names
- Field element names and descriptions
- Data types and mandatory/conditional status
- Composite element structures

**Method**: Web scraping HTML pages
- Index page: `/trsd/trsdi1.htm`
- Individual segments: `/trsd/trsd{segment}.htm` (e.g., `/trsd/trsdnad.htm`)

### Priority 2: Microsoft BizTalk (Structure Validation)
**Download XSD files for structural definitions:**
- D96A XSD schemas
- D96B XSD schemas
- D01B XSD schemas

**Use for**: Validating message structures, understanding loops and hierarchies

### Priority 3: php-edifact/edifact-mapping (Investigation)
Explore this repository to compare with UN/CEFACT data

## Download Commands

### UN/CEFACT UNTDID Segment Definitions

**Challenge**: Individual HTML pages for each segment (600+ pages total across 3 versions)

**Solution Options**:

**Option 1: Python Web Scraper (Recommended)**
```python
# Create script: download_edifact_segments.py
import requests
from bs4 import BeautifulSoup
import json
import time

versions = {
    'd96a': 'https://service.unece.org/trade/untdid/d96a/trsd/',
    'd96b': 'https://service.unece.org/trade/untdid/d96b/trsd/',
    'd01b': 'https://service.unece.org/trade/untdid/d01b/trsd/'
}

for version, base_url in versions.items():
    # 1. Fetch index page to get list of segments
    index = requests.get(base_url + 'trsdi1.htm')
    # 2. Parse segment links
    # 3. For each segment, fetch detail page
    # 4. Extract segment name, fields, data types, status
    # 5. Save as JSON
    time.sleep(0.5)  # Rate limiting
```

**Option 2: Manual Download Helper**
```bash
# Download index pages first
wget https://service.unece.org/trade/untdid/d96a/trsd/trsdi1.htm
wget https://service.unece.org/trade/untdid/d96b/trsd/trsdi1.htm
wget https://service.unece.org/trade/untdid/d01b/trsd/trsdi1.htm

# Then use script to parse HTML and get segment links
# Then bulk download all segment pages
```

**Expected Output Structure**:
```json
{
  "version": "D96A",
  "segments": {
    "NAD": {
      "name": "Name and Address",
      "function": "To specify the name/address and their related function...",
      "fields": [
        {
          "position": "010",
          "code": "3035",
          "name": "Party Qualifier",
          "data_type": "an..3",
          "status": "Mandatory"
        },
        {
          "position": "020",
          "code": "C082",
          "name": "Party Identification Details",
          "data_type": "composite",
          "status": "Conditional",
          "sub_elements": [...]
        }
      ]
    }
  }
}
```

### Microsoft BizTalk Repository

Since GitHub doesn't allow direct directory downloads, options:

**Option 1: Clone entire repository**
```bash
git clone https://github.com/microsoft/Integration.git
cd Integration
# XSD files are in: BizTalk Server/Schema/EDIFACT/
```

**Option 2: Use GitHub sparse checkout (selective clone)**
```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/microsoft/Integration.git
cd Integration
git sparse-checkout set "BizTalk Server/Schema/EDIFACT/D96A"
git sparse-checkout add "BizTalk Server/Schema/EDIFACT/D96B"
git sparse-checkout add "BizTalk Server/Schema/EDIFACT/D01B"
```

**Option 3: Download specific files via raw GitHub URLs**
```bash
# Example for D96A INVOIC
curl -O https://raw.githubusercontent.com/microsoft/Integration/master/BizTalk%20Server/Schema/EDIFACT/D96A/EFACT_D96A_INVOIC.xsd
```

**Option 4: Use a GitHub downloader tool**
- https://download-directory.github.io/
- Paste directory URL to download as ZIP

## Next Steps

1. **Download UN/CEFACT segment definitions** (PRIORITY)
   - Create web scraper for D96A, D96B, D01B
   - Extract all segment names and field descriptions
   - Save as structured JSON files

2. **Download Microsoft BizTalk XSDs** (SUPPLEMENTARY)
   - Use sparse checkout for D96A, D96B, D01B
   - Use for understanding message structures and loops

3. **Build EDIFACT field mapper**:
   - Parse UN/CEFACT JSON to create segment/field database
   - Implement transformation functions similar to X12 plan
   - Support both segment-level and field-level human-readable names

4. **Integration**:
   - Add EDIFACT support to human-readable mapping API
   - Test with parsed EDIFACT messages
   - Validate against grammars

## Structure of XSD Files

Based on Microsoft BizTalk XSDs, each file defines:
- Root element (message type)
- Segment sequence and structure
- Element data types
- Cardinality (min/max occurrences)

**May NOT include**:
- Human-readable element names
- Element descriptions
- Usage notes
- Code value lists

**Will need supplementary data from**:
- UNECE UNTDID directories
- php-edifact/edifact-mapping
- Manual documentation of common fields

## Comparison: X12 vs EDIFACT Resources

| Aspect | X12 (imsweb) | EDIFACT (Microsoft) |
|--------|--------------|---------------------|
| **Format** | Implementation Guide XML | XSD Schema |
| **Coverage** | ~28 transaction types | 100+ message types per version |
| **Versions** | Specific (835.5010.X221.A1) | By directory (D96A, D96B, etc.) |
| **Descriptions** | Yes, embedded | Limited/none |
| **Field Names** | Human-readable | Element codes only |
| **License** | Apache 2.0 | MIT |
| **Use Case** | Documentation | Schema validation |

## Conclusion

For EDIFACT human-readable field mapping, use a **two-source approach**:

### Primary Source: UN/CEFACT UNTDID ⭐
**Best for**: Human-readable segment names, field descriptions, data types
- Complete coverage of all your grammar versions (D96A, D96B, D01B)
- Official authoritative source
- Detailed field-level information with mandatory/conditional status
- Composite element hierarchies clearly defined
- **Limitation**: Requires web scraping ~600 HTML pages

### Supplementary Source: Microsoft BizTalk
**Best for**: Message structure definitions, loops, XSD validation
- Pre-formatted XSD files (easier to download)
- Good for understanding message hierarchies
- **Limitation**: May lack human-readable field descriptions

### Recommended Approach
1. **Use UN/CEFACT** for building the field mapping database (segment names → field names → descriptions)
2. **Use Microsoft BizTalk** for validating message structures and understanding loops
3. **Combine both** for comprehensive EDIFACT support

The mapping effort for EDIFACT will be **similar complexity to X12**, but requires web scraping instead of parsing pre-existing XML files.

"""
X12 Segment and Field Definitions

Provides access to X12 segment structures with human-readable field names
from imsweb/x12-parser implementation guides.

Supported transactions and versions:
- 835 (Healthcare Claim Payment) - 4010, 5010
- 837 (Healthcare Claim) - 4010, 5010
- Plus 270, 271, 276, 277, 278, 820, 834, etc.

Example usage:
    >>> from edi_parser.field_mappings.x12 import get_segment
    >>> bpr = get_segment('BPR', '835', '5010')
    >>> print(bpr['name'])
    'Financial Information'
    >>> print(bpr['elements'][0]['name'])
    'Transaction Handling Code'
"""

from .segments import (
    get_segment,
    get_element,
    list_segments,
    list_transactions,
    SegmentDatabase,
)

__all__ = [
    'get_segment',
    'get_element',
    'list_segments',
    'list_transactions',
    'SegmentDatabase',
]

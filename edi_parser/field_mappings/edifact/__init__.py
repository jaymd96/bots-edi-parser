"""
EDIFACT Segment Definitions

Provides access to EDIFACT segment structures with human-readable field names
from UN/CEFACT UNTDID directories.

Supported versions:
- D96A (1996 Release A) - 127 segments
- D96B (1996 Release B) - 136 segments
- D01B (2001 Release B) - 158 segments

Example usage:
    >>> from edi_parser.field_mappings.edifact import get_segment
    >>> nad = get_segment('NAD', 'D96A')
    >>> print(nad['name'])
    'NAME AND ADDRESS'
    >>> print(nad['fields'][0]['name'])
    'PARTY QUALIFIER'
"""

from .segments import (
    get_segment,
    get_field,
    list_segments,
    list_versions,
    search_segments,
    SegmentDatabase,
)

__all__ = [
    'get_segment',
    'get_field',
    'list_segments',
    'list_versions',
    'search_segments',
    'SegmentDatabase',
]

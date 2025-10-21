"""
Field mapping database for EDI standards (X12 and EDIFACT)

This package provides human-readable field names and descriptions for:
- EDIFACT segment definitions
- X12 implementation guides (future)
"""

from .edifact import get_segment, get_field, list_segments, list_versions, search_segments

__all__ = [
    'get_segment',
    'get_field',
    'list_segments',
    'list_versions',
    'search_segments',
]

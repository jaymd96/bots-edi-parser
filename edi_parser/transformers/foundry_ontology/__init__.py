"""
Ontology Transformers

Transforms parsed EDI JSON into structured ontology schemas.

Supports:
- 837P Professional Claims → Claims, Services, Diagnoses, Providers, Payers
- 835 Electronic Remittance Advice → Denials, Reason Codes
"""

from .transform_837p import transform_837p
from .transform_835 import transform_835

__all__ = [
    'transform_837p',
    'transform_835',
]

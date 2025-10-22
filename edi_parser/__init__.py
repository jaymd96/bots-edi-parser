"""
EDI Parser - Standalone EDI parsing library extracted from Bots
Supports EDIFACT, X12, CSV, XML, JSON, TRADACOMS, IDOC and more
"""

__version__ = '1.0.4'
__author__ = 'Extracted from Bots EDI Translator'

# Install 'bots' compatibility module so grammar files can import from 'bots'
import sys
from . import bots as _bots_compat
sys.modules['bots'] = _bots_compat

# Import main API functions
from .api import (
    parse_edi,
    parse_edi_file_path,
    node_to_dict,
    get_supported_formats,
    validate_edi,
    validate_edi_file_path,
    parse,  # Alias
    parse_file,  # Alias
    validate,  # Alias
    validate_file,  # Alias
)

# Import transformer functions
from .transformers import add_human_readable_names, transform_837p, transform_835

# Import exceptions that users might want to catch
from .core.exceptions import (
    BotsError,
    InMessageError,
    MessageError,
    GrammarError,
    BotsImportError,
)

__all__ = [
    # Main API
    'parse_edi',
    'parse_edi_file_path',
    'node_to_dict',
    'get_supported_formats',
    'validate_edi',
    'validate_edi_file_path',
    'parse',
    'parse_file',
    'validate',
    'validate_file',
    # Transformers
    'add_human_readable_names',
    'transform_837p',
    'transform_835',
    # Exceptions
    'BotsError',
    'InMessageError',
    'MessageError',
    'GrammarError',
    'BotsImportError',
    # Version
    '__version__',
]

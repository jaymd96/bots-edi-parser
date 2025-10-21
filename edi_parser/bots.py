"""
Compatibility module to allow grammar files to import from 'bots'
The grammars were designed for the original Bots package and import like:
    from bots.botsconfig import ID, MIN, MAX
    from bots import grammarfunctions

This module provides those imports by redirecting to the edi_parser equivalents.
"""

import sys

# Re-export everything from botsconfig at module level
from .core.config import *  # noqa: F401, F403

# Make botsconfig importable as bots.botsconfig
from .core import config
# Install as submodule
sys.modules['bots.botsconfig'] = config

# Store reference
botsconfig = config

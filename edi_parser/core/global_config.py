"""
Global configuration for EDI Parser
Replaces botsglobal from Bots
"""

import logging
import os


class SimpleIni:
    """
    Simple configuration class to replace ConfigParser
    Provides getint, getboolean, get methods
    """

    def __init__(self):
        self.config = {
            'settings': {
                'debug': False,
                'max_number_errors': 10,
                'readrecorddebug': False,
            },
            'directories': {
                'usersys': 'grammars',
                'usersysabs': os.path.join(os.path.dirname(__file__), '..', 'grammars'),
            },
            'acceptance': {
                'runacceptancetest': False,
            }
        }

    def get(self, section, key, default=None):
        """Get a string value"""
        try:
            return self.config[section][key]
        except KeyError:
            return default

    def getint(self, section, key, default=0):
        """Get an integer value"""
        try:
            return int(self.config[section][key])
        except (KeyError, ValueError, TypeError):
            return default

    def getboolean(self, section, key, default=False):
        """Get a boolean value"""
        try:
            val = self.config[section][key]
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ('true', '1', 'yes', 'on')
            return bool(val)
        except (KeyError, ValueError, TypeError):
            return default

    def set(self, section, key, value):
        """Set a value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value


class GlobalConfig:
    """
    Global configuration object to replace botsglobal
    """

    def __init__(self):
        # Initialize loggers
        self.logger = logging.getLogger('edi_parser')
        self.logmap = logging.getLogger('edi_parser.mapping')

        # Set default logging level
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.WARNING)

        # Initialize configuration
        self.ini = SimpleIni()

        # Set for tracking failed imports
        self.not_import = set()

        # Version
        self.version = '1.0.0'

        # usersysimportpath for grammar imports
        self.usersysimportpath = 'edi_parser.grammars'


# Global instance
config = GlobalConfig()


# For backward compatibility, provide individual attributes
logger = config.logger
logmap = config.logmap
ini = config.ini
not_import = config.not_import
version = config.version
usersysimportpath = config.usersysimportpath

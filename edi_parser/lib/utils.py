"""
Utility functions for EDI Parser
Extracted from Bots botslib.py
"""

import importlib
import os
import logging

from ..core.exceptions import BotsImportError, ScriptImportError


# Simple gettext replacement
def gettext(text):
    """Simple gettext implementation - just return the text"""
    return text


def updateunlessset(updatedict, fromdict):
    """
    Update dict with values from another dict,
    but only if the key is not already set.
    """
    updatedict.update(
        (key, value)
        for key, value in fromdict.items()
        if not updatedict.get(key)
    )


def get_relevant_text_for_UnicodeError(exc):
    """Extract relevant text from UnicodeError for error messages"""
    start = exc.start - 10 if exc.start >= 10 else 0
    return exc.object[start: exc.end + 35]


def botsbaseimport(modulename, filepath=None):
    """
    Do a dynamic import.
    Errors/exceptions are handled in calling functions.
    If filepath is provided, use spec_from_file_location (for modules with numeric names).
    """
    if filepath:
        # Use spec_from_file_location for modules with names that aren't valid Python identifiers
        spec = importlib.util.spec_from_file_location(modulename, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        raise ImportError(f"Could not load module from {filepath}")
    return importlib.import_module(modulename)


def botsimport(typeofgrammarfile, editype, grammarname):
    """
    Import grammar modules.
    return: imported module, filename imported module;
    if not found or error in module: raise

    Args:
        typeofgrammarfile: Type of grammar file ('grammars', 'envelope', 'partners')
        editype: EDI type (e.g., 'edifact', 'x12')
        grammarname: Name of the grammar file
    """
    from ..core import global_config as botsglobal

    logger = logging.getLogger('edi_parser')

    # Assemble import string - use relative import from grammars
    # For X12 implementation guides, check version subdirectory first
    grammar_path = os.path.join(os.path.dirname(__file__), '..', 'grammars')

    # Try to detect version subdirectory for X12 grammars
    if editype == 'x12' and len(grammarname) >= 4:
        # Extract version from grammar name (last 4-6 digits before 'X' if present)
        if 'X' in grammarname:
            base = grammarname.split('X')[0]
        else:
            base = grammarname

        # Version is last 4 digits of base (e.g., "5010" from "835005010")
        if len(base) >= 4:
            version = base[-4:]
            version_path = os.path.join(grammar_path, editype, version, grammarname + '.py')

            if os.path.exists(version_path):
                modulepath = f'edi_parser.grammars.{editype}.{version}.{grammarname}'
                modulefile = version_path
                logger.debug(f'Found X12 grammar in version subdirectory: {version}/{grammarname}')
            else:
                # Fall back to flat structure
                modulepath = f'edi_parser.grammars.{editype}.{grammarname}'
                modulefile = os.path.join(grammar_path, editype, grammarname + '.py')
        else:
            modulepath = f'edi_parser.grammars.{editype}.{grammarname}'
            modulefile = os.path.join(grammar_path, editype, grammarname + '.py')
    else:
        modulepath = f'edi_parser.grammars.{editype}.{grammarname}'
        modulefile = os.path.join(grammar_path, editype, grammarname + '.py')

    # Check if previous import failed (no need to try again)
    if modulepath in botsglobal.not_import:
        errs = f'No import of module "{modulefile}".'
        logger.debug(errs)
        raise BotsImportError(errs)

    try:
        # First try normal import
        module = botsbaseimport(modulepath)

    except (ImportError, SyntaxError) as exc:
        # If import failed and file exists, try loading via filepath
        # This handles grammars with numeric names (like 835005010X221A1) which aren't valid Python identifiers
        if os.path.exists(modulefile):
            try:
                logger.debug(f'Standard import failed, trying filepath import for "{grammarname}"')
                module = botsbaseimport(modulepath, modulefile)
                logger.info(f'Loaded grammar "{grammarname}" via filepath')
                return module, modulefile
            except Exception as filepath_exc:
                logger.debug(f'Filepath import also failed: {filepath_exc}')
                # Fall through to original error handling

        # Original error handling continues below
        botsglobal.not_import.add(modulepath)

        # Try fallback for X12 implementation guides
        # X12 implementation guides follow pattern: {trans}{version}X{ig}
        # e.g., "835005010X221A1" -> base grammar "835005010" in version dir "5010"
        if editype == 'x12' and 'X' in grammarname and grammarname.count('X') == 1:
            base_grammarname = grammarname.split('X')[0]
            # Extract version from base grammar name (last 4 digits: "5010" from "835005010")
            if len(base_grammarname) >= 4:
                version = base_grammarname[-4:]
                logger.debug(f'Grammar "{grammarname}" not found, trying fallback to "{base_grammarname}" in version "{version}"')

                try:
                    # Retry with base grammar in version subdirectory
                    modulepath_fallback = f'edi_parser.grammars.{editype}.{version}.{base_grammarname}'
                    module = botsbaseimport(modulepath_fallback)
                    modulefile_fallback = os.path.join(grammar_path, editype, version, base_grammarname + '.py')
                    logger.info(f'Using fallback grammar: {version}/{base_grammarname} for requested {grammarname}')
                    return module, modulefile_fallback
                except ImportError:
                    logger.debug(f'Fallback grammar "{version}/{base_grammarname}" also not found')
                    pass  # Continue to raise original error

        errs = f'No import of module "{modulefile}": {exc}.'
        logger.debug(errs)
        _exception = BotsImportError(errs)
        _exception.__cause__ = None
        raise _exception from exc

    except Exception as exc:
        errs = f'Error in import of module "{modulefile}":\\n{exc}'
        logger.debug(errs)
        _exception = ScriptImportError(errs)
        _exception.__cause__ = None
        raise _exception from exc

    logger.debug(f'Imported "{modulefile}".')
    return module, modulefile


def rreplace(org, old, new='', count=1):
    """
    String handling:
    replace old with new in org, max count times.
    with default values: remove last occurrence of old in org.
    """
    lijst = org.rsplit(old, count)
    return new.join(lijst)


# File reading functions - these work with content passed directly, not from disk
def readdata(filename=None, charset='utf-8', errors='strict', content=None):
    """
    Read data - either from passed content or filename.
    In our standalone parser, content should be passed directly.
    """
    if content is not None:
        if isinstance(content, bytes):
            return content.decode(charset, errors)
        return content
    raise NotImplementedError("File reading not yet implemented - pass content directly")


def readdata_bin(filename=None, content=None):
    """Read binary data"""
    if content is not None:
        if isinstance(content, str):
            return content.encode('utf-8')
        return content
    raise NotImplementedError("File reading not yet implemented - pass content directly")


def readdata_pickled(filename=None):
    """Read pickled data - not supported in standalone parser"""
    raise NotImplementedError("Pickled data not supported in standalone parser")

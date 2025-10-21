"""
Main API for EDI Parser
Provides simple interface to parse EDI files and return JSON
"""

import logging
from typing import Union, Dict, Any, Optional

from .core import inmessage
from .core.exceptions import MessageError
from .core import global_config
from .core import error_formatter


def node_to_dict(node) -> Dict[str, Any]:
    """
    Convert a Node tree to a dictionary (JSON-serializable)

    Args:
        node: Node object from parsed EDI

    Returns:
        dict: Dictionary representation of the node tree
    """
    if node.record is None:
        # Empty root - return children as list
        return {
            'children': [node_to_dict(child) for child in node.children]
        }

    result = dict(node.record)

    # Add children if they exist
    if node.children:
        result['_children'] = [node_to_dict(child) for child in node.children]

    return result


def parse_edi(
    content: Union[str, bytes],
    editype: str,
    messagetype: str,
    charset: str = 'utf-8',
    filename: str = 'edi_file',
    field_validation_mode: str = 'lenient',
    empty_segment_handling: str = 'skip',
    **options
) -> Dict[str, Any]:
    """
    Parse EDI content and return JSON representation

    Args:
        content: EDI file content (string or bytes)
        editype: Type of EDI (e.g., 'edifact', 'x12', 'csv', 'xml', 'json')
        messagetype: Message type/grammar name (e.g., 'ORDERS', 'INVOIC', '850')
        charset: Character encoding (default: 'utf-8')
        filename: Filename for error reporting (default: 'edi_file')
        field_validation_mode: How to handle field validation errors (default: 'lenient')
            - 'strict': Fail on any field validation error
            - 'lenient': Log validation errors but continue parsing
            - 'skip': Don't perform field validation
        empty_segment_handling: How to handle empty segments (default: 'skip')
            - 'error': Raise error on empty segments
            - 'skip': Silently skip empty segments
            - 'warn': Log warning and skip empty segments
        **options: Additional parsing options:
            - debug (bool): Enable debug logging
            - allow_flexible_optional_order (bool): Allow optional segments in any order (default: True)
            - checkunknownentities (bool): Validate unknown fields (default: True)
            - continue_on_error (bool): Continue parsing on non-fatal errors (default: False)

    Returns:
        dict: Parsed EDI as nested dictionary with the following structure:
            {
                'success': bool,          # Whether parsing succeeded
                'data': dict,            # Parsed EDI tree (if success=True)
                'errors': list,          # List of error messages (if any)
                'message_count': int,    # Number of messages found
                'editype': str,         # EDI type
                'messagetype': str      # Message type
            }

    Example:
        >>> with open('invoice.edi', 'r') as f:
        ...     result = parse_edi(
        ...         content=f.read(),
        ...         editype='edifact',
        ...         messagetype='INVOIC'
        ...     )
        >>> if result['success']:
        ...     print(result['data'])
    """
    # Set up logging level if debug is requested
    if options.get('debug', False):
        global_config.logger.setLevel(logging.DEBUG)
        global_config.logmap.setLevel(logging.DEBUG)

    # Prepare ta_info dictionary for inmessage
    ta_info = {
        'editype': editype,
        'messagetype': messagetype,
        'charset': charset,
        'filename': filename,
        'checkunknownentities': options.get('checkunknownentities', True),
        'allow_flexible_optional_order': options.get('allow_flexible_optional_order', True),
        'field_validation_mode': field_validation_mode,
        'empty_segment_handling': empty_segment_handling,
        'has_structure': True,  # Most EDI formats have structure
        '_edi_content': content,  # Pass content directly
    }

    # Add any additional options to ta_info
    for key, value in options.items():
        if key not in ta_info:
            ta_info[key] = value

    result = {
        'success': False,
        'data': None,
        'errors': [],
        'message_count': 0,
        'editype': editype,
        'messagetype': messagetype
    }

    ediobject = None
    try:
        # Parse the EDI file
        ediobject = inmessage.parse_edi_file(**ta_info)

        # Check for fatal errors
        if ediobject.errorfatal:
            result['errors'] = ediobject.errorlist
            result['success'] = False
            return result

        # Check for non-fatal errors
        try:
            ediobject.checkforerrorlist()
        except MessageError as e:
            result['errors'].append(str(e))
            # Continue even with non-fatal errors if requested
            if not options.get('continue_on_error', False):
                return result

        # Convert the parsed tree to dictionary
        if ediobject.root:
            result['data'] = node_to_dict(ediobject.root)
            result['message_count'] = ediobject.messagecount
            result['success'] = True
        else:
            result['errors'].append('No data parsed from EDI file')

    except Exception as e:
        result['errors'].append(f'Parse error: {str(e)}')
        if options.get('debug', False):
            import traceback
            result['errors'].append(traceback.format_exc())

        # Try to extract partial data even on error
        if ediobject and hasattr(ediobject, 'root') and ediobject.root:
            try:
                result['data'] = node_to_dict(ediobject.root)
                result['message_count'] = getattr(ediobject, 'messagecount', 0)
                result['success'] = True  # Mark as success if we got partial data
                result['errors'].append('Note: Partial data returned due to structure validation errors with fallback grammar')
            except Exception:
                pass  # If we can't extract data, just leave it as failed

    return result


def parse_edi_file_path(
    filepath: str,
    editype: str,
    messagetype: str,
    charset: str = 'utf-8',
    field_validation_mode: str = 'lenient',
    empty_segment_handling: str = 'skip',
    **options
) -> Dict[str, Any]:
    """
    Parse an EDI file from a file path

    Args:
        filepath: Path to EDI file
        editype: Type of EDI (e.g., 'edifact', 'x12', 'csv', 'xml', 'json')
        messagetype: Message type/grammar name
        charset: Character encoding (default: 'utf-8')
        field_validation_mode: 'strict', 'lenient', or 'skip' (default: 'lenient')
        empty_segment_handling: 'error', 'skip', or 'warn' (default: 'skip')
        **options: Additional parsing options

    Returns:
        dict: Parsed EDI as nested dictionary (same format as parse_edi)

    Example:
        >>> result = parse_edi_file_path(
        ...     filepath='invoice.edi',
        ...     editype='edifact',
        ...     messagetype='INVOIC'
        ... )
    """
    with open(filepath, 'rb') as f:
        content = f.read()

    import os
    filename = os.path.basename(filepath)

    return parse_edi(
        content=content,
        editype=editype,
        messagetype=messagetype,
        charset=charset,
        filename=filename,
        field_validation_mode=field_validation_mode,
        empty_segment_handling=empty_segment_handling,
        **options
    )


def get_supported_formats():
    """
    Get list of supported EDI formats

    Returns:
        dict: Dictionary of supported formats with descriptions
    """
    return {
        'edifact': 'UN/EDIFACT - United Nations Electronic Data Interchange',
        'x12': 'ANSI X12 - American National Standards Institute X12',
        'csv': 'CSV - Comma Separated Values',
        'fixed': 'Fixed-width record format',
        'xml': 'XML - Extensible Markup Language',
        'json': 'JSON - JavaScript Object Notation',
        'tradacoms': 'TRADACOMS - Trading Data Communications Standard',
        'idoc': 'SAP IDOC - Intermediate Document',
    }


def validate_edi(
    content: Union[str, bytes],
    editype: str,
    messagetype: str,
    charset: str = 'utf-8',
    filename: str = 'edi_file',
    **options
) -> Dict[str, Any]:
    """
    Validate EDI content and return ALL errors in structured, human-readable format

    This function focuses on comprehensive error detection, finding all validation
    issues rather than stopping at the first error.

    Args:
        content: EDI file content (string or bytes)
        editype: Type of EDI (e.g., 'edifact', 'x12', 'csv', 'xml', 'json')
        messagetype: Message type/grammar name (e.g., 'ORDERS', 'INVOIC', '850', '835005010')
        charset: Character encoding (default: 'utf-8')
        filename: Filename for error reporting (default: 'edi_file')
        **options: Additional options:
            - debug (bool): Enable debug logging

    Returns:
        dict: Validation results with structured error information:
            {
                'valid': bool,           # True if no errors found
                'error_count': int,      # Total number of errors
                'errors': [              # List of structured error objects
                    {
                        'code': 'F06',
                        'severity': 'error',  # 'critical', 'error', 'warning'
                        'category': 'field_validation',  # 'structure', 'field_validation', 'format', 'parsing'
                        'location': {
                            'line': 5,
                            'position': 123,
                            'segment': 'BPR',
                            'field': 'BPR10',
                            'path': 'ST/BPR/BPR10'
                        },
                        'message': '[F06] Field too small...',  # Technical message
                        'description': 'The bank account number must be...',  # Plain English
                        'expected': '10 characters minimum',
                        'actual': '9 characters',
                        'value': '123456789',
                        'suggestion': 'Verify the account number is complete...'
                    },
                    ...
                ],
                'summary': str,          # Human-readable summary
                'editype': str,          # EDI type
                'messagetype': str       # Message type
            }

    Example:
        >>> result = validate_edi(
        ...     content=edi_content,
        ...     editype='x12',
        ...     messagetype='835005010'
        ... )
        >>> print(f"Valid: {result['valid']}")
        >>> for error in result['errors']:
        ...     print(f"{error['severity'].upper()}: {error['description']}")
        ...     print(f"  Suggestion: {error['suggestion']}")
    """
    # Set up logging level if debug is requested
    if options.get('debug', False):
        global_config.logger.setLevel(logging.DEBUG)
        global_config.logmap.setLevel(logging.DEBUG)

    # Prepare ta_info dictionary for inmessage with validation mode enabled
    ta_info = {
        'editype': editype,
        'messagetype': messagetype,
        'charset': charset,
        'filename': filename,
        'checkunknownentities': options.get('checkunknownentities', True),
        'allow_flexible_optional_order': options.get('allow_flexible_optional_order', True),
        'field_validation_mode': 'lenient',  # Collect errors, don't raise
        'empty_segment_handling': 'skip',     # Skip empty segments
        'validate_only': True,                # NEW: Enable validation mode
        'has_structure': True,
        '_edi_content': content,
    }

    # Add any additional options to ta_info
    for key, value in options.items():
        if key not in ta_info:
            ta_info[key] = value

    result = {
        'valid': True,
        'error_count': 0,
        'errors': [],
        'summary': '',
        'editype': editype,
        'messagetype': messagetype
    }

    ediobject = None
    try:
        # Parse the EDI file in validation mode
        ediobject = inmessage.parse_edi_file(**ta_info)

        # Check for errors - in validate_only mode, errors don't raise exceptions
        # They're collected in errorlist
        if ediobject.errorlist:
            result['valid'] = False
            result['error_count'] = len(ediobject.errorlist)

            # Enrich errors with metadata and human-readable descriptions
            result['errors'] = error_formatter.enrich_error_list(ediobject.errorlist)

            # Create summary
            result['summary'] = error_formatter.format_error_summary(result['errors'])
        else:
            result['summary'] = 'No errors found. Transaction is valid.'

    except Exception as e:
        # Even in validation mode, fatal errors (like file not found, grammar missing) can occur
        result['valid'] = False
        result['error_count'] = 1
        error_str = f'[FATAL] {str(e)}'

        # Try to enrich this error too
        try:
            enriched = error_formatter.enrich_error(error_str)
            result['errors'] = [enriched]
        except Exception:
            # If enrichment fails, return raw error
            result['errors'] = [{
                'code': 'FATAL',
                'severity': 'critical',
                'category': 'parsing',
                'location': {},
                'message': error_str,
                'description': str(e),
                'expected': None,
                'actual': None,
                'value': None,
                'suggestion': 'Check that the file format and message type are correct.'
            }]

        result['summary'] = f"Critical error: {str(e)}"

        if options.get('debug', False):
            import traceback
            result['summary'] += '\n\n' + traceback.format_exc()

    return result


def validate_edi_file_path(
    filepath: str,
    editype: str,
    messagetype: str,
    charset: str = 'utf-8',
    **options
) -> Dict[str, Any]:
    """
    Validate an EDI file from a file path

    Args:
        filepath: Path to EDI file
        editype: Type of EDI (e.g., 'edifact', 'x12')
        messagetype: Message type/grammar name
        charset: Character encoding (default: 'utf-8')
        **options: Additional validation options

    Returns:
        dict: Validation results (same format as validate_edi)

    Example:
        >>> result = validate_edi_file_path(
        ...     filepath='invoice.edi',
        ...     editype='x12',
        ...     messagetype='835005010'
        ... )
        >>> print(result['summary'])
    """
    with open(filepath, 'rb') as f:
        content = f.read()

    import os
    filename = os.path.basename(filepath)

    return validate_edi(
        content=content,
        editype=editype,
        messagetype=messagetype,
        charset=charset,
        filename=filename,
        **options
    )


# Convenience function aliases
parse = parse_edi
parse_file = parse_edi_file_path
validate = validate_edi
validate_file = validate_edi_file_path

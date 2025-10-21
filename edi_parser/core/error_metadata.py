"""
Error metadata for EDI validation
Maps error codes to categories, severities, descriptions, and suggestions
"""

# Error categories
CATEGORY_STRUCTURE = 'structure'
CATEGORY_FIELD = 'field_validation'
CATEGORY_FORMAT = 'format'
CATEGORY_PARSING = 'parsing'

# Severity levels
SEVERITY_CRITICAL = 'critical'  # Prevents parsing
SEVERITY_ERROR = 'error'        # Violates EDI standard
SEVERITY_WARNING = 'warning'    # Data quality issue

# Error code metadata
# Each entry contains: category, severity, description_template, suggestion_template
ERROR_METADATA = {
    # Structure errors (S01-S04)
    'S01': {
        'category': CATEGORY_STRUCTURE,
        'severity': SEVERITY_ERROR,
        'description': 'Record "{record}" has children but should not according to the grammar definition.',
        'suggestion': 'Check the EDI structure. This record should be a simple segment without nested elements. Remove any child segments or review the grammar specification.',
    },
    'S02': {
        'category': CATEGORY_STRUCTURE,
        'severity': SEVERITY_ERROR,
        'description': 'Unknown record "{record}" found in the message. This segment is not defined in the grammar for this transaction type.',
        'suggestion': 'Verify the segment ID is correct. Check if you\'re using the right message type/version. Remove this segment if it\'s not required, or add it to the grammar definition.',
    },
    'S03': {
        'category': CATEGORY_STRUCTURE,
        'severity': SEVERITY_ERROR,
        'description': 'Record "{record}" appears {count} times but must appear at least {min} times according to the grammar.',
        'suggestion': 'Add the missing required occurrences of this segment. Check the implementation guide for minimum occurrences.',
    },
    'S04': {
        'category': CATEGORY_STRUCTURE,
        'severity': SEVERITY_ERROR,
        'description': 'Record "{record}" appears {count} times but can only appear at most {max} times according to the grammar.',
        'suggestion': 'Remove extra occurrences of this segment or consolidate the data. Check the implementation guide for maximum occurrences.',
    },
    'S50': {
        'category': CATEGORY_STRUCTURE,
        'severity': SEVERITY_CRITICAL,
        'description': 'Record "{record}" is not allowed at this position in the message structure. Expected "{expected}" next.',
        'suggestion': 'Reorder the segments to match the required structure, or check if required segments are missing before this one.',
    },

    # Field errors (F01-F47)
    'F01': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Record "{record}" contains unknown field "{field}". This field is not defined in the grammar.',
        'suggestion': 'Remove this field if it\'s not needed, or verify you\'re using the correct transaction version. Check the field name for typos.',
    },
    'F02': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Mandatory field "{field}" in record "{record}" is missing or empty.',
        'suggestion': 'Provide a value for this required field. Check the implementation guide for what data should be included.',
    },
    'F03': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Mandatory composite "{field}" in record "{record}" is missing or empty.',
        'suggestion': 'Provide values for this required composite field. A composite contains multiple sub-elements.',
    },
    'F04': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Mandatory subfield "{field}" in record "{record}" is missing or empty.',
        'suggestion': 'Provide a value for this required subfield within the composite element.',
    },
    'F05': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Field "{field}" in record "{record}" is too large. Maximum length is {max} characters, but {length} characters were provided.',
        'suggestion': 'Shorten the field value to {max} characters or fewer. Truncate or abbreviate the data as needed.',
    },
    'F06': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Field "{field}" in record "{record}" is too small. Minimum length is {min} characters, but only {length} characters were provided.',
        'suggestion': 'Extend the field value to at least {min} characters. For numeric fields, add leading zeros. For text fields, verify the complete value is present.',
    },
    'F07': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Date field "{field}" in record "{record}" contains invalid date "{value}". Expected format: YYMMDD or YYYYMMDD.',
        'suggestion': 'Correct the date format. Use YYMMDD (6 digits) or YYYYMMDD (8 digits). Verify the date is valid (e.g., not February 30th).',
    },
    'F08': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Time field "{field}" in record "{record}" contains invalid time "{value}". Expected format: HHMM or HHMMSS.',
        'suggestion': 'Correct the time format. Use HHMM (4 digits) or HHMMSS (6 digits). Verify hours are 00-23 and minutes/seconds are 00-59.',
    },
    'F09': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Fixed decimal field "{field}" in record "{record}" has incorrect decimal precision. Expected {expected} decimal places.',
        'suggestion': 'Adjust the number of decimal places to match the specification. Add trailing zeros or round as needed.',
    },
    'F10': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Alphanumeric field "{field}" in record "{record}" contains characters that are not allowed.',
        'suggestion': 'Remove or replace invalid characters. Ensure only letters, numbers, and allowed special characters are used.',
    },
    'F11': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Numeric field "{field}" in record "{record}" contains non-numeric characters: "{value}".',
        'suggestion': 'Remove non-numeric characters. For decimal numbers, use only digits and a single decimal point. For integers, use only digits.',
    },
    'F12': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Integer field "{field}" in record "{record}" must not contain a decimal point.',
        'suggestion': 'Remove the decimal portion. Round or truncate the value to a whole number as appropriate.',
    },
    'F14': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Numeric field "{field}" in record "{record}" has too many digits after the decimal point.',
        'suggestion': 'Round the value to the allowed number of decimal places.',
    },
    'F15': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Numeric field "{field}" in record "{record}" has too many digits before the decimal point.',
        'suggestion': 'The value exceeds the maximum allowed. Reduce the value or verify it\'s correct.',
    },
    'F16': {
        'category': CATEGORY_FORMAT,
        'severity': SEVERITY_ERROR,
        'description': 'Numeric field "{field}" in record "{record}" contains multiple decimal points.',
        'suggestion': 'Correct the value to have only one decimal point, or remove all decimal points for integer fields.',
    },

    # Repeating field errors
    'F41': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Mandatory repeating field "{field}" in record "{record}" is missing.',
        'suggestion': 'Add at least one occurrence of this repeating field.',
    },
    'F42': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Repeating field "{field}" in record "{record}" exceeds maximum allowed repetitions.',
        'suggestion': 'Reduce the number of repetitions to the maximum allowed.',
    },
    'F43': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Mandatory subfield in repeating field "{field}" in record "{record}" is missing.',
        'suggestion': 'Provide values for all mandatory subfields in each repetition.',
    },
    'F44': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Mandatory repeating composite "{field}" in record "{record}" is missing.',
        'suggestion': 'Add at least one occurrence of this repeating composite field.',
    },
    'F45': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Repeating composite "{field}" in record "{record}" exceeds maximum allowed repetitions.',
        'suggestion': 'Reduce the number of composite repetitions to the maximum allowed.',
    },
    'F46': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Mandatory subfield in repeating composite "{field}" in record "{record}" is missing.',
        'suggestion': 'Provide values for all mandatory subfields in each composite repetition.',
    },
    'F47': {
        'category': CATEGORY_FIELD,
        'severity': SEVERITY_ERROR,
        'description': 'Subfield count in repeating composite "{field}" in record "{record}" is incorrect.',
        'suggestion': 'Ensure each composite repetition has the correct number of subfields.',
    },

    # Parsing errors (A50-A69)
    'A50': {
        'category': CATEGORY_PARSING,
        'severity': SEVERITY_WARNING,
        'description': 'Non-valid data found at end of EDI file after position {pos} on line {line}.',
        'suggestion': 'Remove trailing data after the final segment terminator. Check for extra characters or incomplete segments.',
    },
    'A59': {
        'category': CATEGORY_PARSING,
        'severity': SEVERITY_CRITICAL,
        'description': 'File contains characters that are not allowed in the specified character set at or after position {pos}.',
        'suggestion': 'Ensure the file encoding matches the declared character set. Remove or replace invalid characters.',
    },
    'A60': {
        'category': CATEGORY_PARSING,
        'severity': SEVERITY_CRITICAL,
        'description': 'Expected "{expected}" but found "{found}". The file may not be valid {editype} format.',
        'suggestion': 'Verify the file is in the correct EDI format. Check the interchange envelope structure.',
    },
    'A68': {
        'category': CATEGORY_PARSING,
        'severity': SEVERITY_WARNING,
        'description': 'Empty segment found at line {line}, position {pos}.',
        'suggestion': 'Remove empty segments (consecutive segment terminators). Ensure each segment has data.',
    },
    'A69': {
        'category': CATEGORY_PARSING,
        'severity': SEVERITY_ERROR,
        'description': 'Double record separator found at line {line}, position {pos}. This creates an empty segment.',
        'suggestion': 'Remove the extra segment terminator. Each segment should be terminated exactly once.',
    },

    # Envelope errors (E20)
    'E20': {
        'category': CATEGORY_STRUCTURE,
        'severity': SEVERITY_ERROR,
        'description': 'Segment count in trailer does not match actual count. Trailer claims {trailer_count} but {actual_count} segments were found.',
        'suggestion': 'Correct the segment count in the SE/GE/IEA trailer segment to match the actual number of segments.',
    },
}


def get_error_metadata(error_code):
    """
    Get metadata for an error code

    Args:
        error_code: Error code like 'F06', 'S50', etc.

    Returns:
        dict with category, severity, description template, suggestion template
        Returns default metadata if code not found
    """
    # Extract just the code part (F06 from [F06])
    if error_code.startswith('[') and ']' in error_code:
        error_code = error_code[1:error_code.index(']')]

    return ERROR_METADATA.get(error_code, {
        'category': CATEGORY_PARSING,
        'severity': SEVERITY_ERROR,
        'description': 'Unknown error occurred.',
        'suggestion': 'Review the error message for details.',
    })


def categorize_severity(error_code):
    """
    Determine severity level for an error code

    Returns: 'critical', 'error', or 'warning'
    """
    metadata = get_error_metadata(error_code)
    return metadata['severity']


def get_category(error_code):
    """Get the category for an error code"""
    metadata = get_error_metadata(error_code)
    return metadata['category']

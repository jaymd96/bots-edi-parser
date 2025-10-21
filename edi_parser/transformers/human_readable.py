"""
Human-Readable Name Transformer

Adds human-readable field names to parsed EDI JSON output.
"""

from typing import Dict, Any, Optional
from ..field_mappings.x12 import get_segment


def add_human_readable_names(
    parsed_json: Dict[str, Any],
    transaction: str = '835',
    version: str = '5010',
    mode: str = 'dual'
) -> Dict[str, Any]:
    """
    Add human-readable field names to parsed EDI JSON

    Args:
        parsed_json: Parsed EDI output from BOTS parser
        transaction: Transaction type (e.g., '835', '837')
        version: X12 version (e.g., '5010', '4010')
        mode: Output mode
            - 'dual': Keep both technical codes and add readable names (default)
            - 'replace': Replace technical codes with readable names
            - 'metadata': Add full metadata including descriptions

    Returns:
        Transformed JSON with human-readable names

    Example:
        >>> result = parse_edi(content, 'x12', 'envelope')
        >>> readable = add_human_readable_names(result['data'], '835', '5010')
    """
    if not parsed_json:
        return parsed_json

    # Handle the root 'children' wrapper
    if 'children' in parsed_json and isinstance(parsed_json['children'], list):
        return {
            'children': [
                _transform_node(child, transaction, version, mode)
                for child in parsed_json['children']
            ]
        }
    else:
        return _transform_node(parsed_json, transaction, version, mode)


def _transform_node(
    node: Dict[str, Any],
    transaction: str,
    version: str,
    mode: str
) -> Dict[str, Any]:
    """Transform a single node and its children recursively"""
    if not isinstance(node, dict):
        return node

    # Get segment ID
    segment_id = node.get('BOTSID')
    if not segment_id:
        return node

    # Get segment definition
    segment_def = get_segment(segment_id, transaction, version)

    # Create transformed node
    transformed = {}

    # Add segment name
    if mode == 'dual':
        transformed['BOTSID'] = segment_id
        if segment_def and segment_def.get('name'):
            transformed['segment_name'] = segment_def['name']
    elif mode == 'replace':
        if segment_def and segment_def.get('name'):
            transformed['segment_name'] = segment_def['name']
            transformed['segment_id'] = segment_id
        else:
            transformed['BOTSID'] = segment_id
    else:  # metadata mode
        transformed['BOTSID'] = segment_id
        if segment_def:
            transformed['_segment_metadata'] = {
                'name': segment_def.get('name', ''),
                'usage': segment_def.get('usage', ''),
                'id': segment_id
            }

    # Process all fields
    for key, value in node.items():
        if key == 'BOTSID':
            continue  # Already handled

        elif key == '_children':
            # Recursively transform children
            if isinstance(value, list):
                transformed['_children'] = [
                    _transform_node(child, transaction, version, mode)
                    for child in value
                ]
            continue

        elif key.startswith('BOTSIDnr') or key == 'BOTSIDnr':
            # Keep internal tracking fields
            transformed[key] = value
            continue

        # Check if this is a field that needs a name
        if segment_def and _is_field_key(key, segment_id):
            field_name = _get_field_name(key, segment_def)

            if mode == 'dual':
                transformed[key] = value
                if field_name:
                    transformed[f'{key}_name'] = field_name

            elif mode == 'replace':
                if field_name:
                    # Use snake_case version of field name
                    readable_key = _to_snake_case(field_name)
                    transformed[readable_key] = value
                    transformed[f'_{readable_key}_original_id'] = key
                else:
                    transformed[key] = value

            else:  # metadata mode
                transformed[key] = value
                if field_name:
                    elem_def = _get_element_def(key, segment_def)
                    transformed[f'{key}_metadata'] = {
                        'name': field_name,
                        'data_element': elem_def.get('data_element', ''),
                        'usage': elem_def.get('usage', ''),
                        'original_id': key
                    }
        else:
            # Keep field as-is
            transformed[key] = value

    return transformed


def _is_field_key(key: str, segment_id: str) -> bool:
    """Check if a key represents a field (e.g., BPR01, ISA06)"""
    # Pattern: SEGMENTXX or SEGMENT.XX
    return (
        key.startswith(segment_id) and
        len(key) > len(segment_id) and
        (key[len(segment_id):len(segment_id)+2].isdigit() or
         key[len(segment_id)] == '.')
    )


def _get_field_name(field_id: str, segment_def: Dict[str, Any]) -> Optional[str]:
    """Get human-readable name for a field"""
    if not segment_def or 'elements' not in segment_def:
        return None

    for element in segment_def['elements']:
        if element.get('id') == field_id:
            return element.get('name', '')

        # Check sub-elements for composites
        if 'sub_elements' in element:
            for sub in element['sub_elements']:
                # Handle both BPR05.01 and BPR05-01 formats
                sub_id = f"{element.get('id')}.{sub.get('id', '').split('-')[-1]}"
                alt_sub_id = f"{element.get('id')}-{sub.get('id', '').split('-')[-1]}"
                if field_id in (sub_id, alt_sub_id, sub.get('id', '')):
                    return sub.get('name', '')

    return None


def _get_element_def(field_id: str, segment_def: Dict[str, Any]) -> Dict[str, Any]:
    """Get full element definition"""
    if not segment_def or 'elements' not in segment_def:
        return {}

    for element in segment_def['elements']:
        if element.get('id') == field_id:
            return element

        if 'sub_elements' in element:
            for sub in element['sub_elements']:
                sub_id = f"{element.get('id')}.{sub.get('id', '').split('-')[-1]}"
                alt_sub_id = f"{element.get('id')}-{sub.get('id', '').split('-')[-1]}"
                if field_id in (sub_id, alt_sub_id, sub.get('id', '')):
                    return sub

    return {}


def _to_snake_case(text: str) -> str:
    """Convert text to snake_case"""
    # Remove special characters
    text = text.replace('/', '_').replace('-', '_')
    # Split on spaces and join with underscores
    words = text.split()
    return '_'.join(word.lower() for word in words)

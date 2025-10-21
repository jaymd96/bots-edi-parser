#!/usr/bin/env python3
"""
Parse X12 Implementation Guide XMLs and extract field mappings

Processes XML files from imsweb/x12-parser to create a field mapping database
similar to the EDIFACT segment definitions.
"""

import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Dict, List, Any
import re


def parse_element(element_node: ET.Element) -> Dict[str, Any]:
    """Parse an element definition from XML"""
    element_data = {
        'id': element_node.get('xid', ''),
        'data_element': '',
        'name': '',
        'usage': '',
        'seq': '',
        'valid_codes': []
    }

    # Extract child elements
    for child in element_node:
        if child.tag == 'data_ele':
            element_data['data_element'] = (child.text or '').strip()
        elif child.tag == 'name':
            element_data['name'] = (child.text or '').strip()
        elif child.tag == 'usage':
            element_data['usage'] = (child.text or '').strip()
        elif child.tag == 'seq':
            element_data['seq'] = (child.text or '').strip()
        elif child.tag == 'valid_codes':
            codes = [(code.text or '').strip() for code in child.findall('code') if code.text]
            element_data['valid_codes'] = codes

    return element_data


def parse_composite(composite_node: ET.Element) -> Dict[str, Any]:
    """Parse a composite element definition"""
    composite_data = {
        'id': composite_node.get('xid', ''),
        'name': '',
        'usage': '',
        'seq': '',
        'sub_elements': []
    }

    for child in composite_node:
        if child.tag == 'name':
            composite_data['name'] = (child.text or '').strip()
        elif child.tag == 'usage':
            composite_data['usage'] = (child.text or '').strip()
        elif child.tag == 'seq':
            composite_data['seq'] = (child.text or '').strip()
        elif child.tag == 'element':
            sub_element = parse_element(child)
            composite_data['sub_elements'].append(sub_element)

    return composite_data


def parse_segment(segment_node: ET.Element) -> Dict[str, Any]:
    """Parse a segment definition from XML"""
    segment_data = {
        'id': segment_node.get('xid', ''),
        'name': '',
        'usage': '',
        'position': '',
        'max_use': '',
        'elements': []
    }

    for child in segment_node:
        if child.tag == 'name':
            segment_data['name'] = (child.text or '').strip()
        elif child.tag == 'usage':
            segment_data['usage'] = (child.text or '').strip()
        elif child.tag == 'pos':
            segment_data['position'] = (child.text or '').strip()
        elif child.tag == 'max_use':
            segment_data['max_use'] = (child.text or '').strip()
        elif child.tag == 'element':
            element = parse_element(child)
            segment_data['elements'].append(element)
        elif child.tag == 'composite':
            composite = parse_composite(child)
            segment_data['elements'].append(composite)

    return segment_data


def extract_segments_from_xml(xml_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract all segment definitions from an X12 implementation guide XML"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    segments = {}

    # Recursively find all segment nodes
    for segment_node in root.iter('segment'):
        segment_data = parse_segment(segment_node)
        segment_id = segment_data['id']

        # Store by segment ID, merge if already exists
        if segment_id in segments:
            existing = segments[segment_id]
            new_elem_count = len(segment_data['elements'])
            existing_elem_count = len(existing['elements'])

            # Prefer segments with names over those without
            # When element counts are equal, keep the one with a name
            if new_elem_count > existing_elem_count:
                segments[segment_id] = segment_data
            elif new_elem_count == existing_elem_count:
                # If new has name and existing doesn't, use new
                if segment_data['name'] and not existing['name']:
                    segments[segment_id] = segment_data
                # If new has element names and existing doesn't, use new
                elif (segment_data['elements'] and segment_data['elements'][0].get('name')
                      and existing['elements'] and not existing['elements'][0].get('name')):
                    segments[segment_id] = segment_data
        else:
            segments[segment_id] = segment_data

    return segments


def main():
    """Parse all X12 XMLs and create field mapping database"""
    print("X12 Implementation Guide XML Parser")
    print("=" * 60)

    xml_dir = Path('implementation_guides')
    output_dir = Path('edi_parser/field_mappings/x12/data')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find all X12 XML files (exclude control and support files)
    xml_files = sorted(xml_dir.glob('*.xml'))
    exclude_patterns = ['control', 'dataele', 'codes', 'maps']
    xml_files = [
        f for f in xml_files
        if not any(pattern in f.stem.lower() for pattern in exclude_patterns)
    ]

    print(f"Found {len(xml_files)} X12 implementation guide files\n")

    # Group by transaction type and version
    by_transaction = {}

    for xml_file in xml_files:
        print(f"Processing: {xml_file.name}")

        try:
            segments = extract_segments_from_xml(xml_file)

            # Extract transaction type from filename (e.g., "835.5010.X221.A1.xml" -> "835")
            match = re.match(r'(\d+)', xml_file.stem)
            if match:
                trans_type = match.group(1)
            else:
                trans_type = xml_file.stem

            # Extract version (5010 or 4010)
            if '5010' in xml_file.stem:
                version = '5010'
            elif '4010' in xml_file.stem:
                version = '4010'
            else:
                version = 'unknown'

            key = f"{trans_type}_{version}"

            if key not in by_transaction:
                by_transaction[key] = {
                    'transaction_type': trans_type,
                    'version': version,
                    'filename': xml_file.name,
                    'segments': {}
                }

            # Merge segments
            for seg_id, seg_data in segments.items():
                if seg_id not in by_transaction[key]['segments']:
                    by_transaction[key]['segments'][seg_id] = seg_data
                else:
                    # Merge, preferring segments with names
                    existing = by_transaction[key]['segments'][seg_id]
                    new_elem_count = len(seg_data['elements'])
                    existing_elem_count = len(existing['elements'])

                    if new_elem_count > existing_elem_count:
                        by_transaction[key]['segments'][seg_id] = seg_data
                    elif new_elem_count == existing_elem_count:
                        # Prefer segments with names
                        if seg_data['name'] and not existing['name']:
                            by_transaction[key]['segments'][seg_id] = seg_data
                        elif (seg_data['elements'] and seg_data['elements'][0].get('name')
                              and existing['elements'] and not existing['elements'][0].get('name')):
                            by_transaction[key]['segments'][seg_id] = seg_data

            print(f"  Extracted {len(segments)} segments")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Save individual transaction files
    print(f"\n{'=' * 60}")
    print("Saving transaction-specific files...")

    for key, data in by_transaction.items():
        output_file = output_dir / f"{key}_segments.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        segment_count = len(data['segments'])
        print(f"  {key}: {segment_count} segments -> {output_file.name}")

    # Create a consolidated common segments file (segments that appear in multiple transactions)
    print(f"\n{'=' * 60}")
    print("Creating common segments database...")

    # Count segment occurrences
    segment_counts = {}
    all_segments = {}

    for trans_data in by_transaction.values():
        for seg_id, seg_data in trans_data['segments'].items():
            if seg_id not in segment_counts:
                segment_counts[seg_id] = 0
                all_segments[seg_id] = seg_data
            segment_counts[seg_id] += 1

            # Keep most detailed version
            if len(seg_data['elements']) > len(all_segments[seg_id]['elements']):
                all_segments[seg_id] = seg_data

    # Common segments (appear in 3+ transactions)
    common_segments = {
        seg_id: seg_data
        for seg_id, seg_data in all_segments.items()
        if segment_counts[seg_id] >= 3
    }

    common_file = output_dir / 'common_segments.json'
    with open(common_file, 'w', encoding='utf-8') as f:
        json.dump({
            'description': 'Common X12 segments appearing in multiple transaction types',
            'segments': common_segments
        }, f, indent=2, ensure_ascii=False)

    print(f"  Common segments: {len(common_segments)} -> {common_file.name}")

    print(f"\n{'=' * 60}")
    print(f"Processing complete!")
    print(f"Created {len(by_transaction)} transaction-specific files")
    print(f"Created 1 common segments file")
    print(f"Output directory: {output_dir}")


if __name__ == '__main__':
    main()

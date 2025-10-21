"""
EDIFACT Segment Database

Loads and provides access to EDIFACT segment definitions from JSON data files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class SegmentDatabase:
    """
    EDIFACT segment definition database

    Loads segment definitions from JSON files and provides query methods.
    """

    def __init__(self):
        """Initialize the database (lazy loading)"""
        self._data: Dict[str, Dict] = {}
        self._data_dir = Path(__file__).parent / 'data'

    def _load_version(self, version: str) -> None:
        """Load a specific version's data if not already loaded"""
        version_key = version.upper()

        if version_key in self._data:
            return  # Already loaded

        # Map version to filename
        filename = f"{version.lower()}_segments.json"
        filepath = self._data_dir / filename

        if not filepath.exists():
            raise ValueError(
                f"Version {version} not found. "
                f"Available versions: {', '.join(self.list_versions())}"
            )

        with open(filepath, 'r', encoding='utf-8') as f:
            self._data[version_key] = json.load(f)

    def list_versions(self) -> List[str]:
        """List all available EDIFACT versions"""
        if not self._data_dir.exists():
            return []

        versions = []
        for filepath in self._data_dir.glob('*_segments.json'):
            # Extract version from filename (e.g., 'd96a_segments.json' -> 'D96A')
            version = filepath.stem.replace('_segments', '').upper()
            versions.append(version)

        return sorted(versions)

    def get_segment(self, segment_code: str, version: str = 'D01B') -> Optional[Dict[str, Any]]:
        """
        Get segment definition

        Args:
            segment_code: 3-letter segment code (e.g., 'NAD', 'BGM')
            version: EDIFACT version (default: 'D01B')

        Returns:
            Dictionary with segment definition or None if not found

        Example:
            >>> db = SegmentDatabase()
            >>> nad = db.get_segment('NAD', 'D96A')
            >>> print(nad['name'])
            'NAME AND ADDRESS'
        """
        self._load_version(version)

        version_key = version.upper()
        segment_key = segment_code.upper()

        return self._data[version_key]['segments'].get(segment_key)

    def get_field(
        self,
        segment_code: str,
        position: str,
        version: str = 'D01B'
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific field definition from a segment

        Args:
            segment_code: 3-letter segment code (e.g., 'NAD')
            position: Field position (e.g., '010', '020')
            version: EDIFACT version (default: 'D01B')

        Returns:
            Dictionary with field definition or None if not found

        Example:
            >>> db = SegmentDatabase()
            >>> field = db.get_field('NAD', '010', 'D96A')
            >>> print(field['name'])
            'PARTY QUALIFIER'
        """
        segment = self.get_segment(segment_code, version)

        if not segment:
            return None

        for field in segment.get('fields', []):
            if field['position'] == position:
                return field

        return None

    def list_segments(self, version: str = 'D01B') -> List[str]:
        """
        List all segment codes for a version

        Args:
            version: EDIFACT version (default: 'D01B')

        Returns:
            List of 3-letter segment codes

        Example:
            >>> db = SegmentDatabase()
            >>> segments = db.list_segments('D96A')
            >>> print(len(segments))
            127
        """
        self._load_version(version)

        version_key = version.upper()
        return sorted(self._data[version_key]['segments'].keys())

    def search_segments(
        self,
        name_pattern: str,
        version: str = 'D01B'
    ) -> List[Dict[str, str]]:
        """
        Search segments by name pattern

        Args:
            name_pattern: Case-insensitive substring to search for
            version: EDIFACT version (default: 'D01B')

        Returns:
            List of dicts with 'code' and 'name' keys

        Example:
            >>> db = SegmentDatabase()
            >>> results = db.search_segments('address', 'D96A')
            >>> print(results[0])
            {'code': 'NAD', 'name': 'NAME AND ADDRESS'}
        """
        self._load_version(version)

        version_key = version.upper()
        pattern_lower = name_pattern.lower()

        results = []
        for code, segment in self._data[version_key]['segments'].items():
            if pattern_lower in segment['name'].lower():
                results.append({
                    'code': code,
                    'name': segment['name']
                })

        return results

    def get_field_by_code(
        self,
        segment_code: str,
        element_code: str,
        version: str = 'D01B'
    ) -> Optional[Dict[str, Any]]:
        """
        Get field by element code instead of position

        Args:
            segment_code: 3-letter segment code
            element_code: Data element code (e.g., '3035', 'C082')
            version: EDIFACT version

        Returns:
            Field definition or None

        Example:
            >>> db = SegmentDatabase()
            >>> field = db.get_field_by_code('NAD', '3035', 'D96A')
            >>> print(field['name'])
            'PARTY QUALIFIER'
        """
        segment = self.get_segment(segment_code, version)

        if not segment:
            return None

        for field in segment.get('fields', []):
            if field['code'] == element_code:
                return field

        return None


# Module-level convenience functions using a shared instance
_db = SegmentDatabase()


def get_segment(segment_code: str, version: str = 'D01B') -> Optional[Dict[str, Any]]:
    """
    Get segment definition (convenience function)

    Args:
        segment_code: 3-letter segment code (e.g., 'NAD', 'BGM')
        version: EDIFACT version (default: 'D01B')

    Returns:
        Dictionary with segment definition or None if not found
    """
    return _db.get_segment(segment_code, version)


def get_field(
    segment_code: str,
    position: str,
    version: str = 'D01B'
) -> Optional[Dict[str, Any]]:
    """
    Get specific field definition (convenience function)

    Args:
        segment_code: 3-letter segment code
        position: Field position (e.g., '010', '020')
        version: EDIFACT version (default: 'D01B')

    Returns:
        Dictionary with field definition or None if not found
    """
    return _db.get_field(segment_code, position, version)


def list_segments(version: str = 'D01B') -> List[str]:
    """
    List all segment codes (convenience function)

    Args:
        version: EDIFACT version (default: 'D01B')

    Returns:
        List of 3-letter segment codes
    """
    return _db.list_segments(version)


def list_versions() -> List[str]:
    """
    List all available EDIFACT versions

    Returns:
        List of version strings (e.g., ['D96A', 'D96B', 'D01B'])
    """
    return _db.list_versions()


def search_segments(name_pattern: str, version: str = 'D01B') -> List[Dict[str, str]]:
    """
    Search segments by name (convenience function)

    Args:
        name_pattern: Case-insensitive substring to search for
        version: EDIFACT version (default: 'D01B')

    Returns:
        List of dicts with 'code' and 'name' keys
    """
    return _db.search_segments(name_pattern, version)

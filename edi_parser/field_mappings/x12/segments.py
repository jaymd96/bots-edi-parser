"""
X12 Segment Database

Loads and provides access to X12 segment definitions from JSON data files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class SegmentDatabase:
    """
    X12 segment definition database

    Loads segment definitions from JSON files and provides query methods.
    """

    def __init__(self):
        """Initialize the database (lazy loading)"""
        self._data: Dict[str, Dict] = {}
        self._data_dir = Path(__file__).parent / 'data'
        self._common: Optional[Dict] = None

    def _load_transaction(self, transaction: str, version: str) -> None:
        """Load a specific transaction's data if not already loaded"""
        key = f"{transaction}_{version}"

        if key in self._data:
            return  # Already loaded

        # Map to filename
        filename = f"{key}_segments.json"
        filepath = self._data_dir / filename

        if not filepath.exists():
            raise ValueError(
                f"Transaction {transaction} version {version} not found. "
                f"Available: {', '.join(self.list_transactions())}"
            )

        with open(filepath, 'r', encoding='utf-8') as f:
            self._data[key] = json.load(f)

    def _load_common(self) -> None:
        """Load common segments database"""
        if self._common is not None:
            return

        common_file = self._data_dir / 'common_segments.json'
        if common_file.exists():
            with open(common_file, 'r', encoding='utf-8') as f:
                self._common = json.load(f)
        else:
            self._common = {'segments': {}}

    def list_transactions(self) -> List[str]:
        """
        List all available transactions

        Returns:
            List of strings like '835_5010', '837_4010'
        """
        if not self._data_dir.exists():
            return []

        transactions = []
        for filepath in self._data_dir.glob('*_segments.json'):
            if 'common' not in filepath.stem:
                # Extract from filename like '835_5010_segments.json'
                trans = filepath.stem.replace('_segments', '')
                transactions.append(trans)

        return sorted(transactions)

    def get_segment(
        self,
        segment_id: str,
        transaction: str = '835',
        version: str = '5010'
    ) -> Optional[Dict[str, Any]]:
        """
        Get segment definition

        Args:
            segment_id: Segment identifier (e.g., 'BPR', 'NM1')
            transaction: Transaction type (e.g., '835', '837')
            version: X12 version (default: '5010')

        Returns:
            Dictionary with segment definition or None if not found

        Example:
            >>> db = SegmentDatabase()
            >>> bpr = db.get_segment('BPR', '835', '5010')
            >>> print(bpr['name'])
            'Financial Information'
        """
        self._load_transaction(transaction, version)

        key = f"{transaction}_{version}"
        segment_key = segment_id.upper()

        segment = self._data[key]['segments'].get(segment_key)

        # Fall back to common segments if not in transaction-specific
        if not segment:
            self._load_common()
            segment = self._common['segments'].get(segment_key)

        return segment

    def get_element(
        self,
        segment_id: str,
        element_id: str,
        transaction: str = '835',
        version: str = '5010'
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific element definition from a segment

        Args:
            segment_id: Segment identifier (e.g., 'BPR')
            element_id: Element ID (e.g., 'BPR01', 'BPR02')
            transaction: Transaction type
            version: X12 version

        Returns:
            Dictionary with element definition or None if not found

        Example:
            >>> db = SegmentDatabase()
            >>> elem = db.get_element('BPR', 'BPR01', '835', '5010')
            >>> print(elem['name'])
            'Transaction Handling Code'
        """
        segment = self.get_segment(segment_id, transaction, version)

        if not segment:
            return None

        for element in segment.get('elements', []):
            if element['id'] == element_id:
                return element

        return None

    def list_segments(
        self,
        transaction: str = '835',
        version: str = '5010'
    ) -> List[str]:
        """
        List all segment IDs for a transaction

        Args:
            transaction: Transaction type
            version: X12 version

        Returns:
            List of segment identifiers

        Example:
            >>> db = SegmentDatabase()
            >>> segments = db.list_segments('835', '5010')
            >>> print(len(segments))
            30
        """
        self._load_transaction(transaction, version)

        key = f"{transaction}_{version}"
        return sorted(self._data[key]['segments'].keys())

    def search_segments(
        self,
        name_pattern: str,
        transaction: str = '835',
        version: str = '5010'
    ) -> List[Dict[str, str]]:
        """
        Search segments by name pattern

        Args:
            name_pattern: Case-insensitive substring to search for
            transaction: Transaction type
            version: X12 version

        Returns:
            List of dicts with 'id' and 'name' keys

        Example:
            >>> db = SegmentDatabase()
            >>> results = db.search_segments('financial', '835', '5010')
            >>> print(results[0])
            {'id': 'BPR', 'name': 'Financial Information'}
        """
        self._load_transaction(transaction, version)

        key = f"{transaction}_{version}"
        pattern_lower = name_pattern.lower()

        results = []
        for seg_id, segment in self._data[key]['segments'].items():
            if pattern_lower in segment['name'].lower():
                results.append({
                    'id': seg_id,
                    'name': segment['name']
                })

        return results


# Module-level convenience functions using a shared instance
_db = SegmentDatabase()


def get_segment(
    segment_id: str,
    transaction: str = '835',
    version: str = '5010'
) -> Optional[Dict[str, Any]]:
    """
    Get segment definition (convenience function)

    Args:
        segment_id: Segment identifier (e.g., 'BPR', 'NM1')
        transaction: Transaction type (default: '835')
        version: X12 version (default: '5010')

    Returns:
        Dictionary with segment definition or None if not found
    """
    return _db.get_segment(segment_id, transaction, version)


def get_element(
    segment_id: str,
    element_id: str,
    transaction: str = '835',
    version: str = '5010'
) -> Optional[Dict[str, Any]]:
    """
    Get specific element definition (convenience function)

    Args:
        segment_id: Segment identifier
        element_id: Element ID (e.g., 'BPR01')
        transaction: Transaction type
        version: X12 version

    Returns:
        Dictionary with element definition or None if not found
    """
    return _db.get_element(segment_id, element_id, transaction, version)


def list_segments(
    transaction: str = '835',
    version: str = '5010'
) -> List[str]:
    """
    List all segment IDs (convenience function)

    Args:
        transaction: Transaction type
        version: X12 version

    Returns:
        List of segment identifiers
    """
    return _db.list_segments(transaction, version)


def list_transactions() -> List[str]:
    """
    List all available transactions

    Returns:
        List of transaction keys like '835_5010', '837_4010'
    """
    return _db.list_transactions()


def search_segments(
    name_pattern: str,
    transaction: str = '835',
    version: str = '5010'
) -> List[Dict[str, str]]:
    """
    Search segments by name (convenience function)

    Args:
        name_pattern: Case-insensitive substring to search for
        transaction: Transaction type
        version: X12 version

    Returns:
        List of dicts with 'id' and 'name' keys
    """
    return _db.search_segments(name_pattern, transaction, version)

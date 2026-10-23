"""engine/apaar_engine/registry.py

Mock APAAR Registry interface and implementation for V003/V004 validation.
- lookup(apaar_id) -> {"name": str, "dob": str} | None

Owned by Team A (Data & Intelligence).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Optional, Protocol, Union


class ApaarRegistryProtocol(Protocol):
    def lookup(self, apaar_id: str) -> Optional[Dict[str, Any]]:
        """Look up student registry details by 12-digit APAAR ID."""
        ...


class MockApaarRegistry:
    """In-memory mock APAAR registry seeded from CSV or dictionary."""

    def __init__(self, records: Optional[Dict[str, Dict[str, Any]]] = None) -> None:
        self._records: Dict[str, Dict[str, Any]] = records or {}

    @classmethod
    def from_csv(cls, csv_path: Union[str, Path]) -> MockApaarRegistry:
        """Seed registry from registry.csv file."""
        records: Dict[str, Dict[str, Any]] = {}
        path = Path(csv_path)
        if not path.exists():
            return cls(records)

        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                apaar = str(row.get("apaar_id", "")).strip()
                if apaar:
                    records[apaar] = {
                        "name": row.get("full_name") or row.get("name", ""),
                        "dob": row.get("dob", ""),
                        "gender": row.get("gender", ""),
                    }
        return cls(records)

    def lookup(self, apaar_id: str) -> Optional[Dict[str, Any]]:
        """Look up student registry record by APAAR ID."""
        if not apaar_id:
            return None
        return self._records.get(str(apaar_id).strip())

    def add_record(self, apaar_id: str, name: str, dob: str, gender: str = "") -> None:
        """Add or update an APAAR registry record."""
        self._records[str(apaar_id).strip()] = {
            "name": name,
            "dob": dob,
            "gender": gender,
        }

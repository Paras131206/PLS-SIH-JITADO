import json
import os
from typing import Optional, Dict, Any
from pathlib import Path

class MockApaarRegistry:
    """Mock APAAR registry for development. Replace with real APAAR API in production."""
    
    def __init__(self, data_path: Optional[str] = None):
        self.registry: Dict[str, Dict[str, Any]] = {}
        if data_path and os.path.exists(data_path):
            self.load_from_file(data_path)
        else:
            self._seed_synthetic_data()
    
    def _seed_synthetic_data(self):
        """Seed with synthetic APAAR records for testing."""
        synthetic_records = {
            "123456789012": {"name": "Rahul Sharma", "dob": "2005-03-15", "gender": "M"},
            "123456789013": {"name": "Priya Patel", "dob": "2004-08-22", "gender": "F"},
            "123456789014": {"name": "Amit Kumar", "dob": "2005-01-10", "gender": "M"},
            "123456789015": {"name": "Sneha Reddy", "dob": "2004-11-05", "gender": "F"},
            "123456789016": {"name": "Vikram Singh", "dob": "2005-06-18", "gender": "M"},
            "123456789017": {"name": "Anjali Gupta", "dob": "2004-09-30", "gender": "F"},
            "123456789018": {"name": "Rohit Verma", "dob": "2005-02-14", "gender": "M"},
            "123456789019": {"name": "Kavya Nair", "dob": "2004-12-25", "gender": "F"},
            "123456789020": {"name": "Arjun Mehta", "dob": "2005-04-07", "gender": "M"},
            "123456789021": {"name": "Meera Joshi", "dob": "2004-10-12", "gender": "F"},
        }
        for apaar_id, data in synthetic_records.items():
            self.registry[apaar_id] = data
    
    def load_from_file(self, data_path: str):
        with open(data_path, 'r') as f:
            data = json.load(f)
            for record in data:
                self.registry[record["apaar_id"]] = record
    
    def lookup(self, apaar_id: str) -> Optional[Dict[str, Any]]:
        """Lookup APAAR ID in registry. Returns record if found, None otherwise."""
        return self.registry.get(apaar_id)
    
    def verify_name_dob(self, apaar_id: str, name: str, dob: str) -> tuple[bool, float]:
        """Verify name and DOB match registry. Returns (match, confidence_score)."""
        record = self.registry.get(apaar_id)
        if not record:
            return False, 0.0
        
        # Simple fuzzy matching for demo
        name_match = name.lower().strip() == record["name"].lower().strip()
        dob_match = dob == record["dob"]
        
        if name_match and dob_match:
            return True, 1.0
        elif name_match or dob_match:
            return True, 0.7
        return False, 0.0
    
    def exists(self, apaar_id: str) -> bool:
        return apaar_id in self.registry


# Global instance
_mock_registry: Optional[MockApaarRegistry] = None


def get_apaar_registry() -> MockApaarRegistry:
    global _mock_registry
    if _mock_registry is None:
        _mock_registry = MockApaarRegistry()
    return _mock_registry
import json
import os
from models.farmer import Farmer
from models.diagnosis import Diagnosis
from models.scheme import Scheme

class StorageService:
    def __init__(self):
        self.original_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        if os.environ.get("VERCEL"):
            self.data_dir = "/tmp/data"
        else:
            self.data_dir = self.original_data_dir
            
        self.farmers_file = os.path.join(self.data_dir, "farmers.json")
        self.history_file = os.path.join(self.data_dir, "diagnosis_history.json")
        self.schemes_file = os.path.join(self.data_dir, "schemes.json")
        self.weather_cache_file = os.path.join(self.data_dir, "weather_cache.json")
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

    def _read_json(self, filepath, default_val):
        if not os.path.exists(filepath):
            # Check if we can copy from the original read-only directory
            filename = os.path.basename(filepath)
            original_path = os.path.join(self.original_data_dir, filename)
            if os.path.exists(original_path):
                try:
                    import shutil
                    shutil.copy2(original_path, filepath)
                except Exception:
                    # Fallback to reading directly from original_path (read-only)
                    try:
                        with open(original_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception:
                        pass
            
            # If not copied, write default and return
            self._write_json(filepath, default_val)
            return default_val
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default_val

    def _write_json(self, filepath, data):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    # Farmer profile operations
    def get_farmer(self, farmer_id):
        farmers = self._read_json(self.farmers_file, {})
        farmer_data = farmers.get(farmer_id)
        if farmer_data:
            return Farmer.from_dict(farmer_data)
        return None

    def save_farmer(self, farmer: Farmer):
        farmers = self._read_json(self.farmers_file, {})
        farmers[farmer.id] = farmer.to_dict()
        return self._write_json(self.farmers_file, farmers)

    # Diagnosis history operations
    def get_history(self, farmer_id=None):
        records = self._read_json(self.history_file, [])
        diagnoses = [Diagnosis.from_dict(r) for r in records]
        if farmer_id:
            return [d for d in diagnoses if d.farmer_id == farmer_id]
        return diagnoses

    def add_diagnosis(self, diagnosis: Diagnosis):
        records = self._read_json(self.history_file, [])
        records.insert(0, diagnosis.to_dict())  # Keep newest at the top
        return self._write_json(self.history_file, records)

    # Government schemes operations
    def get_all_schemes(self):
        schemes_data = self._read_json(self.schemes_file, [])
        return [Scheme.from_dict(s) for s in schemes_data]

    # Weather Cache operations
    def get_weather_cache(self, key):
        cache = self._read_json(self.weather_cache_file, {})
        return cache.get(key)

    def set_weather_cache(self, key, weather_data):
        cache = self._read_json(self.weather_cache_file, {})
        cache[key] = weather_data
        return self._write_json(self.weather_cache_file, cache)

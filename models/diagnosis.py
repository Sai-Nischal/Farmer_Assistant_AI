from datetime import datetime

class Diagnosis:
    def __init__(self, id, farmer_id, crop_type, likely_condition, confidence, symptoms, organic_treatment, chemical_treatment, date=None, image_path=None):
        self.id = id
        self.farmer_id = farmer_id
        self.crop_type = crop_type
        self.likely_condition = likely_condition
        self.confidence = float(confidence) if confidence else 0.0
        self.symptoms = symptoms
        self.organic_treatment = organic_treatment
        self.chemical_treatment = chemical_treatment
        self.date = date or datetime.now().isoformat()
        self.image_path = image_path

    def to_dict(self):
        return {
            "id": self.id,
            "farmer_id": self.farmer_id,
            "crop_type": self.crop_type,
            "likely_condition": self.likely_condition,
            "confidence": self.confidence,
            "symptoms": self.symptoms,
            "organic_treatment": self.organic_treatment,
            "chemical_treatment": self.chemical_treatment,
            "date": self.date,
            "image_path": self.image_path
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            id=data.get("id"),
            farmer_id=data.get("farmer_id"),
            crop_type=data.get("crop_type", ""),
            likely_condition=data.get("likely_condition", ""),
            confidence=data.get("confidence", 0.0),
            symptoms=data.get("symptoms", ""),
            organic_treatment=data.get("organic_treatment", ""),
            chemical_treatment=data.get("chemical_treatment", ""),
            date=data.get("date"),
            image_path=data.get("image_path")
        )

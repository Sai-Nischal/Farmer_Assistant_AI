class Farmer:
    def __init__(self, id, name, village_mandal, land_size_acres=0.0, primary_crop="", category="small_marginal", language="en", voice_enabled=True, phone=None, latitude=None, longitude=None):
        self.id = str(id) if id else ""
        self.name = str(name) if name else ""
        self.village_mandal = str(village_mandal) if village_mandal else ""
        try:
            self.land_size_acres = float(land_size_acres) if land_size_acres is not None and str(land_size_acres).strip() != "" else 0.0
        except (ValueError, TypeError):
            self.land_size_acres = 0.0
            
        self.primary_crop = str(primary_crop) if primary_crop else ""
        
        # Automatically categorise based on land size if not explicitly set
        if category and category in ["small_marginal", "all", "large"]:
            self.category = category
        elif self.land_size_acres > 5.0:
            self.category = "all"
        else:
            self.category = "small_marginal"
            
        self.language = language if language in ["te", "en"] else "en"
        self.voice_enabled = bool(voice_enabled)
        self.phone = str(phone).strip() if phone else None
        
        try:
            self.latitude = float(latitude) if latitude is not None and str(latitude).strip() != "" else None
        except (ValueError, TypeError):
            self.latitude = None
            
        try:
            self.longitude = float(longitude) if longitude is not None and str(longitude).strip() != "" else None
        except (ValueError, TypeError):
            self.longitude = None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "village_mandal": self.village_mandal,
            "land_size_acres": self.land_size_acres,
            "primary_crop": self.primary_crop,
            "category": self.category,
            "language": self.language,
            "voice_enabled": self.voice_enabled,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            village_mandal=data.get("village_mandal", ""),
            land_size_acres=data.get("land_size_acres", 0.0),
            primary_crop=data.get("primary_crop", ""),
            category=data.get("category", "small_marginal"),
            language=data.get("language", "en"),
            voice_enabled=data.get("voice_enabled", True),
            phone=data.get("phone"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude")
        )

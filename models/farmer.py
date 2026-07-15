class Farmer:
    def __init__(self, id, name, village_mandal, land_size_acres, primary_crop, category="small_marginal", language="en", voice_enabled=True):
        self.id = id
        self.name = name
        self.village_mandal = village_mandal
        self.land_size_acres = float(land_size_acres) if land_size_acres else 0.0
        self.primary_crop = primary_crop
        # Automatically categorise based on land size if not explicitly set
        if self.land_size_acres > 5.0:
            self.category = "all"
        else:
            self.category = "small_marginal"
        self.language = language
        self.voice_enabled = voice_enabled

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "village_mandal": self.village_mandal,
            "land_size_acres": self.land_size_acres,
            "primary_crop": self.primary_crop,
            "category": self.category,
            "language": self.language,
            "voice_enabled": self.voice_enabled
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
            voice_enabled=data.get("voice_enabled", True)
        )

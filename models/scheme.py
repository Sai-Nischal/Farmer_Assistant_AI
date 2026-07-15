class Scheme:
    def __init__(self, id, name_en, name_te, category, eligibility, benefit_en, benefit_te, apply_link, how_to_apply_en, how_to_apply_te):
        self.id = id
        self.name_en = name_en
        self.name_te = name_te
        self.category = category
        self.eligibility = eligibility  # dictionary with max_land_acres, min_land_acres, farmer_type, state
        self.benefit_en = benefit_en
        self.benefit_te = benefit_te
        self.apply_link = apply_link
        self.how_to_apply_en = how_to_apply_en
        self.how_to_apply_te = how_to_apply_te

    def to_dict(self):
        return {
            "id": self.id,
            "name_en": self.name_en,
            "name_te": self.name_te,
            "category": self.category,
            "eligibility": self.eligibility,
            "benefit_en": self.benefit_en,
            "benefit_te": self.benefit_te,
            "apply_link": self.apply_link,
            "how_to_apply_en": self.how_to_apply_en,
            "how_to_apply_te": self.how_to_apply_te
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        return cls(
            id=data.get("id"),
            name_en=data.get("name_en", ""),
            name_te=data.get("name_te", ""),
            category=data.get("category", ""),
            eligibility=data.get("eligibility", {}),
            benefit_en=data.get("benefit_en", ""),
            benefit_te=data.get("benefit_te", ""),
            apply_link=data.get("apply_link", ""),
            how_to_apply_en=data.get("how_to_apply_en", ""),
            how_to_apply_te=data.get("how_to_apply_te", "")
        )

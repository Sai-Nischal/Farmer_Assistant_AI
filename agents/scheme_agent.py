import os
import logging
from models.farmer import Farmer

try:
    from google.adk.agents import Agent as ADKAgent
    HAS_ADK = True
except Exception:
    HAS_ADK = False

class SchemeAgent:
    def __init__(self, storage_service, gemini_service):
        self.storage_service = storage_service
        self.gemini_service = gemini_service
        self.name = "SchemeAgent"
        self.instruction = """
        You are the Scheme Eligibility Agent of Rythu Mitra AI.
        Your responsibilities:
        1. Examine the farmer's profile (land size, crop, state, classification).
        2. Filter schemes from the database, recommending only those where the farmer strictly meets the criteria.
        3. Provide a transparent reason of why they qualify (e.g. "Eligible because land is 3 acres (under 5-acre limit for Rythu Bharosa) and you grow Paddy").
        4. Include the official website link for application.
        """
        
        if HAS_ADK:
            try:
                self.adk_agent = ADKAgent(
                    name=self.name,
                    instruction=self.instruction,
                    model="gemini-2.5-flash"
                )
            except Exception as e:
                logging.warning(f"Failed to initialize ADK Agent for {self.name}: {e}")
                self.adk_agent = None
        else:
            self.adk_agent = None

    def evaluate_eligibility(self, farmer: Farmer):
        """Programmatically evaluates schemes matching farmer's criteria to prevent any LLM hallucination."""
        schemes = self.storage_service.get_all_schemes()
        if not schemes:
            return []

        # Safe extraction of farmer attributes
        village = (getattr(farmer, "village_mandal", "") or "").strip().lower() if farmer else ""
        try:
            farmer_land = float(getattr(farmer, "land_size_acres", 0.0) or 0.0) if farmer else 0.0
        except (ValueError, TypeError):
            farmer_land = 0.0
            
        farmer_crop = (getattr(farmer, "primary_crop", "") or "").strip().lower() if farmer else ""
        farmer_cat = (getattr(farmer, "category", "") or "small_marginal") if farmer else "small_marginal"
        
        eligible_schemes = []

        for scheme in schemes:
            elig = getattr(scheme, "eligibility", {}) or {}
            
            # 1. State check
            state_req = elig.get("state", "All") or "All"
            if state_req != "All":
                # If village is unspecified or includes AP, Andhra, or is in AP, permit AP schemes
                is_ap = ("ap" in village or "andhra" in village or village == "" or 
                         any(d in village for d in ["guntur", "vijayawada", "nellore", "kurnool", "anantapur", "kadapa", "tirupati", "visakhapatnam", "vizag", "kakinada", "ongole", "chittoor", "eluru", "srikakulam", "vizianagaram", "amravati", "rajahmundry", "machilipatnam"]))
                if state_req == "Andhra Pradesh" and not is_ap:
                    continue
                elif state_req.lower() not in village and state_req != "Andhra Pradesh":
                    continue

            # 2. Land checks
            try:
                max_land = float(elig.get("max_land_acres") or 0.0)
            except (ValueError, TypeError):
                max_land = 0.0
                
            try:
                min_land = float(elig.get("min_land_acres") or 0.0)
            except (ValueError, TypeError):
                min_land = 0.0
            
            if max_land > 0 and farmer_land > 0 and farmer_land > max_land:
                continue
            if min_land > 0 and farmer_land > 0 and farmer_land < min_land:
                continue

            # 3. Farmer Type check (small/marginal vs large)
            scheme_farmer_type = elig.get("farmer_type", "all") or "all"
            if scheme_farmer_type == "small_marginal" and farmer_cat != "small_marginal" and farmer_land > 5.0:
                continue

            # 4. Crop Category check
            scheme_cat = (getattr(scheme, "category", "") or "All Crops").strip()
            
            # Match if scheme is "All Crops", or matches crop name, or if farmer hasn't specified crop yet
            crop_matched = False
            if scheme_cat.lower() == "all crops" or not farmer_crop or farmer_crop == "all":
                crop_matched = True
            elif scheme_cat.lower() in farmer_crop or farmer_crop in scheme_cat.lower():
                crop_matched = True
            elif scheme_cat.lower() == "organic crops" and "organic" in farmer_crop:
                crop_matched = True
            elif scheme_cat.lower() == "horticulture" and any(h in farmer_crop for h in ["chilli", "tomato", "citrus", "mango", "banana", "vegetable", "fruit"]):
                crop_matched = True

            if not crop_matched:
                continue

            # Generate bilingual explanation
            cat_display = farmer_cat.replace('_', ' ')
            crop_display = farmer_crop.capitalize() if farmer_crop else "All Crops"
            land_display = f"{farmer_land:.1f}" if farmer_land > 0 else "Flexible"

            reason_en = f"Eligible: Land size ({land_display} acres) fits scheme range ({min_land} to {max_land if max_land > 0 else 'No limit'} acres), crop suitability ({crop_display}), and {cat_display} category."
            reason_te = f"అర్హత: మీ భూమి ({land_display} ఎకరాలు), పంట ({crop_display}), మరియు {cat_display} రైతు వర్గానికి ఈ పథకం సరిపోతుంది."
            
            eligible_schemes.append({
                "id": scheme.id,
                "name_en": scheme.name_en,
                "name_te": scheme.name_te,
                "category": scheme.category,
                "benefit_en": scheme.benefit_en,
                "benefit_te": scheme.benefit_te,
                "apply_link": scheme.apply_link,
                "how_to_apply_en": scheme.how_to_apply_en,
                "how_to_apply_te": scheme.how_to_apply_te,
                "reason_en": reason_en,
                "reason_te": reason_te
            })

        return eligible_schemes

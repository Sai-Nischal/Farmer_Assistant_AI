import os
import logging
from models.farmer import Farmer

try:
    from google.adk.agents import Agent as ADKAgent
    HAS_ADK = True
except ImportError:
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
        if not farmer:
            return []

        schemes = self.storage_service.get_all_schemes()
        eligible_schemes = []

        for scheme in schemes:
            elig = scheme.eligibility
            
            # 1. State check
            state_req = elig.get("state", "All")
            if state_req != "All" and state_req.lower() not in farmer.village_mandal.lower() and state_req != "Andhra Pradesh":
                # Assuming all our farmers are in Andhra Pradesh since the application is Rythu Mitra AI
                if "ap" not in farmer.village_mandal.lower() and "andhra" not in farmer.village_mandal.lower():
                    continue # Skip if state doesn't match

            # 2. Land checks
            max_land = elig.get("max_land_acres", 0.0)
            min_land = elig.get("min_land_acres", 0.0)
            
            if max_land > 0 and farmer.land_size_acres > max_land:
                continue
            if min_land > 0 and farmer.land_size_acres < min_land:
                continue

            # 3. Farmer Type check (small/marginal vs large)
            scheme_farmer_type = elig.get("farmer_type", "all")
            if scheme_farmer_type == "small_marginal" and farmer.category != "small_marginal":
                continue

            # 4. Crop Category check
            scheme_cat = scheme.category
            farmer_crop = farmer.primary_crop or "all"
            
            # Match if scheme is "All Crops", or matches crop name
            crop_matched = False
            if scheme_cat.lower() == "all crops":
                crop_matched = True
            elif scheme_cat.lower() in farmer_crop.lower() or farmer_crop.lower() in scheme_cat.lower():
                crop_matched = True
            elif scheme_cat.lower() == "organic crops" and "organic" in farmer_crop.lower():
                crop_matched = True
            elif scheme_cat.lower() == "horticulture" and farmer_crop.lower() in ["chilli", "tomato", "chilli", "citrus", "mango", "banana", "vegetables", "fruit", "fruits"]:
                crop_matched = True

            if not crop_matched:
                continue

            # If it passes all criteria, add explanations
            reason_en = f"Eligible since your land size ({farmer.land_size_acres} acres) is within the required range ({min_land} to {max_land} acres), your crop is '{farmer.primary_crop}', and you are categorized as a {farmer.category.replace('_', ' ')} farmer."
            
            # Custom explanations in English
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
                "reason_en": reason_en
            })

        return eligible_schemes

import os
import json
import logging

try:
    from google.adk.agents import Agent as ADKAgent
    HAS_ADK = True
except ImportError:
    HAS_ADK = False

class AdvisoryAgent:
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        self.name = "AdvisoryAgent"
        self.instruction = """
        You are the Advisory Agent of Rythu Mitra AI.
        Your responsibilities:
        1. Formulate treatment recommendations for a diagnosed crop disease/condition.
        2. Always divide treatments into:
           - Organic Treatment: Bio-control methods, organic manure, neem oil, traditional solutions.
           - Chemical Treatment: Approved chemical fungicides, insecticides, or fertilizers.
        3. Never invent exact chemical chemical dosages (like "apply 3.4g per plant"). Name the recommended active chemical ingredient and advise checking the package label or consulting local officers.
        4. Analyze the weather forecast to provide:
           - Irrigation advice: If rainfall is likely (>= 50% chance in the next 3 days), suggest delaying irrigation.
           - Spraying advice: Suggest skipping spraying if wind speeds are > 15 km/h (risk of drift) or if rain is forecast within 24 hours (will wash off chemicals).
        5. If the request is about livestock (cows, goats, poultry) or falls outside standard crops, immediately flag it and advise consulting a veterinarian.
        6. Return results as a structured JSON object.
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

    def generate_advisory(self, diagnosis_report, weather_forecast, api_key=None):
        """Generates treatment, irrigation, and spray recommendations based on crop diagnosis and weather."""
        prompt = f"""
        Given the following Diagnosis Report:
        {json.dumps(diagnosis_report)}
        
        And the following Weather Forecast:
        {json.dumps(weather_forecast)}
        
        Generate weather-aware agricultural advice.
        Determine:
        1. Organic treatment options (natural, non-chemical, bio-pesticides).
        2. Chemical treatment options (active ingredients, general guidelines - warn to read label for dosages).
        3. Irrigation decision (Should they irrigate? Look at precipitation_probability in days forecast).
        4. Spraying safety (Look at wind_speed_max and precipitation_probability).
        5. Safety Flags (Does it require an agronomist or vet check?).
        
        Format your response EXACTLY as a JSON object with the following keys:
        {{
          "organic_treatment": "string (clear organic recommendations)",
          "chemical_treatment": "string (clear chemical recommendations)",
          "irrigation_status": "green" (safe to irrigate) or "yellow" (monitor weather) or "red" (delay/stop due to rain),
          "irrigation_advice": "string (explanation of irrigation timing based on weather)",
          "spray_status": "green" (safe to spray) or "yellow" (unfavorable wind/light rain) or "red" (do not spray - heavy rain or wind expected),
          "spray_advice": "string (explanation of spraying safety window)",
          "safety_flags": "string (any warnings or escalation notices to vet/agronomist, if none write '')"
        }}
        Do not add any markup or text other than the JSON object.
        """
        try:
            response_text = self.gemini_service.generate_text(prompt, api_key=api_key)
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)
            return data
        except Exception as e:
            logging.error(f"AdvisoryAgent failed to generate advisory: {e}")
            return {
                "organic_treatment": "Keep soil well-drained. Remove infected leaves manually.",
                "chemical_treatment": "Consult local agri officer for appropriate fungicide recommendations.",
                "irrigation_status": "yellow",
                "irrigation_advice": "Verify local sky conditions before irrigating.",
                "spray_status": "yellow",
                "spray_advice": "Avoid spraying if rain is expected in the next few hours.",
                "safety_flags": "Please check pesticide bottle instructions carefully."
            }

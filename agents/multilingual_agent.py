import os
import logging

try:
    from google.adk.agents import Agent as ADKAgent
    HAS_ADK = True
except Exception:
    HAS_ADK = False

class MultilingualAgent:
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        self.name = "MultilingualAgent"
        self.instruction = """
        You are the Multilingual Agent of Rythu Mitra AI.
        Your responsibilities:
        1. Detect whether the input from the farmer is in Telugu (Telugu script), transliterated Telugu (Telugu words written in Latin/English letters, e.g., "mokki rogam vachindi"), or English.
        2. If the input is in Telugu or transliterated Telugu, translate it into standard agricultural English for other agents to process. Preserve core details.
        3. If translating expert English reports/outputs back into Telugu:
           - Use simple, warm, rural-friendly Telugu (rural register) that small farmers in Andhra Pradesh can easily comprehend.
           - Avoid robotic, literal dictionary translations. Keep sentences short and active.
           - Important: Preserve key technical/scientific terms (like disease names, chemical names, or scheme names) by showing them in Telugu/English script alongside a simplified Telugu meaning. E.g., "Late Blight (ఆకుమాడు తెగులు)" or "PM-KISAN scheme (పీఎం కిసాన్ పథకం)".
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

    def detect_and_translate_to_english(self, user_input, api_key=None):
        """Detects language and translates farmer input to English."""
        if not user_input or user_input.strip() == "":
            return "No input provided."
            
        prompt = f"""
        Analyze this farmer's input: "{user_input}"
        1. Detect if it is in Telugu (script), Transliterated Telugu (Latin script), or English.
        2. Translate it to clear, simple English.
        
        Respond ONLY with a JSON object in this format:
        {{
          "detected_lang": "te" or "te-latin" or "en",
          "translated_text": "Translated English query"
        }}
        """
        try:
            response_text = self.gemini_service.generate_text(prompt, api_key=api_key)
            # Standard cleaning of potential JSON markdown code block formatting
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            import json
            data = json.loads(cleaned_response)
            return data
        except Exception as e:
            logging.error(f"Multilingual translation to English failed: {e}")
            # Safe fallback: return input as is with default language
            return {
                "detected_lang": "te",
                "translated_text": user_input
            }

    def translate_to_telugu(self, english_text, api_key=None):
        """Translates final agent outputs to simple Telugu."""
        if not english_text or english_text.strip() == "":
            return ""
            
        prompt = f"""
        Translate the following English agricultural text into friendly, rural Telugu:
        "{english_text}"
        
        Remember:
        - Keep sentences short.
        - Use rural AP register (informal, respectful, clear).
        - Keep technical names intact but explain in brackets: e.g. "Late Blight (ఆకుమాడు తెగులు)".
        - Output ONLY the translated Telugu text.
        """
        try:
            response_text = self.gemini_service.generate_text(prompt, api_key=api_key)
            return response_text.strip()
        except Exception as e:
            logging.error(f"Multilingual translation to Telugu failed: {e}")
            return f"{english_text} (అనువాదం అందుబాటులో లేదు)"

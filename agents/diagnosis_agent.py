import os
import json
import logging

try:
    from google.adk.agents import Agent as ADKAgent
    HAS_ADK = True
except ImportError:
    HAS_ADK = False

class DiagnosisAgent:
    def __init__(self, gemini_service):
        self.gemini_service = gemini_service
        self.name = "DiagnosisAgent"
        self.instruction = """
        You are the Diagnosis Agent of Rythu Mitra AI.
        Your responsibilities:
        1. Examine the uploaded image of a crop, plant, or leaf.
        2. Identify the crop type (e.g. Paddy, Cotton, Tomato, Groundnut, etc.)
        3. Identify the most likely disease, pest infestation, or nutrient deficiency.
        4. State the diagnosis only as "likely" or "probable" with a confidence percentage (e.g., 75%).
        5. If the image is blurry, doesn't contain a plant/crop, or you cannot make a confident assessment (confidence less than 50%), set "unclear_image": true and explain why. Recommend visiting the nearest Rythu Bharosa Kendra (RBK) or agriculture extension officer.
        6. Return the response as a structured JSON object.
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

    def diagnose_crop(self, image_bytes, api_key=None):
        """Diagnoses disease from image bytes using Gemini multimodal."""
        if not image_bytes:
            return {
                "crop_type": "Unknown",
                "likely_condition": "No Image Provided",
                "confidence": 0,
                "symptoms_noted": "Please upload a valid crop photo.",
                "unclear_image": True,
                "recommend_expert_visit": True
            }

        prompt = """
        Analyze this crop leaf/plant image.
        Provide your diagnosis of the most likely disease/pest/deficiency.
        Format your response EXACTLY as a JSON object with the following keys:
        {
          "crop_type": "string (e.g. Paddy, Cotton, Chilli)",
          "likely_condition": "string (condition name in English with common Telugu transliteration in brackets if known, e.g. Blast Disease (అగ్గి తెగులు))",
          "confidence": integer (0 to 100),
          "symptoms_noted": "string (short description of the symptoms observed in the image)",
          "unclear_image": boolean (true if image is blurry, irrelevant, or too low quality to diagnose),
          "recommend_expert_visit": boolean (true if confidence is under 50% or if it requires a professional field visit)
        }
        Do not add any markup or text other than the JSON object.
        """
        try:
            response_text = self.gemini_service.generate_multimodal(
                prompt=prompt,
                image_bytes=image_bytes,
                api_key=api_key
            )
            # Standard cleaning of potential JSON markdown code block formatting
            cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_response)
            return data
        except Exception as e:
            logging.error(f"Diagnosis agent failed to process image: {e}")
            return {
                "crop_type": "Unknown",
                "likely_condition": "Analysis Error",
                "confidence": 0,
                "symptoms_noted": "Unable to analyze the image due to a technical error.",
                "unclear_image": True,
                "recommend_expert_visit": True
            }

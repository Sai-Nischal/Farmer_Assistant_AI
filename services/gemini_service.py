import os
import io
import logging
from PIL import Image

try:
    from google import genai
    from google.genai import types
    HAS_NEW_SDK = True
except ImportError:
    HAS_NEW_SDK = False

try:
    import google.generativeai as genai_legacy
    HAS_LEGACY_SDK = True
except ImportError:
    HAS_LEGACY_SDK = False


class GeminiService:
    def __init__(self):
        pass

    def _get_api_key(self, api_key=None):
        """Resolves the API key from parameter or environment."""
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Gemini API key is missing. Please configure it in your environment or Settings.")
        return key

    def generate_text(self, prompt, api_key=None, model_name="gemini-2.5-flash"):
        """Generates text output from Gemini."""
        key = self._get_api_key(api_key)
        
        # Try new SDK first
        if HAS_NEW_SDK:
            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                logging.error(f"New SDK text generation failed: {e}. Trying legacy fallback.")
                
        # Try legacy SDK fallback
        if HAS_LEGACY_SDK:
            try:
                genai_legacy.configure(api_key=key)
                # Map model name if needed, legacy might not know gemini-2.5-flash depending on version
                legacy_model_name = "gemini-1.5-flash" if "2.5" in model_name else model_name
                model = genai_legacy.GenerativeModel(legacy_model_name)
                response = model.generate_content(prompt)
                return response.text
            except Exception as e:
                logging.error(f"Legacy SDK text generation failed: {e}")
                raise e
                
        raise ImportError("No Google GenAI SDK is available. Please install google-genai or google-generativeai.")

    def generate_multimodal(self, prompt, image_bytes, api_key=None, model_name="gemini-2.5-flash"):
        """Generates text response from prompt and image input."""
        key = self._get_api_key(api_key)
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logging.error(f"Failed to open uploaded image bytes: {e}")
            raise ValueError("Invalid image file uploaded.")

        # Try new SDK first
        if HAS_NEW_SDK:
            try:
                client = genai.Client(api_key=key)
                # Use PIL image directly in contents
                response = client.models.generate_content(
                    model=model_name,
                    contents=[image, prompt]
                )
                return response.text
            except Exception as e:
                logging.error(f"New SDK multimodal generation failed: {e}. Trying legacy fallback.")
                
        # Try legacy SDK fallback
        if HAS_LEGACY_SDK:
            try:
                genai_legacy.configure(api_key=key)
                legacy_model_name = "gemini-1.5-flash" if "2.5" in model_name else model_name
                model = genai_legacy.GenerativeModel(legacy_model_name)
                response = model.generate_content([image, prompt])
                return response.text
            except Exception as e:
                logging.error(f"Legacy SDK multimodal generation failed: {e}")
                raise e
                
        raise ImportError("No Google GenAI SDK is available. Please install google-genai or google-generativeai.")

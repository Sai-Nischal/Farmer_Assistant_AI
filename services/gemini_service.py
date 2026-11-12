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
    TEXT_FALLBACK_MODELS = (
        "gemini-2.5-flash-lite",
        "gemini-3-flash-preview",
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it",
    )
    AUDIO_FALLBACK_MODELS = (
        "gemini-2.5-flash-lite",
        "gemini-3-flash-preview",
    )

    def __init__(self):
        pass

    def _get_api_key(self, api_key=None):
        """Resolves the API key from parameter or environment."""
        key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Gemini API key is missing. Please configure it in your environment or Settings.")
        return key

    @staticmethod
    def _is_retryable_model_error(error):
        message = str(error).lower()
        return any(marker in message for marker in (
            "429",
            "resource_exhausted",
            "quota",
            "rate limit",
            "too many requests",
            "404",
            "not_found",
            "not found",
            "not supported",
            "unsupported model",
        ))

    def generate_content(self, contents, api_key=None, model_name="gemini-2.5-flash",
                         fallback_models=None):
        """Generates content, trying configured models after quota or model-availability errors."""
        key = self._get_api_key(api_key)
        models = [model_name]
        for fallback_model in fallback_models or self.TEXT_FALLBACK_MODELS:
            if fallback_model not in models:
                models.append(fallback_model)

        if not HAS_NEW_SDK and not HAS_LEGACY_SDK:
            raise ImportError("No Google GenAI SDK is available. Please install google-genai or google-generativeai.")

        last_error = None
        for candidate in models:
            try:
                if HAS_NEW_SDK:
                    client = genai.Client(api_key=key)
                    response = client.models.generate_content(
                        model=candidate,
                        contents=contents
                    )
                else:
                    genai_legacy.configure(api_key=key)
                    model = genai_legacy.GenerativeModel(candidate)
                    response = model.generate_content(contents)
                return response.text
            except Exception as error:
                if HAS_NEW_SDK and HAS_LEGACY_SDK and not self._is_retryable_model_error(error):
                    try:
                        genai_legacy.configure(api_key=key)
                        legacy_model = genai_legacy.GenerativeModel(candidate)
                        response = legacy_model.generate_content(contents)
                        return response.text
                    except Exception as legacy_error:
                        error = legacy_error

                last_error = error
                if not self._is_retryable_model_error(error):
                    raise
                logging.warning(
                    "Gemini model %s unavailable or rate-limited; trying the next fallback: %s",
                    candidate,
                    error,
                )

        raise last_error

    def generate_text(self, prompt, api_key=None, model_name="gemini-2.5-flash"):
        """Generates text output from Gemini."""
        return self.generate_content(
            prompt,
            api_key=api_key,
            model_name=model_name,
        )

    def generate_multimodal(self, prompt, image_bytes, api_key=None, model_name="gemini-2.5-flash"):
        """Generates text response from prompt and image input."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            logging.error(f"Failed to open uploaded image bytes: {e}")
            raise ValueError("Invalid image file uploaded.")

        return self.generate_content(
            [image, prompt],
            api_key=api_key,
            model_name=model_name,
        )

    def transcribe_audio(self, audio_bytes, prompt, api_key=None, model_name="gemini-2.5-flash"):
        """Transcribes audio with Gemini models that support audio input."""
        if HAS_NEW_SDK:
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
        else:
            audio_part = {
                "mime_type": "audio/wav",
                "data": audio_bytes,
            }
        return self.generate_content(
            [audio_part, prompt],
            api_key=api_key,
            model_name=model_name,
            fallback_models=self.AUDIO_FALLBACK_MODELS,
        )

import hashlib
import os
import logging
from gtts import gTTS

class TTSService:
    def __init__(self):
        self.audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")
        os.makedirs(self.audio_dir, exist_ok=True)

    def text_to_speech(self, text, lang='te'):
        """
        Converts text to speech using gTTS and saves as MP3 file.
        Returns the relative path to the MP3 file.
        lang: 'te' for Telugu, 'en' for English
        """
        if not text:
            return None
            
        # Clean text from special characters that might break TTS or make it sound weird
        cleaned_text = text.replace("**", "").replace("*", "").replace("`", "").strip()
        if not cleaned_text:
            return None

        # Create a unique filename based on language and hash of the text
        text_hash = hashlib.md5(cleaned_text.encode('utf-8')).hexdigest()
        filename = f"tts_{lang}_{text_hash}.mp3"
        filepath = os.path.join(self.audio_dir, filename)
        
        # Return existing file if already cached
        if os.path.exists(filepath):
            return f"/static/audio/{filename}"
            
        try:
            # gTTS supports 'te' (Telugu) and 'en' (English)
            tts = gTTS(text=cleaned_text, lang=lang, slow=False)
            tts.save(filepath)
            return f"/static/audio/{filename}"
        except Exception as e:
            logging.error(f"TTS conversion failed for lang {lang}: {e}")
            return None
            
    def cleanup_old_audio(self):
        """Clean up generated audio files to save space."""
        try:
            for file in os.listdir(self.audio_dir):
                if file.startswith("tts_") and file.endswith(".mp3"):
                    os.remove(os.path.join(self.audio_dir, file))
        except Exception as e:
            logging.error(f"Failed to cleanup audio: {e}")

import sys
import logging

# Set up logging early
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    import os
    import uuid
    from flask import Flask, render_template, request, jsonify, session, redirect, url_for
    from werkzeug.utils import secure_filename
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "rythu_mitra_ai_secure_dev_key")

    # Import models, services and agents
    from models.farmer import Farmer
    from services.storage_service import StorageService
    from services.gemini_service import GeminiService
    from services.weather_service import WeatherService
    from services.tts_service import TTSService

    from agents.multilingual_agent import MultilingualAgent
    from agents.diagnosis_agent import DiagnosisAgent
    from agents.weather_agent import WeatherAgent
    from agents.advisory_agent import AdvisoryAgent
    from agents.scheme_agent import SchemeAgent
    from agents.fallback_agent import FallbackAgent
    from agents.conversation_agent import ConversationAgent

    # Initialize Services
    storage_service = StorageService()
    gemini_service = GeminiService()
    weather_service = WeatherService(storage_service)
    tts_service = TTSService()

    # Initialize Agents
    multilingual_agent = MultilingualAgent(gemini_service)
    diagnosis_agent = DiagnosisAgent(gemini_service)
    weather_agent = WeatherAgent(weather_service)
    advisory_agent = AdvisoryAgent(gemini_service)
    scheme_agent = SchemeAgent(storage_service, gemini_service)
    fallback_agent = FallbackAgent()

    conversation_agent = ConversationAgent(
        storage_service=storage_service,
        gemini_service=gemini_service,
        multilingual_agent=multilingual_agent,
        diagnosis_agent=diagnosis_agent,
        weather_agent=weather_agent,
        advisory_agent=advisory_agent,
        scheme_agent=scheme_agent,
        fallback_agent=fallback_agent
    )

    # Configure upload folder
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

except Exception as e:
    import traceback
    print("----- START TRACEBACK -----", file=sys.stderr, flush=True)
    for line in traceback.format_exc().splitlines():
        print(line, file=sys.stderr, flush=True)
    print("----- END TRACEBACK -----", file=sys.stderr, flush=True)
    raise e

# Helper to get active user ID
def get_current_farmer_id():
    if 'farmer_id' not in session:
        session['farmer_id'] = 'farmer_123'  # Default farmer ID
    return session['farmer_id']

@app.context_processor
def inject_farmer():
    """Injects current farmer profile and UI translations globally."""
    farmer_id = get_current_farmer_id()
    farmer = storage_service.get_farmer(farmer_id)
    if not farmer:
        # Create a default small farmer
        farmer = Farmer(
            id=farmer_id,
            name="రామయ్య (Ramayya)",
            village_mandal="Guntur",
            land_size_acres=3.0,
            primary_crop="Paddy",
            category="small_marginal",
            language="te",
            voice_enabled=True
        )
        storage_service.save_farmer(farmer)
        
    # Dictionary of simple Telugu translations for basic PWA shell headers/buttons
    te_translations = {
        "title": "రైతు మిత్ర AI",
        "home": "హోమ్",
        "diagnose": "రోగా నిర్ధారణ",
        "advisory": "సలహాలు",
        "schemes": "పథకాలు",
        "history": "చరిత్ర",
        "settings": "సెట్టింగ్స్",
        "photo_btn": "ఫోటో తీయండి / అప్‌లోడ్ చేయండి",
        "voice_btn": "మాట్లాడండి",
        "lang_toggle": "English",
        "offline_banner": "ఇంటర్నెట్ లేదు - మునుపటి ఫలితాలు చూపిస్తోంది"
    }
    
    en_translations = {
        "title": "Rythu Mitra AI",
        "home": "Home",
        "diagnose": "Diagnose",
        "advisory": "Advisories",
        "schemes": "Schemes",
        "history": "History",
        "settings": "Settings",
        "photo_btn": "Take / Upload Photo",
        "voice_btn": "Speak Now",
        "lang_toggle": "తెలుగు",
        "offline_banner": "No Connection - Showing Cached Data"
    }
    
    translations = te_translations if farmer.language == 'te' else en_translations
    return dict(current_farmer=farmer, lang_pref=farmer.language, ui=translations)

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    farmer_id = get_current_farmer_id()
    farmer = storage_service.get_farmer(farmer_id)
    api_key_override = session.get('gemini_api_key_override')
    
    if request.method == 'POST':
        # Check if file upload is present
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
            
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
            
        if file:
            filename = f"crop_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Read image bytes for Gemini processing
            with open(filepath, 'rb') as f:
                image_bytes = f.read()
                
            # Process diagnosis
            result = conversation_agent.process_farmer_input(
                farmer_id=farmer_id,
                image_bytes=image_bytes,
                api_key=api_key_override
            )
            
            # Update diagnosis history file path in DB
            if result.get("is_success") and result.get("diagnosis"):
                # Load history and modify latest image path
                histories = storage_service.get_history(farmer_id)
                if histories:
                    latest = histories[0]
                    latest.image_path = f"/static/uploads/{filename}"
                    # Re-save list to storage
                    all_records = storage_service.get_history()
                    for r in all_records:
                        if r.id == latest.id:
                            r.image_path = f"/static/uploads/{filename}"
                    storage_service._write_json(storage_service.history_file, [r.to_dict() for r in all_records])
                    
            return jsonify(result)
            
    return render_template('diagnose.html')

@app.route('/advisory')
def advisory():
    farmer_id = get_current_farmer_id()
    farmer = storage_service.get_farmer(farmer_id)
    
    # Get weather forecast
    weather_data = weather_agent.get_forecast(farmer.village_mandal)
    
    # Get latest diagnosis to render alongside
    history = storage_service.get_history(farmer_id)
    latest_diag = history[0] if history else None
    
    return render_template('advisory.html', weather=weather_data, latest_diag=latest_diag)

@app.route('/schemes')
def schemes():
    farmer_id = get_current_farmer_id()
    farmer = storage_service.get_farmer(farmer_id)
    
    # Find matching schemes
    matched = scheme_agent.evaluate_eligibility(farmer)
    
    # Get all schemes for filter lists
    all_schemes = storage_service.get_all_schemes()
    categories = list(set([s.category for s in all_schemes]))
    
    return render_template('schemes.html', schemes=matched, categories=categories)

@app.route('/history')
def history():
    farmer_id = get_current_farmer_id()
    diagnoses = storage_service.get_history(farmer_id)
    return render_template('history.html', history=diagnoses)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    farmer_id = get_current_farmer_id()
    farmer = storage_service.get_farmer(farmer_id)
    
    if request.method == 'POST':
        name = request.form.get('name', farmer.name)
        village = request.form.get('village_mandal', farmer.village_mandal)
        land = request.form.get('land_size_acres', farmer.land_size_acres)
        crop = request.form.get('primary_crop', farmer.primary_crop)
        lang = request.form.get('language', farmer.language)
        voice = request.form.get('voice_enabled') == 'on'
        
        # Save custom credentials if inputted
        api_key = request.form.get('gemini_api_key', '')
        if api_key.strip() != '':
            session['gemini_api_key_override'] = api_key
            os.environ['GEMINI_API_KEY'] = api_key
        else:
            # Allow clearing the override key
            session.pop('gemini_api_key_override', None)
            
        updated_farmer = Farmer(
            id=farmer_id,
            name=name,
            village_mandal=village,
            land_size_acres=land,
            primary_crop=crop,
            language=lang,
            voice_enabled=voice
        )
        storage_service.save_farmer(updated_farmer)
        return redirect(url_for('settings'))
        
    api_key_override = session.get('gemini_api_key_override', '')
    return render_template('settings.html', api_key_override=api_key_override)

@app.route('/toggle-lang')
def toggle_lang():
    farmer_id = get_current_farmer_id()
    farmer = storage_service.get_farmer(farmer_id)
    if farmer:
        farmer.language = 'en' if farmer.language == 'te' else 'te'
        storage_service.save_farmer(farmer)
    return redirect(request.referrer or url_for('index'))

# --- API ENDPOINTS ---

@app.route('/api/chat', methods=['POST'])
def api_chat():
    farmer_id = get_current_farmer_id()
    api_key_override = session.get('gemini_api_key_override')
    
    data = request.json or {}
    text_query = data.get("query")
    
    if not text_query:
        return jsonify({"error": "No query provided"}), 400
        
    result = conversation_agent.process_farmer_input(
        farmer_id=farmer_id,
        text_input=text_query,
        api_key=api_key_override
    )
    return jsonify(result)

@app.route('/api/voice-output', methods=['POST'])
def api_voice_output():
    data = request.json or {}
    text = data.get("text")
    lang = data.get("lang", "te")
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
        
    audio_path = tts_service.text_to_speech(text, lang=lang)
    if audio_path:
        return jsonify({"audio_url": audio_path})
    return jsonify({"error": "Speech synthesis failed"}), 500

@app.route('/api/voice-input', methods=['POST'])
def api_voice_input():
    """Accepts audio file and transcribes it using Gemini's multimodal capabilities."""
    api_key_override = session.get('gemini_api_key_override')
    
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400
        
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No file name"}), 400
        
    try:
        # Save temp file
        temp_filename = f"voice_{uuid.uuid4().hex[:8]}.wav"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        audio_file.save(temp_path)
        
        # Read audio bytes
        with open(temp_path, 'rb') as f:
            audio_bytes = f.read()
            
        # Call Gemini using standard models config to transcribe the speech
        prompt = """
        You are a voice recognition helper for an agricultural app. 
        Transcribe the audio file EXACTLY as it is spoken.
        Do not add any greetings, punctuation formatting, or meta-comments.
        If it is in Telugu, output the Telugu text. If it is in English, output the English text.
        If it is in Telugu but transliterated (written in English script), output Telugu words in English letters.
        """
        
        # Note: Gemini 2.5 Flash can process audio files natively.
        # We wrap this in a multimodal call.
        # Since we saved the file, we can read and pass it.
        # However, to avoid legacy SDK issues, we can request a text input by prompting the Gemini Model with the audio.
        # If the SDK has audio parsing, let's process it. Otherwise, return fallback message.
        key = session.get('gemini_api_key_override') or os.environ.get("GEMINI_API_KEY")
        if not key:
            return jsonify({"error": "Gemini key missing"}), 400
            
        # Load Client and model
        if HAS_NEW_SDK:
            client = genai.Client(api_key=key)
            # The google-genai client supports passing audio bytes directly
            audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[audio_part, prompt]
            )
            transcription = response.text
        elif HAS_LEGACY_SDK:
            genai_legacy.configure(api_key=key)
            # Legacy audio upload / passing
            audio_part = {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
            model = genai_legacy.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([audio_part, prompt])
            transcription = response.text
        else:
            transcription = ""
            
        # Cleanup temp file
        os.remove(temp_path)
        
        return jsonify({"transcription": transcription.strip()})
        
    except Exception as e:
        logging.error(f"Voice transcription failed: {e}")
        return jsonify({"error": f"Transcription error: {str(e)}"}), 500

if __name__ == '__main__':
    # Generate mock data for testing if files are empty
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)

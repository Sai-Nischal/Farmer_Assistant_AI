import os
import uuid
import logging
from models.farmer import Farmer
from models.diagnosis import Diagnosis

class ConversationAgent:
    def __init__(self, storage_service, gemini_service, multilingual_agent, diagnosis_agent, weather_agent, advisory_agent, scheme_agent, fallback_agent):
        self.storage_service = storage_service
        self.gemini_service = gemini_service
        self.multilingual_agent = multilingual_agent
        self.diagnosis_agent = diagnosis_agent
        self.weather_agent = weather_agent
        self.advisory_agent = advisory_agent
        self.scheme_agent = scheme_agent
        self.fallback_agent = fallback_agent

    def process_farmer_input(self, farmer_id, text_input=None, image_bytes=None, api_key=None):
        """Orchestrates multi-agent routing based on the inputs provided by the farmer."""
        
        # 1. Fetch or create farmer profile
        farmer = self.storage_service.get_farmer(farmer_id)
        if not farmer:
            # Create a default small farmer profile for AP
            farmer = Farmer(
                id=farmer_id,
                name="Gangaiah",
                village_mandal="Guntur",
                land_size_acres=3.0,
                primary_crop="Paddy",
                category="small_marginal",
                language="te",
                voice_enabled=True
            )
            self.storage_service.save_farmer(farmer)
            
        lang = farmer.language

        # 2. Case A: Photo Diagnosis Upload
        if image_bytes:
            logging.info(f"Routing to DiagnosisAgent for farmer: {farmer_id}")
            
            # Step A1: Call Diagnosis Agent
            diag_report = self.diagnosis_agent.diagnose_crop(image_bytes, api_key=api_key)
            
            # Step A2: Check if diagnosis failed or is unclear
            if diag_report.get("unclear_image") or diag_report.get("recommend_expert_visit") or diag_report.get("confidence", 0) < 50:
                reason = "Image is unclear, blurry, or not recognized as a known crop disease."
                fallback_res = self.fallback_agent.get_fallback_response(lang=lang, reason=reason)
                
                # Format final return response in user's language
                telugu_reply = fallback_res["message"]
                if lang == "en":
                    telugu_reply = fallback_res["message"]
                
                return {
                    "is_success": False,
                    "diagnosis": {
                        "crop_type": diag_report.get("crop_type", "Unknown"),
                        "likely_condition": diag_report.get("likely_condition", "Unclear Image"),
                        "confidence": diag_report.get("confidence", 0),
                        "symptoms_noted": diag_report.get("symptoms_noted", "No symptoms recognized.")
                    },
                    "reply_text": telugu_reply,
                    "advisory": None,
                    "schemes": [],
                    "weather": None,
                    "requires_fallback": True
                }
            
            # Step A3: Fetch location weather
            weather_forecast = self.weather_agent.get_forecast(farmer.village_mandal)
            
            # Step A4: Call Advisory Agent to get weather-driven advice
            advisory_report = self.advisory_agent.generate_advisory(
                diagnosis_report=diag_report,
                weather_forecast=weather_forecast,
                api_key=api_key
            )
            
            # Step A5: Check Scheme Eligibility for this crop & farmer profile
            eligible_schemes = self.scheme_agent.evaluate_eligibility(farmer)
            # Filter schemes matching this diagnosed crop specifically, if possible
            matching_schemes = []
            for s in eligible_schemes:
                if s["category"].lower() == "all crops" or diag_report["crop_type"].lower() in s["category"].lower() or s["category"].lower() in diag_report["crop_type"].lower():
                    matching_schemes.append(s)
            
            # Use general eligible schemes if no crop-specific ones match
            if not matching_schemes:
                matching_schemes = eligible_schemes[:2]  # Limit to top 2 to keep response clean
            
            # Step A6: Translate response components back to Telugu if requested
            reply_text_en = f"Crop: {diag_report['crop_type']}\n"
            reply_text_en += f"Likely Condition: {diag_report['likely_condition']} (Confidence: {diag_report['confidence']}%)\n\n"
            reply_text_en += f"Symptoms: {diag_report['symptoms_noted']}\n\n"
            reply_text_en += f"Organic Treatment:\n{advisory_report['organic_treatment']}\n\n"
            reply_text_en += f"Chemical Treatment:\n{advisory_report['chemical_treatment']}\n\n"
            reply_text_en += f"Irrigation Advice: {advisory_report['irrigation_advice']}\n"
            reply_text_en += f"Spraying Advice: {advisory_report['spray_advice']}\n"
            if advisory_report.get("safety_flags"):
                reply_text_en += f"\nSafety Warning: {advisory_report['safety_flags']}\n"
                
            if matching_schemes:
                reply_text_en += f"\nGovernment Scheme Note: You may be eligible for '{matching_schemes[0]['name_en']}'. {matching_schemes[0]['benefit_en']}"

            if lang == "te":
                # Translate English segments to simple Telugu
                translated_condition = self.multilingual_agent.translate_to_telugu(diag_report['likely_condition'], api_key=api_key)
                translated_symptoms = self.multilingual_agent.translate_to_telugu(diag_report['symptoms_noted'], api_key=api_key)
                translated_organic = self.multilingual_agent.translate_to_telugu(advisory_report['organic_treatment'], api_key=api_key)
                translated_chemical = self.multilingual_agent.translate_to_telugu(advisory_report['chemical_treatment'], api_key=api_key)
                translated_irrigation = self.multilingual_agent.translate_to_telugu(advisory_report['irrigation_advice'], api_key=api_key)
                translated_spray = self.multilingual_agent.translate_to_telugu(advisory_report['spray_advice'], api_key=api_key)
                
                reply_text = f"పంట రకం: {diag_report['crop_type']}\n"
                reply_text += f"అనుమానిత వ్యాధి/తెగులు: {translated_condition} (నమ్మకం: {diag_report['confidence']}%)\n\n"
                reply_text += f"గమనించిన లక్షణాలు: {translated_symptoms}\n\n"
                reply_text += f"సేంద్రీయ నివారణ (రసాయన రహిత):\n{translated_organic}\n\n"
                reply_text += f"రసాయన నివారణ (జాగ్రత్తగా వాడండి):\n{translated_chemical}\n\n"
                reply_text += f"నీటి తడుల సలహా: {translated_irrigation}\n"
                reply_text += f"మందుల పిచికారీ సలహా: {translated_spray}\n"
                
                if advisory_report.get("safety_flags") and advisory_report["safety_flags"].strip() != "":
                    translated_safety = self.multilingual_agent.translate_to_telugu(advisory_report['safety_flags'], api_key=api_key)
                    reply_text += f"\nభద్రతా హెచ్చరిక: {translated_safety}\n"
                
                if matching_schemes:
                    reply_text += f"\nప్రభుత్వ పథకం సమాచారం: మీరు '{matching_schemes[0]['name_te']}' పథకానికి అర్హులు కావచ్చు. లబ్ధి: {matching_schemes[0]['benefit_te']}"
            else:
                reply_text = reply_text_en

            # Step A7: Record this diagnosis in History
            diagnosis_record = Diagnosis(
                id=str(uuid.uuid4())[:8],
                farmer_id=farmer_id,
                crop_type=diag_report["crop_type"],
                likely_condition=diag_report["likely_condition"],
                confidence=diag_report["confidence"],
                symptoms=diag_report["symptoms_noted"],
                organic_treatment=advisory_report["organic_treatment"],
                chemical_treatment=advisory_report["chemical_treatment"]
            )
            self.storage_service.add_diagnosis(diagnosis_record)

            return {
                "is_success": True,
                "diagnosis": diag_report,
                "advisory": advisory_report,
                "schemes": matching_schemes,
                "weather": weather_forecast,
                "reply_text": reply_text,
                "requires_fallback": False
            }

        # 3. Case B: Text or Voice Advisory Question (No Photo)
        else:
            logging.info(f"Routing text query for farmer: {farmer_id}")
            
            # Step B1: Detect input language & translate query to English
            translation_result = self.multilingual_agent.detect_and_translate_to_english(text_input, api_key=api_key)
            english_query = translation_result["translated_text"]
            detected_lang = translation_result["detected_lang"]

            # Step B2: Determine query intent (schemes, weather, advisory) via simple routing
            intent_prompt = f"""
            Identify which agent should handle this farmer's query: "{english_query}"
            Respond with exactly one of: "SCHEME", "WEATHER", "ADVISORY", or "FALLBACK".
            - Use "SCHEME" if they ask about government help, money, subsidies, bank loans, or specific schemes like PM-KISAN, Rythu Bharosa.
            - Use "WEATHER" if they ask about rain, wind, temperature, or whether it will rain today/tomorrow.
            - Use "ADVISORY" if they ask general agronomy questions, crop care, plant diseases, or irrigation.
            - Use "FALLBACK" if the query is unrelated to farming, gibberish, or highly uncertain.
            """
            
            try:
                intent_res = self.gemini_service.generate_text(intent_prompt, api_key=api_key).strip().upper()
            except Exception:
                intent_res = "ADVISORY" # Safe default

            # Route to respective agent
            if "SCHEME" in intent_res:
                eligible_schemes = self.scheme_agent.evaluate_eligibility(farmer)
                if eligible_schemes:
                    sch = eligible_schemes[0]
                    english_reply = f"You are eligible for government support under the '{sch['name_en']}' scheme. Benefit: {sch['benefit_en']}. How to apply: {sch['how_to_apply_en']}. Official link: {sch['apply_link']}"
                else:
                    english_reply = "We checked our records against our database of 20 agricultural schemes, but did not find a strict match for your profile parameters. Please check details with your local cooperative bank or RBK."
                
            elif "WEATHER" in intent_res:
                weather_forecast = self.weather_agent.get_forecast(farmer.village_mandal)
                today_forecast = weather_forecast["days"][0]
                english_reply = f"Weather forecast for {weather_forecast['location']}: Today, maximum temperature is {today_forecast['temp_max']}°C and minimum is {today_forecast['temp_min']}°C. Rain probability is {today_forecast['precipitation_probability']}%. Wind speeds can reach {today_forecast['wind_speed_max']} km/h."
                
            elif "ADVISORY" in intent_res:
                # Use Gemini text generation for simple agricultural Q&A
                weather_forecast = self.weather_agent.get_forecast(farmer.village_mandal)
                
                qa_prompt = f"""
                You are the Advisory Agent of Rythu Mitra AI.
                Answer the farmer's question: "{english_query}"
                Ground your answer strictly in agricultural facts. Do not invent dosages.
                Suggest organic remedies first, followed by safe chemical recommendations if appropriate.
                If they mention livestock or cattle, tell them to consult a veterinary specialist.
                Keep it under 3-4 short sentences.
                """
                try:
                    english_reply = self.gemini_service.generate_text(qa_prompt, api_key=api_key)
                except Exception as e:
                    english_reply = "We apologize, our advisory model is currently busy. Please consult your local agriculture officer."
            else:
                fallback_res = self.fallback_agent.get_fallback_response(lang=lang, reason="Query not recognized.")
                english_reply = fallback_res["message"]

            # Translate the final response back to Telugu if Telugu preferred
            if lang == "te":
                telugu_reply = self.multilingual_agent.translate_to_telugu(english_reply, api_key=api_key)
            else:
                telugu_reply = english_reply

            return {
                "is_success": True,
                "reply_text": telugu_reply,
                "diagnosis": None,
                "advisory": None,
                "schemes": [],
                "weather": None,
                "requires_fallback": ("FALLBACK" in intent_res)
            }

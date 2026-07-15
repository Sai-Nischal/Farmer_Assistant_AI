# Rythu Mitra AI (రైతు మిత్ర AI)

Rythu Mitra AI ("Farmer's Friend AI") is a mobile-first, offline-capable Agentic AI advisory platform designed for small and marginal farmers in Andhra Pradesh.

## Features
- **Crop Disease Diagnosis:** Snap or upload a leaf photo to diagnose crop health issues using Gemini 2.5 Flash vision.
- **Weather-Driven Advisory:** Real-time irrigation and spraying guidance customized to local village weather conditions.
- **Government Schemes Matcher:** Instantly checks eligibility for 20+ key state and central schemes.
- **Multilingual Support:** Conversational Telugu (with optional voice input/output) and English.
- **Offline Shell PWA:** Installable as a progressive web app that caches history and user settings.

## Tech Stack
- **Frontend:** HTML5, CSS3 (Bootstrap 5, custom styles), Vanilla JS.
- **Backend:** Flask, Python.
- **AI Core:** Google Agent Development Kit (ADK) + Gemini 2.5 Flash.
- **APIs:** Open-Meteo API.

## Setup Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and configure your credentials:
   ```bash
   cp .env.example .env
   ```
3. Run the application:
   ```bash
   python app.py
   ```
# Farmer_Assistant_AI

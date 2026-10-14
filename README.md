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

## Setup & Running Instructions

### 1. Activate the Virtual Environment
The project includes a configured virtual environment `.venv`:
```bash
source .venv/bin/activate
```

### 2. Verify / Configure Environment Variables
Ensure your [.env](file:///home/sunny/Downloads/Project/Farmer_Assistant_AI/.env) file is populated with your Gemini API key:
```bash
cp .env.example .env
```
*(Your `.env` file is already created and configured with the Gemini API key).*

### 3. Start the Web Application
Run the Flask server:
```bash
python app.py
```
Or directly using the project's virtual environment:
```bash
./.venv/bin/python app.py
```

### 4. Open in Your Browser
Navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## Key Pages & Navigation
- **Homepage (`/`)**: Feature showcase, live weather glance widget, 3-step farmer guide.
- **Farmer Dashboard (`/dashboard`)**: Farmer profile snapshot, quick diagnosis launch, and bilingual AI chat helper.
- **Farmer Login (`/login`)**:
  - Direct 10-digit mobile number / Farmer ID sign-in (free, zero SMS cost).
  - 1-Click **Demo Login** as *రామయ్య (Ramayya - Guntur)*.
  - New farmer registration with interactive GMaps location picker.
- **Crop Disease Diagnosis (`/diagnose`)**: Leaf photo upload/camera scan with AI diagnosis and remedies.
- **Weather Advisories (`/advisory`)**: 3-day hyperlocal weather with safe spraying and irrigation indicators.
- **Government Welfare Schemes (`/schemes`)**: Real-time eligibility evaluation for 15+ central & AP state schemes with search & category filters.
- **Profile & Map Settings (`/settings`)**: Interactive Google Maps / Leaflet location picker, GPS detection, land size, and crop preferences.

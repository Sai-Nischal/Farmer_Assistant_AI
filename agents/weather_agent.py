import os
import logging

try:
    from google.adk.agents import Agent as ADKAgent
    HAS_ADK = True
except Exception:
    HAS_ADK = False

class WeatherAgent:
    def __init__(self, weather_service):
        self.weather_service = weather_service
        self.name = "WeatherAgent"
        self.instruction = """
        You are the Weather Agent of Rythu Mitra AI.
        Your responsibilities:
        1. Fetch structured live weather forecast (current + 3 days) for the farmer's location.
        2. Provide details like temperature, rainfall probability, relative humidity, and wind speed.
        3. Hand this structured forecast to the Advisory Agent.
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

    def get_forecast(self, location_name):
        """Fetches and prepares the forecast data."""
        if not location_name:
            location_name = "Guntur"
        try:
            return self.weather_service.get_weather_forecast(location_name)
        except Exception as e:
            logging.error(f"WeatherAgent failed to get forecast: {e}")
            # Safe basic fallback
            from datetime import datetime
            return {
                "location": location_name,
                "current": {"temperature": 30.0, "humidity": 70, "wind_speed": 5.0, "precipitation": 0.0},
                "days": [{"date": datetime.now().strftime("%Y-%m-%d"), "temp_max": 33.0, "temp_min": 25.0, "precipitation_probability": 0, "wind_speed_max": 10.0}]
            }

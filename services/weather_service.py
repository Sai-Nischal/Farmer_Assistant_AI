import requests
from datetime import datetime, timedelta
import os
import logging

class WeatherService:
    def __init__(self, storage_service):
        self.storage_service = storage_service
        # Local mapping of common Andhra Pradesh districts/mandals to coordinates
        self.location_coords = {
            "guntur": (16.3067, 80.4365),
            "vijayawada": (16.5062, 80.6480),
            "visakhapatnam": (17.6868, 83.2185),
            "vizag": (17.6868, 83.2185),
            "anantapur": (14.6819, 77.6006),
            "nellore": (14.4426, 79.9865),
            "kurnool": (15.8281, 78.0373),
            "kadapa": (14.4673, 78.8242),
            "chittoor": (13.2172, 79.1003),
            "eluru": (16.7107, 81.1018),
            "kakinada": (16.9891, 82.2475),
            "ongole": (15.5057, 80.0499),
            "srikakulam": (18.3019, 83.8967),
            "vizianagaram": (18.1124, 83.3986),
            "tirupati": (13.6288, 79.4192),
            "amravati": (16.5085, 80.5120),
            "rajahmundry": (17.0005, 81.8040),
            "machilipatnam": (16.1875, 81.1389)
        }

    def _geocode_location(self, place_name):
        """Resolves location name to latitude and longitude."""
        if not place_name:
            # Default to Guntur (center of AP)
            return 16.3067, 80.4365
        
        normalized = place_name.strip().lower()
        # Direct lookup
        if normalized in self.location_coords:
            return self.location_coords[normalized]
        
        # Substring search in our AP database
        for key, coords in self.location_coords.items():
            if key in normalized or normalized in key:
                return coords
                
        # Try dynamic geocoding via Open-Meteo's geocoding API or fallback
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={place_name}&count=1&language=en&format=json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    result = data["results"][0]
                    return float(result["latitude"]), float(result["longitude"])
        except Exception as e:
            logging.error(f"Geocoding failed: {e}")
            
        # Default fallback to central AP (Guntur)
        return 16.3067, 80.4365

    def get_weather_forecast(self, location_name):
        """Fetches 3-day weather forecast from Open-Meteo, with caching."""
        cache_key = location_name.strip().lower() if location_name else "default"
        cached_data = self.storage_service.get_weather_cache(cache_key)
        
        # Check if cache is still valid (less than 1 hour old)
        if cached_data:
            cached_time_str = cached_data.get("timestamp")
            if cached_time_str:
                try:
                    cached_time = datetime.fromisoformat(cached_time_str)
                    if datetime.now() - cached_time < timedelta(hours=1):
                        return cached_data["forecast"]
                except Exception:
                    pass

        # If cache invalid or missing, fetch new forecast
        lat, lon = self._geocode_location(location_name)
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,relative_humidity_2m_max&timezone=auto"
            response = requests.get(url, timeout=8)
            if response.status_code != 200:
                raise Exception(f"Weather API returned status code {response.status_code}")
            
            raw_data = response.json()
            
            # Extract daily forecast elements for the next 3 days
            daily = raw_data.get("daily", {})
            current = raw_data.get("current", {})
            
            forecast = {
                "location": location_name or "AP Central (Guntur)",
                "latitude": lat,
                "longitude": lon,
                "current": {
                    "temperature": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "precipitation": current.get("precipitation")
                },
                "days": []
            }
            
            # Format today and next 2 days
            for i in range(min(3, len(daily.get("time", [])))):
                day_data = {
                    "date": daily["time"][i],
                    "temp_max": daily["temperature_2m_max"][i],
                    "temp_min": daily["temperature_2m_min"][i],
                    "precipitation_probability": daily["precipitation_probability_max"][i],
                    "wind_speed_max": daily["wind_speed_10m_max"][i]
                }
                forecast["days"].append(day_data)
                
            # Update cache
            self.storage_service.set_weather_cache(cache_key, {
                "timestamp": datetime.now().isoformat(),
                "forecast": forecast
            })
            
            return forecast
            
        except Exception as e:
            logging.error(f"Failed to fetch live weather: {e}")
            # If API fails, check if we have older cached weather and return it, otherwise fallback
            if cached_data:
                return cached_data["forecast"]
            
            # Hardcoded static fallback so the app never crashes
            return {
                "location": f"{location_name} (Forecast Offline)",
                "latitude": lat,
                "longitude": lon,
                "current": {
                    "temperature": 32.0,
                    "humidity": 65,
                    "wind_speed": 10.0,
                    "precipitation": 0.0
                },
                "days": [
                    {"date": datetime.now().strftime("%Y-%m-%d"), "temp_max": 34.0, "temp_min": 26.0, "precipitation_probability": 10, "wind_speed_max": 12.0},
                    {"date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"), "temp_max": 33.0, "temp_min": 25.0, "precipitation_probability": 20, "wind_speed_max": 15.0},
                    {"date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"), "temp_max": 35.0, "temp_min": 27.0, "precipitation_probability": 15, "wind_speed_max": 10.0}
                ]
            }

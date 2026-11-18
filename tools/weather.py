import requests

TIMEOUT = 10

WMO = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Rime fog",
       51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle",
       61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
       71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
       80: "Light rain showers", 81: "Rain showers", 82: "Heavy rain showers", 85: "Snow showers", 86: "Heavy snow showers",
       95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail"}


def _openweather(city, key):
    r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                     params={"q": city, "appid": key, "units": "metric"}, timeout=TIMEOUT)
    r.raise_for_status()
    d = r.json()
    msg = (f"Weather in {d.get('name', city)}: {d['weather'][0]['description'].capitalize()}, "
           f"{d['main']['temp']}°C (feels like {d['main']['feels_like']}°C), humidity {d['main']['humidity']}%.")
    return {"message": msg, "data": d}


def _open_meteo(city):
    """Free fallback, no API key needed."""
    g = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                     params={"name": city, "count": 1}, timeout=TIMEOUT)
    g.raise_for_status()
    results = g.json().get("results")
    if not results:
        raise LookupError("city not found")
    place = results[0]
    w = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": place["latitude"], "longitude": place["longitude"],
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m"},
        timeout=TIMEOUT)
    w.raise_for_status()
    c = w.json()["current"]
    desc = WMO.get(c.get("weather_code"), "Current conditions")
    name = place.get("name", city)
    msg = (f"Weather in {name}: {desc}, {c['temperature_2m']}°C (feels like {c['apparent_temperature']}°C), "
           f"humidity {c['relative_humidity_2m']}%, wind {c['wind_speed_10m']} km/h.")
    return {"message": msg, "data": c}


def get_weather(city, key=""):
    city = (city or "Karachi").strip()
    key = (key or "").strip().strip('"').strip("'")
    if key and not key.startswith("your_"):
        try:
            return _openweather(city, key)
        except Exception:
            pass  # invalid/inactive key or network issue -> fall back below
    try:
        return _open_meteo(city)
    except LookupError:
        return {"message": f"I couldn't find a city named “{city}”. Try a different spelling."}
    except Exception:
        return {"message": "Sorry, I couldn't fetch the weather right now. Please check your internet connection and try again."}
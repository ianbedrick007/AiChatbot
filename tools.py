import requests


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current temperature for a specific geographic location using latitude and longitude",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of the location"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the location"
                    }
                },
                "required": ["latitude", "longitude"],
                "additionalProperties": False,
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exchange_rate",
            "description": "Get the exchange rate and metadata for a specific currency pair",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "local_currency": {
                        "type": "string",
                        "description": "The base currency code (e.g., 'USD')"
                    },
                    "foreign_currency": {
                        "type": "string",
                        "description": "The target currency code (e.g., 'EUR')"
                    }
                },
                "required": ["local_currency", "foreign_currency"],
                "additionalProperties": False,
            }
        }
    }
]


def get_weather(latitude, longitude):
    """Get the current weather for a specific geographic location."""
    try:
        response = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,wind_speed_10m"
        )
        response.raise_for_status()
        data = response.json()
        current = data['current']
        return current
    except Exception as e:
        return {"error": str(e)}


def get_exchange_rate(local_currency, foreign_currency):
    "Get the exchange rate for a specific currency pair"
    try:
        response = requests.get(
            f"https://api.exchangerate-api.com/v4/latest/{local_currency}"
        )
        response.raise_for_status()
        data = response.json()
        exchange_rate = data['rates'][foreign_currency]
        return {
            "local_currency": local_currency,
            "foreign_currency": foreign_currency,
            "rate": exchange_rate,
            "date": data.get("date")
        }
    except Exception as e:
        return {"error": str(e)}

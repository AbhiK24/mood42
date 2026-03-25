"""
Geo utilities for mood42
Handles timezone detection, local time, weather, and occasions/holidays
"""

import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Tuple
import calendar

# Region definitions
REGIONS = ["americas", "europe", "asia", "oceania"]

# Timezone offset to region mapping
TIMEZONE_TO_REGION = {
    # Americas (UTC-10 to UTC-3)
    -10: "americas", -9: "americas", -8: "americas", -7: "americas",
    -6: "americas", -5: "americas", -4: "americas", -3: "americas",
    # Europe/Africa (UTC-1 to UTC+3)
    -1: "europe", 0: "europe", 1: "europe", 2: "europe", 3: "europe",
    # Asia (UTC+4 to UTC+9)
    4: "asia", 5: "asia", 6: "asia", 7: "asia", 8: "asia", 9: "asia",
    # Oceania (UTC+10 to UTC+14)
    10: "oceania", 11: "oceania", 12: "oceania", 13: "oceania", 14: "oceania",
}

# Precise timezone to location mapping (for personalized messages)
# Key is timezone offset (float to handle half-hour zones)
TIMEZONE_TO_LOCATION = {
    # Americas
    -10.0: {"city": "Honolulu", "country": "Hawaii", "vibe": "island time"},
    -9.0: {"city": "Anchorage", "country": "Alaska", "vibe": "northern solitude"},
    -8.0: {"city": "Los Angeles", "country": "USA", "vibe": "west coast dreams"},
    -7.0: {"city": "Denver", "country": "USA", "vibe": "mountain air"},
    -6.0: {"city": "Chicago", "country": "USA", "vibe": "midwest heart"},
    -5.0: {"city": "New York", "country": "USA", "vibe": "city that never sleeps"},
    -4.0: {"city": "Santiago", "country": "Chile", "vibe": "andean heights"},
    -3.0: {"city": "São Paulo", "country": "Brazil", "vibe": "tropical metropolis"},
    # Europe
    -1.0: {"city": "Azores", "country": "Portugal", "vibe": "atlantic winds"},
    0.0: {"city": "London", "country": "UK", "vibe": "grey skies, warm tea"},
    1.0: {"city": "Paris", "country": "France", "vibe": "city of light"},
    2.0: {"city": "Berlin", "country": "Germany", "vibe": "techno heartbeat"},
    3.0: {"city": "Moscow", "country": "Russia", "vibe": "endless winter"},
    3.5: {"city": "Tehran", "country": "Iran", "vibe": "ancient crossroads"},
    # Asia
    4.0: {"city": "Dubai", "country": "UAE", "vibe": "desert futurism"},
    4.5: {"city": "Kabul", "country": "Afghanistan", "vibe": "mountain silence"},
    5.0: {"city": "Karachi", "country": "Pakistan", "vibe": "coastal energy"},
    5.5: {"city": "Mumbai", "country": "India", "vibe": "monsoon dreams"},
    5.75: {"city": "Kathmandu", "country": "Nepal", "vibe": "himalayan peace"},
    6.0: {"city": "Dhaka", "country": "Bangladesh", "vibe": "river delta"},
    6.5: {"city": "Yangon", "country": "Myanmar", "vibe": "golden pagodas"},
    7.0: {"city": "Bangkok", "country": "Thailand", "vibe": "street food nights"},
    8.0: {"city": "Singapore", "country": "Singapore", "vibe": "garden city"},
    9.0: {"city": "Tokyo", "country": "Japan", "vibe": "neon and silence"},
    9.5: {"city": "Adelaide", "country": "Australia", "vibe": "southern calm"},
    # Oceania
    10.0: {"city": "Sydney", "country": "Australia", "vibe": "harbour light"},
    11.0: {"city": "Melbourne", "country": "Australia", "vibe": "coffee and art"},
    12.0: {"city": "Auckland", "country": "New Zealand", "vibe": "edge of the world"},
    13.0: {"city": "Samoa", "country": "Samoa", "vibe": "pacific dawn"},
}


def get_location_from_offset(offset_hours: float) -> Dict:
    """Get specific location info from timezone offset."""
    # Try exact match first (for half-hour zones like India +5.5)
    if offset_hours in TIMEZONE_TO_LOCATION:
        return TIMEZONE_TO_LOCATION[offset_hours]

    # Try rounded match
    rounded = round(offset_hours)
    if float(rounded) in TIMEZONE_TO_LOCATION:
        return TIMEZONE_TO_LOCATION[float(rounded)]

    # Fallback
    return {"city": "somewhere", "country": "unknown", "vibe": "quiet hours"}


def get_region_from_offset(offset_hours: float) -> str:
    """Get region from UTC offset in hours (handles half-hour zones like India +5.5)."""
    offset_int = int(round(offset_hours))  # Round to nearest hour
    offset_int = max(-12, min(14, offset_int))
    return TIMEZONE_TO_REGION.get(offset_int, "europe")


def get_local_time(offset_hours: int) -> Tuple[str, int]:
    """
    Get local time string and hour for a given UTC offset.
    Returns: (time_string like "3:45 PM", hour 0-23)
    """
    utc_now = datetime.now(timezone.utc)
    local_time = utc_now + timedelta(hours=offset_hours)
    hour = local_time.hour
    minute = local_time.minute

    # Format as 12-hour time
    period = "AM" if hour < 12 else "PM"
    display_hour = hour % 12 or 12
    time_string = f"{display_hour}:{minute:02d} {period}"

    return time_string, hour


def get_time_of_day(hour: int) -> str:
    """Get descriptive time of day from hour."""
    if 5 <= hour < 9:
        return "early morning"
    elif 9 <= hour < 12:
        return "morning"
    elif 12 <= hour < 14:
        return "midday"
    elif 14 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 20:
        return "evening"
    elif 20 <= hour < 23:
        return "night"
    else:
        return "late night"


def get_region_times() -> Dict[str, Dict]:
    """Get current local times for all regions."""
    # Representative offsets for each region
    region_offsets = {
        "americas": -5,  # EST
        "europe": 1,     # CET
        "asia": 8,       # CST (China)
        "oceania": 11,   # AEDT
    }

    result = {}
    for region, offset in region_offsets.items():
        time_str, hour = get_local_time(offset)
        result[region] = {
            "time": time_str,
            "hour": hour,
            "period": get_time_of_day(hour),
            "offset": offset,
        }
    return result


# Major holidays by month and day (simplified global list)
GLOBAL_HOLIDAYS = {
    (1, 1): {"name": "New Year's Day", "mood": "celebratory"},
    (2, 14): {"name": "Valentine's Day", "mood": "romantic"},
    (3, 17): {"name": "St. Patrick's Day", "mood": "festive"},
    (10, 31): {"name": "Halloween", "mood": "spooky"},
    (12, 24): {"name": "Christmas Eve", "mood": "cozy"},
    (12, 25): {"name": "Christmas Day", "mood": "warm"},
    (12, 31): {"name": "New Year's Eve", "mood": "celebratory"},
}

# Regional holidays
REGIONAL_HOLIDAYS = {
    "americas": {
        (7, 4): {"name": "Independence Day (US)", "mood": "celebratory"},
        (11, 28): {"name": "Thanksgiving (approx)", "mood": "grateful"},  # Varies
    },
    "asia": {
        (1, 25): {"name": "Lunar New Year (approx)", "mood": "celebratory"},  # Varies
        (11, 11): {"name": "Singles Day", "mood": "fun"},
    },
    "europe": {
        (5, 9): {"name": "Europe Day", "mood": "united"},
    },
    "oceania": {
        (1, 26): {"name": "Australia Day", "mood": "festive"},
        (4, 25): {"name": "ANZAC Day", "mood": "reflective"},
    },
}


def get_occasion(region: str = None) -> Optional[Dict]:
    """Get any current occasion/holiday for a region."""
    now = datetime.now(timezone.utc)
    month_day = (now.month, now.day)

    # Check global holidays first
    if month_day in GLOBAL_HOLIDAYS:
        return GLOBAL_HOLIDAYS[month_day]

    # Check regional holidays
    if region and region in REGIONAL_HOLIDAYS:
        regional = REGIONAL_HOLIDAYS[region]
        if month_day in regional:
            return regional[month_day]

    # Check for weekends (Friday/Saturday night vibes)
    weekday = now.weekday()
    hour = now.hour

    if weekday == 4 and hour >= 17:  # Friday evening
        return {"name": "Friday Night", "mood": "energetic"}
    elif weekday == 5:  # Saturday
        if hour < 6:
            return {"name": "Saturday Night", "mood": "party"}
        elif hour >= 17:
            return {"name": "Saturday Evening", "mood": "relaxed"}
    elif weekday == 6:  # Sunday
        if hour < 12:
            return {"name": "Sunday Morning", "mood": "peaceful"}
        else:
            return {"name": "Sunday", "mood": "chill"}

    return None


# Weather patterns by region and time (mock/default)
DEFAULT_WEATHER = {
    "americas": {
        "winter": ["snow", "cold", "clear"],
        "spring": ["rain", "mild", "sunny"],
        "summer": ["hot", "humid", "sunny"],
        "fall": ["cool", "rainy", "cloudy"],
    },
    "europe": {
        "winter": ["cold", "grey", "snow"],
        "spring": ["mild", "rainy", "sunny"],
        "summer": ["warm", "sunny", "pleasant"],
        "fall": ["rainy", "windy", "cool"],
    },
    "asia": {
        "winter": ["cold", "dry", "clear"],
        "spring": ["mild", "rainy", "humid"],
        "summer": ["hot", "monsoon", "humid"],
        "fall": ["cool", "clear", "pleasant"],
    },
    "oceania": {
        "winter": ["mild", "rainy", "cool"],  # Southern hemisphere - reversed
        "spring": ["warm", "sunny", "pleasant"],
        "summer": ["hot", "humid", "sunny"],
        "fall": ["mild", "dry", "pleasant"],
    },
}


def get_season(region: str) -> str:
    """Get current season for a region."""
    month = datetime.now(timezone.utc).month

    # Southern hemisphere has reversed seasons
    southern = region == "oceania"

    if month in [12, 1, 2]:
        return "summer" if southern else "winter"
    elif month in [3, 4, 5]:
        return "fall" if southern else "spring"
    elif month in [6, 7, 8]:
        return "winter" if southern else "summer"
    else:
        return "spring" if southern else "fall"


def get_weather(region: str) -> str:
    """Get weather description for a region (mock for now)."""
    import random
    season = get_season(region)
    options = DEFAULT_WEATHER.get(region, {}).get(season, ["clear"])
    return random.choice(options)


async def get_weather_api(lat: float, lon: float) -> Optional[Dict]:
    """
    Get real weather from Open-Meteo API (free, no key needed).
    Returns: {"temp": 20, "condition": "sunny", "description": "Clear sky"}
    """
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                current = data.get("current_weather", {})

                # Map WMO weather codes to descriptions
                code = current.get("weathercode", 0)
                condition = _weather_code_to_description(code)

                return {
                    "temp": current.get("temperature"),
                    "condition": condition,
                    "is_day": current.get("is_day", 1) == 1,
                }
    except Exception as e:
        print(f"[Geo] Weather API error: {e}")

    return None


def _weather_code_to_description(code: int) -> str:
    """Convert WMO weather code to simple description."""
    if code == 0:
        return "clear"
    elif code in [1, 2, 3]:
        return "partly cloudy"
    elif code in [45, 48]:
        return "foggy"
    elif code in [51, 53, 55, 56, 57]:
        return "drizzle"
    elif code in [61, 63, 65, 66, 67]:
        return "rainy"
    elif code in [71, 73, 75, 77]:
        return "snowy"
    elif code in [80, 81, 82]:
        return "showers"
    elif code in [95, 96, 99]:
        return "stormy"
    else:
        return "cloudy"


def get_viewer_context(
    tz_offset: int,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    country_code: Optional[str] = None,
) -> Dict:
    """
    Build full viewer context from available data.
    Returns: {
        "region": "americas",
        "local_time": "3:45 PM",
        "hour": 15,
        "period": "afternoon",
        "weather": "sunny",
        "occasion": {"name": "...", "mood": "..."} or None,
    }
    """
    region = get_region_from_offset(tz_offset)
    time_str, hour = get_local_time(tz_offset)
    period = get_time_of_day(hour)
    occasion = get_occasion(region)
    weather = get_weather(region)  # Default to mock weather

    return {
        "region": region,
        "local_time": time_str,
        "hour": hour,
        "period": period,
        "weather": weather,
        "occasion": occasion,
        "tz_offset": tz_offset,
    }


def format_viewer_context_for_llm(context: Dict) -> str:
    """Format viewer context for inclusion in LLM prompts."""
    lines = [
        f"Region: {context['region'].upper()}",
        f"Local time: {context['local_time']} ({context['period']})",
        f"Weather: {context['weather']}",
    ]

    if context.get("occasion"):
        occ = context["occasion"]
        lines.append(f"Special occasion: {occ['name']} ({occ['mood']} mood)")

    return "\n".join(lines)

from enum import Enum
from typing import List, Optional


class OutfitPart(str, Enum):
    """Enumeration of possible outfit parts"""
    HEAD = "head"
    TOP = "top"
    BOTTOM = "bottom"
    FOOTWEAR = "footwear"


class Gender(str, Enum):
    """Enumeration of gender values"""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"
    OTHER = "other"


class WeatherCondition(str, Enum):
    """Enumeration of possible weather conditions"""
    THUNDERSTORM = "thunderstorm"
    DRIZZLE = "drizzle"
    RAIN = "rain"
    SNOW = "snow"
    MIST = "mist"
    CLEAR = "clear"
    CLOUDS = "clouds"
    EXTREME = "extreme"

from enum import Enum


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


class WeatherDescription(str, Enum):
    """Standardized weather descriptions"""
    CLEAR_SKY = "clear sky"
    FEW_CLOUDS = "few clouds"
    SCATTERED_CLOUDS = "scattered clouds"
    BROKEN_CLOUDS = "broken clouds"
    SHOWER_RAIN = "shower rain"
    RAIN = "rain"
    THUNDERSTORM = "thunderstorm"
    SNOW = "snow"
    MIST = "mist"

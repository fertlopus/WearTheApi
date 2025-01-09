from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ...schemas.assets import AssetItem
from ...schemas.weather import WeatherConditions
from ...core.exceptions import ValidationException


logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Log to the console
    ]
)


class BaseFilter(ABC):
    """Base class for all filters"""
    @abstractmethod
    def filter_assets(self, assets: List[AssetItem], **kwargs) -> List[AssetItem]:
        """Filter assets based on specific criteria"""
        pass


class WeatherFilter(BaseFilter):
    """Filters assets based on weather conditions provided"""
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode

    def filter_assets(self, assets: List[AssetItem], **kwargs) -> List[AssetItem]:
        weather_conditions = kwargs.get('weather_conditions')

        if weather_conditions is None:
            logger.info("Weather conditions is not met or absent")
            raise ValueError("weather_conditions is required for WeatherFilter")

        filtered_assets = []

        for asset in assets:
            logger.info("Weather filter appliance.")
            if self._is_weather_appropriate(asset, weather_conditions):
                filtered_assets.append(asset)

        logger.debug(f"Weather filter: {len(filtered_assets)}/{len(assets)} assets have passed.")
        return filtered_assets

    def _is_weather_appropriate(self, asset: AssetItem, weather: WeatherConditions) -> bool:
        """Checks if asset is appropriate for given weather conditions"""
        if not (asset.temp_range.temperature_min <= weather.temperature <= asset.temp_range.temperature_max):
            logger.info("Temperature range checking.")
            return False

        if weather.description not in asset.condition:
            logger.info("Weather Description checking.")
            return False

        if weather.wind_speed > 0 and asset.wind == "no":
            logger.info("Wind speed checking.")
            return False

        if weather.snow > 0 and asset.snow == "no":
            logger.info("Snow appliance checking.")
            return False

        return True


class StyleFilter(BaseFilter):
    """Filters assets based on style preferences"""
    def filter_assets(self, assets: List[AssetItem], **kwargs) -> List[AssetItem]:
        style_preferences: List[str] = kwargs.get("style_preferences")
        min_style_match: float = kwargs.get("min_style_match", 0.6)

        if style_preferences is None:
            raise ValueError("style_preferences: List[str] argument is required for StyleFilter")

        filtered_assets = []
        for asset in assets:
            style_match_score = self._calculate_style_match(asset, style_preferences)
            if style_match_score >= min_style_match:
                filtered_assets.append(asset)

        logger.debug(f"Style filter: {len(filtered_assets)}/{len(assets)} assets have passed.")
        return filtered_assets

    def _calculate_style_match(self, asset: AssetItem, style_preferences: List[str]) -> float:
        """Calculates style match score between asset and preferences"""
        matching_styles = set(asset.style) & set(style_preferences)
        if style_preferences == 0:
            return 0.0
        else:
            return len(matching_styles) / len(style_preferences)


class GenderFilter(BaseFilter):
    def filter_assets(self, assets: List[AssetItem], **kwargs) -> List[AssetItem]:
        gender: str = kwargs.get("gender", "unknown")
        include_unisex: bool = kwargs.get("include_unisex", True)
        if gender is None:
            raise ValueError("gender: str argument is required for GenderFilter")

        filtered_assets = [asset for asset in assets if asset.gender == gender or (include_unisex and asset.gender == "unisex")]
        return filtered_assets


class SeasonFilter(BaseFilter):
    def filter_assets(self, assets: List[AssetItem], **kwargs) -> List[AssetItem]:
        date: Optional[datetime] = kwargs.get("date", None)
        if date is None:
            date = datetime.now()

        current_season = self._get_season(date)
        filtered_assets = [asset for asset in assets if current_season in asset.season]
        logger.debug(f"Season filter: {len(filtered_assets)}/{len(assets)} assets have passed.")
        return filtered_assets

    def _get_season(self, date: datetime) -> str:
        month = date.month
        if month in (12, 1, 2):
            return "winter"
        elif month in (3, 4, 5):
            return "spring"
        elif month in (6, 7, 8):
            return "summer"
        else:
            return "autumn"


class OutfitCompatibilityFilter(BaseFilter):
    def filter_assets(self, assets: List[AssetItem], **kwargs) -> List[AssetItem]:
        current_outfit: Dict[str, AssetItem] = kwargs.get("current_outfit")
        if current_outfit is None:
            raise ValueError("current_outfit: Dict[str, AssetItem] argument must be provided")
        filtered_assets = []
        for asset in assets:
            if self._is_compatible(asset, current_outfit):
                filtered_assets.append(asset)
        logger.debug(f"Compatibility Filter: {len(filtered_assets)}/{len(assets)} assets have passed.")
        return filtered_assets

    def _is_compatible(self, asset:AssetItem, current_outfit: Dict[str, AssetItem]) -> bool:
        if not current_outfit:
            return True
        # Style compatibility logic
        outfit_styles = set()
        for piece in current_outfit.values():
            outfit_styles.update(piece.style)
        has_matching_style = bool(set(asset.style) & outfit_styles)
        return has_matching_style


class PreferenceFilter(BaseFilter):
    """Filter assets based on user preferences"""
    def filter_assets(self, assets: List[AssetItem], **kwargs) -> List[AssetItem]:
        preferences = kwargs.get("filters", {})
        colors = preferences.get("colors", [])
        styles = preferences.get("styles", [])
        gender = preferences.get("gender", "unisex")
        fit = preferences.get("fit", "normal")

        filtered_assets = []

        for asset_item in assets:
            if colors and asset_item.color not in colors:
                continue
            if styles and not set(styles).intersection(asset_item.style):
                continue
            if gender != "unisex" and asset_item.gender != gender:
                continue
            if fit and asset_item.fit != fit:
                continue
            filtered_assets.append(asset_item)

        logger.debug(f"Preference filter: {len(filtered_assets)}/{len(assets)} assets passed.")
        print(f"Preference filter: {len(filtered_assets)}/{len(assets)} assets passed.")
        return filtered_assets


class FilterPipeline:
    """
    Example of usage:

    pipeline = FilterPipeline([
        WeatherFilter(strict_mode=True, weather_conditions=<weather_conditions>"),
        StyleFilter(style_preferences: List[str], min_style_match=0.6),
        GenderFilter(gender="male"),
        SeasonFilter(),
        OutfitCompatibilityFilter(current_outfit: Dict[str, AssetItem])
    ])

    filtered_assets = pipeline.apply_filters(
        assets=all_assets,
        weather_conditions=current_weather,
        style_preferences=['casual', 'sporty'],
        gender='male',
        current_outfit=existing_outfit
        )
    """
    def __init__(self, filters: List[BaseFilter]):
        self.filters = filters

    def apply_filters(self, assets: List[AssetItem], **filter_params) -> List[AssetItem]:
        filtered_assets = assets
        for filter_instance in self.filters:
            try:
                filtered_assets = filter_instance.filter_assets(filtered_assets, **filter_params)
                if not filtered_assets:
                    logger.warning("No assets passed all filterd")
                    break
            except Exception as e:
                logger.error(f"Filter: {filter_instance.__class__.__name__} failed: {str(e)}")
                raise ValidationException(f"Filtering failed: {str(e)}")
        return filtered_assets

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ....schemas.assets import AssetItem
from ....schemas.weather import WeatherData, WeatherConditions
from ....services.recommendation_kernel.retrieval.base import BaseRetriever
from ....core.exceptions import AssetRetrievalException


logger = logging.getLogger(__name__)


class JsonAssetRetriever(BaseRetriever):
    """JSON-based asset retriever"""
    def __init__(self, asset_path: Path):
        self.asset_path = asset_path
        self._assets: List[AssetItem] = []
        self._asset_index: Dict[str, AssetItem] = {}

    async def initialize(self) -> None:
        """Reload assets from JSON"""
        try:
            with open(self.asset_path) as f:
                raw_assets = json.load(f)
            self._assets = [AssetItem(**asset) for asset in raw_assets]
            self._asset_index = {asset.asset_name: asset for asset in self._assets}
            logger.info(f"Loaded {len(self._assets)} assets successfully")
        except Exception as e:
            logger.error(f"Failed to refresh assets: {str(e)}")
            raise AssetRetrievalException(f"Failed to refresh asset database: {str(e)}")

    async def retrieve_assets(self, weather_conditions: WeatherConditions,
                              filters: Optional[Dict[str, Any]]=None) -> List[AssetItem]:
        """Retrieve assets based on weather conditions and filters"""
        try:
            filtered_assets = []
            for asset in self._assets:
                if self._matches_weather_conditions(asset, weather_conditions):
                    if filters and not self._matches_filters(asset, filters):
                        continue
                    filtered_assets.append(asset)
            logger.debug(f"Retrieved {len(filtered_assets)} assets matching conditions")
            return filtered_assets
        except Exception as e:
            logger.error(f"Error retrieving assets: {str(e)}")
            raise AssetRetrievalException(f"Failed to retrieve assets: {str(e)}")

    def _matches_weather_conditions(self, asset: AssetItem, weather: WeatherConditions) -> bool:
        """Check if asset matches weather conditions"""
        # Temperature check
        if not (asset.temp_range.temperature_min <= weather.temperature <= asset.temp_range.temperature_max):
            return False
        # Weather condition check
        if weather.description not in asset.condition:
            return False
        # Wind check
        if weather.wind_speed > 0 and asset.wind == "no":
            return False
        # Rain check
        if weather.rain > 0 and asset.rain == "no":
            return False
        # Snow check
        if weather.snow > 0 and asset.snow == "no":
            return False
        return True

    async def get_asset_by_name(self, asset_name: str) -> Optional[AssetItem]:
        """Get specific asset by name"""
        try:
            return self._asset_index.get(asset_name)
        except KeyError as e:
            logger.error(f"Asset {asset_name} not found in the asset catalog: {str(e)}")

    def _matches_filters(self, asset: AssetItem, filters: Dict[str, Any]) -> bool:
        """Check if asset matches conditional filters defined"""
        for key, value in filters.items():
            if key == "gender" and asset.gender != value:
                return False
            elif key == "style" and not any(s in asset.style for s in value):
                return False
            elif key == "outfit_part" and asset.outfit_part != value:
                return False
        return True

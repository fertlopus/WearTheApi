from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ....schemas.assets import AssetItem
from ....schemas.weather import WeatherConditions


class BaseRetriever(ABC):
    """Base Class for asset retrieval system"""

    @abstractmethod
    async def retrieve_assets(self, weather_conditions: WeatherConditions,
                              filters: Optional[Dict[str, Any]]=None) -> List[AssetItem]:
        """Retrieve assets based on weather conditions and filters"""
        pass

    @abstractmethod
    async def refresh_assets(self) -> None:
        """Refresh the asset database/index"""
        pass

    @abstractmethod
    async def get_asset_by_name(self, asset_name: str) -> Optional[AssetItem]:
        """Retrieve specific asset by name"""
        pass

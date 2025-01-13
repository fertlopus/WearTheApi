import json
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import  asyncio
from concurrent.futures import ThreadPoolExecutor

from ....schemas.assets import AssetItem
from ....schemas.weather import WeatherData, WeatherConditions
from ....services.recommendation_kernel.retrieval.base import BaseRetriever
from ..parallel_filter import ParallelFilterSystem
from ....core.exceptions import AssetRetrievalException
from ....services.recommendation_kernel.filters import PreferenceFilter


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler()])


class JsonAssetRetriever(BaseRetriever):
    """JSON-based asset retriever"""
    def __init__(self, asset_path: Path, max_workers: Optional[int] = None):
        self.asset_path = Path(asset_path)
        self._assets: List[AssetItem] = []
        self._asset_index: Dict[str, AssetItem] = {}
        self.filter_system = ParallelFilterSystem(max_workers=max_workers)
        self._initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize assets with lazy loading and locking."""
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:  # Double-check pattern
                return

            try:
                logger.info(f"Initializing assets from: {self.asset_path}")

                if not self.asset_path.exists():
                    raise FileNotFoundError(f"Asset file not found: {self.asset_path}")

                # Load assets asynchronously
                loop = asyncio.get_event_loop()
                with ThreadPoolExecutor() as executor:
                    raw_assets = await loop.run_in_executor(
                        executor,
                        self._load_assets_from_file
                    )

                # Process assets
                self._assets = [AssetItem(**asset) for asset in raw_assets]
                self._asset_index = {asset.asset_name: asset for asset in self._assets}

                self._initialized = True
                logger.info(f"Successfully loaded {len(self._assets)} assets")

            except Exception as e:
                logger.error(f"Failed to initialize assets: {str(e)}")
                raise AssetRetrievalException(f"Failed to initialize asset database: {str(e)}")

    def _load_assets_from_file(self) -> List[Dict[str, Any]]:
        """Load assets from file in a separate thread."""
        with open(self.asset_path) as f:
            return json.load(f)

    async def retrieve_assets(self, weather_conditions: Union[WeatherConditions, WeatherData],
                              filters: Optional[Dict[str, Any]]=None) -> List[AssetItem]:
        """Retrieve assets based on weather conditions and filters"""
        try:
            await self.initialize()

            filtered_assets = []
            logger.info(f"Before filtering on weather conditions, number of assets: {len(self._assets)}")

            # Apply parallel filtering
            filtered_assets = await self.filter_system.filter_assets_parallel(
                assets=self._assets,
                weather_conditions=weather_conditions,
                filters=filters
            )

            logger.debug(f"Retrieved {len(filtered_assets)} assets weather conditions")
            logger.info(f"After filtering on weather conditions: {len(filtered_assets)}")

            logger.debug(f"Retrieved {len(filtered_assets)} assets matching conditions")
            return filtered_assets

        except Exception as e:
            logger.error(f"Error retrieving assets: {str(e)}")
            raise AssetRetrievalException(f"Failed to retrieve assets: {str(e)}")

    async def retrieve_assets_without_filters(self, weather_conditions: WeatherConditions) -> List[AssetItem]:
        try:
            filtered_assets = []
            for asset in self._assets:
                if self._matches_weather_conditions(asset, weather_conditions):
                    filtered_assets.append(asset)

            logger.info(f"Retrieved {len(filtered_assets)} assets matching weather conditions")
            return filtered_assets

        except Exception as e:
            logger.error(f"Error retrieving assets: {str(e)}")
            raise AssetRetrievalException(f"Failed to retrieve assets: {str(e)}")

    async def get_asset_by_name(self, asset_name: str) -> Optional[AssetItem]:
        """Get specific asset by name."""
        await self.initialize()
        return self._asset_index.get(asset_name)

    async def refresh_assets(self) -> None:
        """Refresh assets with initialization reset."""
        self._initialized = False
        await self.initialize()


    def _matches_weather_conditions(self, asset: AssetItem, weather: WeatherConditions) -> bool:
        """Check if asset matches weather conditions"""
        # TODO: Add additional fit-checks for better recommendations and retrieval process and check the logic overall
        # FYI: I have implemented more agnostic and flexible filters in filters.py after some iterations move towards
        # using them
        try:
            # Temperature check
            if not int(weather.temperature) in range(int(asset.temp_range.temperature_min), int(asset.temp_range.temperature_max)):
                logger.info(f"Asset {asset.asset_name} failed temperature check. Temp: {weather.temperature}, "
                             f"Range: {asset.temp_range}")
                return False
            return True

        except Exception as e:
            logger.error(f"Error in matching weather conditions: {str(e)}")
            return False


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

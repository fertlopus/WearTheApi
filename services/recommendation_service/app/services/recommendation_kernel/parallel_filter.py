from typing import List, Dict, Any, Optional, Set
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
from functools import partial
from ...schemas.assets import AssetItem
from ...schemas.weather import WeatherConditions, WeatherData
from ...core.exceptions import ValidationException


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    handlers=[logging.StreamHandler()])


class ParallelFilterSystem:
    """Optimized parallel filtering system for assets."""
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(32, (asyncio.get_event_loop().get_default_executor()._max_workers))
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)

    async def filter_assets_parallel(self, assets: List[AssetItem], weather_conditions: WeatherConditions,
                                     filters: Optional[Dict[str, Any]] = None) -> List[AssetItem]:
        """Filter assets in parallel using multiple processors."""
        try:
            if not assets:
                return []

            # Split assets into chunks for parallel processing
            chunk_size = max(len(assets) // self.max_workers, 1)
            chunks = [assets[i:i + chunk_size] for i in range(0, len(assets), chunk_size)]

            # Create partial function for filtering
            filter_func = partial(
                self._process_chunk,
                weather_conditions=weather_conditions,
                filters=filters
            )

            # Process chunks in parallel
            loop = asyncio.get_event_loop()
            tasks = []
            for chunk in chunks:
                task = loop.run_in_executor(self.executor, filter_func, chunk)
                tasks.append(task)

            # Gather results
            results = await asyncio.gather(*tasks)

            # Combine results
            filtered_assets = []
            for chunk_result in results:
                filtered_assets.extend(chunk_result)

            return filtered_assets

        except Exception as e:
            logger.error(f"Error in parallel asset filtering: {str(e)}")
            raise ValidationException(f"Asset filtering failed: {str(e)}")

    def _process_chunk(self, chunk: List[AssetItem], weather_conditions: WeatherConditions,
                       filters: Optional[Dict[str, Any]]) -> List[AssetItem]:
        """Process a chunk of assets with all filters."""
        filtered_chunk = []

        for asset in chunk:
            if self._matches_all_conditions(asset, weather_conditions, filters):
                filtered_chunk.append(asset)

        return filtered_chunk

    def _matches_all_conditions(self, asset: AssetItem, weather: WeatherConditions,
                                filters: Optional[Dict[str, Any]]) -> bool:
        """Check if asset matches all conditions."""
        # Early termination for weather conditions
        if not self._matches_weather_conditions(asset, weather):
            return False

        # Check user preferences if provided
        if filters and not self._matches_preferences(asset, filters):
            return False

        return True

    def _matches_weather_conditions(self, asset: AssetItem, weather: WeatherConditions) -> bool:
        """Optimized weather condition matching."""
        try:
            # Temperature check
            temp = float(weather.temperature)
            min_temp = float(asset.temp_range.temperature_min)
            max_temp = float(asset.temp_range.temperature_max)

            logger.debug(f"Checking temperature range: {min_temp} <= {temp} <= {max_temp}")

            if not (min_temp <= temp <= max_temp):
                return False
            return True

        except Exception as e:
            logger.error(f"Error matching weather conditions: {str(e)}")
            return False

    def _matches_preferences(self, asset: AssetItem, filters: Dict[str, Any]) -> bool:
        """Optimized preference matching with early termination."""
        try:
            # Gender check
            if "gender" in filters and filters["gender"] != "unisex":
                if asset.gender != filters["gender"] and asset.gender != "unisex":
                    return False

            # Style check
            if "styles" in filters and filters["styles"]:
                if not any(style in asset.style for style in filters["styles"]):
                    return False

            # Color check
            if "colors" in filters and filters["colors"]:
                if asset.color not in filters["colors"]:
                    return False

            # Fit check
            if "fit" in filters and filters["fit"]:
                asset_fits = asset.normalized_fit
                if filters["fit"] not in asset_fits:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error matching preferences: {str(e)}")
            return False
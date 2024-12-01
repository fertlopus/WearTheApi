from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ....schemas.assets import AssetItem
from ....services.recommendation_kernel.retrieval.base import BaseRetriever
from json_retriever import JsonAssetRetriever


class VectorAssetRetriever(BaseRetriever):
    """Vector-based asset retrieval implementation for semantic search."""

    def __init__(self, json_retriever: JsonAssetRetriever, embedding_model: Any):
        self.json_retriever = json_retriever
        self.embedding_model = embedding_model
        self._asset_embeddings: Dict[str, np.ndarray] = {}

    async def initialize(self) -> None:
        """Initialize retriever with embeddings."""
        await self.json_retriever.initialize()
        await self._compute_embeddings()

    async def _compute_embeddings(self) -> None:
        """Compute embeddings for all assets."""
        for asset in self.json_retriever._assets:
            # Create a rich text representation of the asset
            text_repr = (
                f"{asset.style} {asset.color} {asset.outfit_part} "
                f"for {asset.gender} in {', '.join(asset.season)} "
                f"weather conditions: {', '.join(asset.condition)}"
            )
            self._asset_embeddings[asset.asset_name] = (
                self.embedding_model.encode(text_repr)
            )

    async def retrieve_assets(self, weather_conditions: Dict[str, Any],
            filters: Optional[Dict[str, Any]] = None, query: Optional[str] = None,
            top_k: int = 50) -> List[AssetItem]:
        """Retrieve assets using both condition matching and semantic search."""
        # First, get condition-matched assets
        base_assets = await self.json_retriever.retrieve_assets(
            weather_conditions,
            filters
        )

        if not query:
            return base_assets

        # If we have a query, perform semantic search on the filtered assets
        query_embedding = self.embedding_model.encode(query)

        similarities = []
        for asset in base_assets:
            asset_embedding = self._asset_embeddings[asset.asset_name]
            similarity = cosine_similarity(
                query_embedding.reshape(1, -1),
                asset_embedding.reshape(1, -1)
            )[0][0]
            similarities.append((asset, similarity))

        # Sort by similarity and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [asset for asset, _ in similarities[:top_k]]

    async def refresh_assets(self) -> None:
        """Refresh assets and recompute embeddings."""
        await self.json_retriever.refresh_assets()
        await self._compute_embeddings()

    async def get_asset_by_name(self, asset_name: str) -> Optional[AssetItem]:
        """Get specific asset by name."""
        return await self.json_retriever.get_asset_by_name(asset_name)

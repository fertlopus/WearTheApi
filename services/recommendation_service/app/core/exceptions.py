from fastapi import HTTPException, status

class RecommendationServiceException(HTTPException):
    """Base exception for recommendation service"""
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        super().__init__(status_code=status_code, detail=detail)

class AssetRetrievalException(RecommendationServiceException):
    """Exception raised when asset retrieval fails"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Asset retrieval error: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class WeatherServiceException(RecommendationServiceException):
    """Exception raised when weather service fails"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Weather service error: {detail}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class LLMException(RecommendationServiceException):
    """Exception raised when LLM service fails"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"LLM service error: {detail}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )

class CacheException(RecommendationServiceException):
    """Exception raised when cache operations fail"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Cache error: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class ValidationException(RecommendationServiceException):
    """Exception raised when validation fails"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Validation error: {detail}",
            status_code=status.HTTP_400_BAD_REQUEST
        )

class ConfigurationException(RecommendationServiceException):
    """Exception raised when configuration is invalid"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Configuration error: {detail}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

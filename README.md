# The WearThe project description (backend microservices)

---

The backend is aimed for the WearThe iOS application backend that aims to gather the weather data for the context and create
a comprehensive recommendations of outfits for the user/client. The backend uses microservice architecture (2 separate microservices)
to use and apply the logic of recommendations. 

The project consists and supports 2 microservices:
1. `Weather Microservices` with optimized workflow to gather the Weather data by user location.
2. `Recommendation Service` that uses the weather data and LLM to act as a skilled and experienced stylist to recommend to the user what to wear under the specific weather conditions and user preferences in outfits.

---

## Weather Service:

### Overview:

The Weather Service is a microservice component of the WearThe application, designed to provide accurate and cached weather data. It integrates with OpenWeather API and implements caching strategies using Redis to ensure optimal performance and reliability.

### Features:

* Real-time weather data retrieval
* Location-based weather information (by city, country or geo-location coordinates)
* Intelligent caching system with automatic refresh
* Health monitoring endpoints
* Production-ready error handling and logging 
* Background task processing for cache management

### Tech Stack:

* Language: Python >= 3.10
* Framework: FastAPI
* Cache: Redis Cache/ Azure Redis Cache
* External API: OpenWeather API
* Container: Docker 
* Local run: Docker-Compose

### Project Structure:

```shell
./services/weather_service/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── dependencies.py      # FastAPI dependencies
│   ├── logging_config.py    # Logging setup
│   ├── api/
│   │   └── v1/             # API version 1 endpoints
│   ├── core/               # Core functionality
│   ├── schemas/            # Pydantic models
│   └── services/           # Business logic services
├── tests/                  # Test suite
├── Dockerfile
└── pyproject.toml         # Project dependencies
```

### Api Endpoints:

* Health Check (http/https):

```shell
GET /api/v1/health
```

* Weather Data:

```shell
GET /api/v1/weather/city/{city}
GET /api/v1/weather/city/{city}/country/{country_code}
POST /api/v1/weather/proximity?lat={latitude}&lon={longitude}
```

### Configuration

* Environment variables:

```shell
# Core Settings
ENVIRONMENT=dev                 # 'dev' or 'production'
API_V1_STR=/api/v1
WEATHER_API_PROJECT_NAME=WearThe Weather Service

# OpenWeather API
OPENWEATHER_API_KEY=your-api-key
OPENWEATHER_API_URL=https://api.openweathermap.org/data/2.5
OPENWEATHER_API_RETRIES=3
OPENWEATHER_BACKOFF_FACTOR=0.5

# Azure Redis Cache
REDIS_CONNECTION_STRING=your-redis-connection-string

# Cache Settings
WEATHER_CACHE_EXPIRATION=3600  # Cache TTL in seconds
```

### Deployment:

#### Prerequisites:

- Local Docker installed
- Azure Subscription
- Azure CLI installed
- Docker registry access

The manual deployment process for each of the service is fully described [here](./docs/manual_deployment.md).

### Cache System:

The service implements a smart caching system:
* The cache duration: 4 hours (configurable)
* Background refresh: Every 5 minutes for frequently accessed locations 
* Automatic invalidation of stale data
* Redis SSL encryption for security

### Error handling

The service includes comprehensive error handling:

* OpenWeather API communication errors
* Cache connectivity issues
* Data validation errors
* Rate limiting handling 
* Retry mechanisms for external API calls

### Contributing
1. Create a feature branch
2. Commit your changes
3. Push to the branch
4. Open a PR.

---

## Recommendation Service:

---

### Overview

The Recommendation Service is a core microservice of the WearThe application, designed to provide intelligent outfit recommendations based on weather conditions and user preferences. It uses advanced LLM models for recommendation generation and integrates with the Weather Service for real-time weather data.

### Features:

* Weather-appropriate outfit recommendations
* Personalized style preferences
* LLM-powered outfit matching + additional custom filters
* Intelligent caching system
* Asset retrieval and management
* Multi-factor recommendation algorithm
* Integration with Weather Service

### Tech Stack:

* Frameworks: FastAPI, PyDantic, Openai, langchain, llama-index
* Language: Python >= 3.10
* Cache: Azure Redis Cache
* LLM Integration: OpenAI GPT models 
* Container: Docker 
* Asset Storage: JSON/Vector Store
* Weather Data: Weather Service API

### Project Structure:

```shell
services/recommendation_service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── logging_config.py
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints.py
│   │       └── routes.py
│   ├── core/
│   │   └── exceptions.py
│   ├── schemas/
│   │   ├── assets.py
│   │   ├── base.py
│   │   ├── weather.py
│   │   └── recommendations.py
│   ├── services/
│   │   ├── weather_client.py
│   │   └── recommendation_kernel/
│   │       ├── engine.py
│   │       ├── filters.py
│   │       ├── llm/
│   │       │   ├── base.py
│   │       │   ├── openai_handler.py
│   │       │   └── prompt_templates.py
│   │       └── retrieval/
│   │           ├── base.py
│   │           ├── vector_retrieval.py
│   │           └── json_retriever.py
│   └── utils/
│       └── redis_cache.py
├── tests/
├── pyproject.toml
└── README.md
```

### API Endpoints

#### Health Check

```shell
GET /api/v1/health
```

#### Recommendations

```shell
POST /api/v1/recommendations/complex
POST /api/v1/recommendations/simple
```

#### Simple Recommendation Request

```shell
{
    "location": "Warsaw"
}
```

#### Complex Recommendation Request

```shell
{
    "location": "Warsaw",
    "style_preferences": ["casual", "modern"],
    "gender": "unisex",
    "fit_preference": "regular"
}
```

### Configuration 

#### Environment Variables

```shell
# Core Settings
ENVIRONMENT=dev
API_V1_STR=/api/v1
RECOMMENDATION_API_PROJECT_NAME=WearThe Recommendation Service

# Weather Service
WEATHER_SERVICE_URL=http://weather-service:8000
WEATHER_SERVICE_TIMEOUT=10

# Redis Settings
REDIS_CONNECTION_STRING=your-redis-connection-string

# LLM Settings
LLM_PROVIDER=openai
OPEN_AI_API_KEY=your-openai-key
OPEN_AI_MODEL=gpt-4
OPEN_AI_TEMPERATURE=0.25

# Assets Configuration
ASSETS_SOURCE=json
ASSETS_PATH=/app/local_data/preprocessed/clothing_data.json

# Recommendation Settings
MAX_RECOMMENDATIONS=5
RECOMMENDATION_CACHE_EXPIRATION=3600
```

## Deployment and CI/CD:

### Manual Deployment

The process of manual deployment is fully described [here](./docs/manual_deployment.md).

### CI/CD

[TBD]

---

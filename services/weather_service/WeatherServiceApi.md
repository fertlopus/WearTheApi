# Weather Service documentation:

----

## Overview:

The Weather Service is one of the core components of the backend for the WearThe iOS application, responsible for 
retrieving current weather data from the **OpenWeather API**. It supports fetching weather data using 2 methods:

1. By **City Name** and optional **Country Code**.
2. By **Latitude** and **Longitude**.

The service includes efficient caching mechanism using Redis to minimize the OpenWeather API costs and improve performance
by reducing redundant requests from the clients inside the same location (location based caching).

---

## Features:

* Fetch current weather data using *City Name* + *Country Code* or *Latitude + Longitude*.
* Implemented caching for: 
    * Geo-Location lookups *e.g. resolving coordinates to city name).
    * Weather data responses
* Health check endpoint for monitoring service availability.
* Supports dependency injection for scalable and testable design.

---

## API Endpoints:

1. **Health Check**
* URL: /api/v1/health
* Method: `GET`
* Description: check if the Weather Service is operational.

*Example Response*:

```json
{
  "status": "Service is OK."
}
```

2. **Get Weather by Location**:
* URL: /api/v1/weather
* Method: `POST`
* Requested Body:
  * *city*: name of the city (required).
  * *country_code*: ISO 3166 country code (optional).

```json
{
  "city": "Warsaw",
  "country_code": "PL"
}
```

Example of the response:

```json
{
  "temperature": 0,
  "feels_like": 0,
  "temperature_min": 0,
  "temperature_max": 0,
  "humidity": 0,
  "pressure": 0,
  "description": "string",
  "weather_group": "string",
  "wind_speed": 0,
  "rain": 0,
  "snow": 0,
  "date": 0,
  "weather_id": 0,
  "location": "string",
  "country": "string",
  "timestamp": 0,
  "sunrise": 0,
  "sunset": 0
}
```

Behavior:

* Cached by **CACHE KEY**: `weather:city:<city>:<country_code>`
* If the response is cached, it is returned from Redis.
* If not, the OpenWeather API is queried, and the result is cached for future use.
* Cache refresh period: 4 hours.

---

### Local Run and Test

To run the Weather Service locally you need to use docker-compose and the following steps:
1. At the root of the project run:
```
$ docker-compose build --no-cache
```
2. After the build succeeded up the containers:
```
$ docker-compose up -d
```
3. After you will finish testing:
```
$ docker-compose down
```
The logs are available by the service name:
```
$ docker-compose logs weather-service
```


## TODOs:

- [ ] Implement the messaging broker for the requests handling.
- [ ] Add a deployment configuration file and logic for MS Azure.
- [ ] Cover with integration and system tests.
- [ ] Support for historical weather data.
- [ ] Customizable cache expiration.
- [ ] Integration with GeoCoding APIs
- [ ] Monitoring

--- 

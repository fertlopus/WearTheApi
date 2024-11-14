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
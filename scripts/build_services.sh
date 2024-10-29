#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [-s service_name] [-t tag] [-e environment]"
    echo "  -s: Specific service to build"
    echo "  -t: Docker image tag (default: latest)"
    echo "  -e: Environment (dev/staging/prod)"
    exit 1
}

# Parse command line arguments
while getopts "s:t:e:" opt; do
    case $opt in
        s) SERVICE="$OPTARG";;
        t) TAG="$OPTARG";;
        e) ENV="$OPTARG";;
        ?) usage;;
    esac
done

# Set defaults
TAG=${TAG:-latest}
ENV=${ENV:-dev}

# Function to build a service
build_service() {
    local service=$1
    echo "Building $service for $ENV environment..."

    cd "services/$service" || exit

    # Build Docker image with build args
    docker build \
        --build-arg ENV=$ENV \
        --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
        --build-arg VERSION=$TAG \
        -t "wearthe/$service:$TAG" \
        -t "wearthe/$service:$ENV" \
        .

    cd ../..
}

# Build specific service or all services
if [ -n "$SERVICE" ]; then
    build_service "$SERVICE"
else
    for service in weather_service recommendation_service; do
        build_service "$service"
    done
fi

#!/bin/bash

# Function to display usage
usage() {
    echo "Usage: $0 [-s service_name] [-e environment]"
    echo "  -s: Specific service to test (weather_service/recommendation_service)"
    echo "  -e: Environment (dev/staging/prod)"
    exit 1
}

# Parse command line arguments
while getopts "s:e:" opt; do
    case $opt in
        s) SERVICE="$OPTARG";;
        e) ENV="$OPTARG";;
        ?) usage;;
    esac
done

# Set default environment
ENV=${ENV:-dev}

# Function to run tests for a service
run_service_tests() {
    local service=$1
    echo "Running tests for $service in $ENV environment..."

    cd "services/$service" || exit

    # Load environment variables
    if [ -f ".env.$ENV" ]; then
        source ".env.$ENV"
    fi

    # Run tests based on environment
    if [ "$ENV" = "dev" ]; then
        poetry run pytest tests/unit --cov=app --cov-report=xml
    elif [ "$ENV" = "staging" ]; then
        poetry run pytest tests/integration --cov=app --cov-report=xml
    else
        poetry run pytest tests/ --cov=app --cov-report=xml
    fi

    cd ../..
}

# Run tests for specific service or all services
if [ -n "$SERVICE" ]; then
    run_service_tests "$SERVICE"
else
    for service in weather_service recommendation_service; do
        run_service_tests "$service"
    done
fi

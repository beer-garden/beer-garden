# REST API Integration Testing

This part of the repository is for testing the beer-garden REST API.

## Running Locally

If you are running the `develop` branch and have some changes you'd like to run through a more rigorous testing environment, you can use this. Simply get your application running however you see fit. Edit `config.json` if you're not running on `localhost:2337` then simply run `nosetests`.

## Using Docker Compose

Before beer-garden goes out, we should be running integration tests on the latest `develop` branch. That's what the `docker-compose.yml` is for. Simply run `docker-compose up` and it should run the integration tests.

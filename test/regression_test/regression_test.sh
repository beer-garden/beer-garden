#!/bin/bash

## All of the versions to test
versions=("3.26.4","3.26.3","3.26.2","3.26.1","3.26.0","3.25.1","3.25.0","3.24.4","3.24.3","3.24.2","3.24.1","3.24.0","3.23.1","3.23.0","3.22.0","3.21.0","3.20.0")
# versions=("3.23.0")

## now loop through the above array
for version in "${versions[@]}"
do
	echo "Running $version"
	
	# Download docker image
	docker image pull bgio/beer-garden:$version
	
	# Tag image for testing
	docker image tag bgio/beer-garden:$version bgio/beer-garden:regression
	
	# Start BG
	docker-compose up -d mongodb rabbitmq beer-garden-parent beer-garden-child
	
	# Give BG a minute to start up
    echo "Wait 60 seconds"
	sleep 60s
	
	# Pre-Load database
    echo "Load Database"
	docker-compose up jmeter-loader | tee $version-jmeter-preload-database.log &

	# Give BG a minute to process requests
    echo "Wait 120 seconds"
	sleep 120s
	
	# Run testing
    echo "Run Tests"
	docker-compose up jmeter-testing-requests | tee $version-jmeter-request.log &
	docker-compose up jmeter-testing-events | tee $version-jmeter-events.log &
	docker-compose up jmeter-testing-ui | tee $version-jmeter-ui.log &
	docker-compose up jmeter-testing-start-stop | tee $version-jmeter-start-stop.log &
	wait
	
	# Evaluate the output files to grab metrics
	# echo "jmeter-rates=$(cat jmeter-request.log | grep 'summary' | tail -1 | cut -d '|' -f 2- | sed 's/^.*summary/summary/')\n"
   
	# Cleanup Environment
	docker-compose down
	docker rm -f $(docker ps -a -q)
	docker volume rm $(docker volume ls -q)
	
	docker rmi bgio/beer-garden:regression

done
Bartender
=================================

Bartender is the beer-garden backend. It's responsible for maintaining plugin health/status and running the actual plugins.

## Getting Started

### Pre-requisites:

* Python >= 2.7, 3.4
* pip
* Connectivity to MongoDB Server  - (Tested on 3.4)
* Connectivity to Rabbitmq-Server - (Tested on 3.6)


### Get Up and Running

These are the minimum required steps once you have all the pre-requisites up and running.

* `git clone https://github.com/beer-garden/bartender.git`
* `cd bartender`
* `pip install -r requirements.txt`
* Ensure that Brew View is running
* `./bin/app.sh`
Visit: http://localhost:2337/api/v1/systems


By default, there are several plugins automatically loaded.

## Testing

* `cd bartender`
* `nosetests`

## Code Coverage

* `cd beer-garden`
* `./bin/generate_coverage.sh`
* `Open Firefox`
* Navigate to: `file:///path/to/beer-garden/bartender/output/python/html/index.html`

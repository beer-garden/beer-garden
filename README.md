Beer Garden
=================================

Looking for better documentation? Check out [our home page beer-garden.io](https://beer-garden.io)

Beer Garden is a Framework that provides a standardized interface for Command and Control of systems through the use of plugins or services. In general, Beer Garden Services should be stateless (or as stateless as it can be) and should operate in terms of requests, systems and commands.

![Beer Garden Demo](https://github.com/beer-garden/beer-garden.io/raw/master/images/demo.gif)

## Getting Started

If you would like to run your own Beer Garden, you may follow these steps. If you are a Beer Garden Developer, you will probably want to work on the individual submodules.

### Pre-requisites:

* Python2.7 or 3.6
* pip
* MongoDB Server  >= 3.2.0
* Rabbitmq-Server >= 3.0.0

or

* docker
* docker-compose

### Get Up and Running

We are going to use `docker` and `docker-compose` to install and run beer-garden.

The first step is to clone the git repository that contains the `docker-compose.yml` file:

```
git clone git@github.com:beer-garden/beer-garden.git
cd beer-garden/docker/docker-compose
```

Beer Garden needs to inform remote plugins the hostname of the RabbitMQ instance that they should connect to for message. This value is set as the `BG_AMQ_PUBLISH_HOST` in the environment or `amq_publish_host` in config/command-line arguments. By default in the `docker-compose.yml` it will be `rabbitmq`. This will work for containers running on the same network, but if a truly remote plugin exists, you may need to change the value to a resolvable hostname or IP address on the network.

Run this command to start beer-garden:

```
docker-compose up -d
```

This will create the necessary docker containers and then run them in the background. Run the folloing command to see the log output from the containers starting:

```
docker-compose logs -f
```

Look for a line that says "Bartender started" - once you see that beer-garden is up and running. Use `ctrl-C` to exit.

beer-garden starts by default on port 2337, so point a browser at `http://<IP-ADDRESS>:2337`. You'll see a message saying beer-garden couldn't find any systems. You're ready to start writing plugins!

## Rest Services

The Rest services beer-garden provides is documented by swagger which will come installed by default on the server you stood up. Go to the About section and click on `Rest API Documentation` for more information.

## Testing

Each of the individual submodules has ways to test individual portions of the application.

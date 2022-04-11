# Beer Garden

## Quick Reference

- **Maintained by**: [the beer-garden team](https://github.com/beer-garden)
- **Where to file issues**:
  [beer-garden github issues](https://github.com/beer-garden/beer-garden/issues)
- **Source of this description**:
  [beer-garden github](https://github.com/beer-garden/beer-garden/tree/develop/src/app/docker/README.md)

## What is Beer Garden

Beer Garden is a powerful plugin framework for converting your functions into
composable, discoverable, production-ready services with minimal overhead. For
more information see the
[beer-garden github](https://github.com/beer-garden/beer-garden/) and
[official documentation](https://beer-garden.io/).

## Note regarding alpine images

These instructions do not apply to images tagged with `-alpine`. The `-alpine`
images are maintained for legacy support and will continue to be published with
new releases for the time being. A decision to either retire the `-alpine`
images or update them to be consistent with the other supported images will be
made at some point in the future.

## How to use this image

Running beer-garden requires the following services:

- mongodb
- rabbitmq

Your beer-garden instance must be configured so that it knows how to communicate
with these services. This can be done a handful of ways, which will be shown
below.

If you want to quickly start up a fully functioning beer-garden to expirement
with, a
[docker-compose.yaml](https://github.com/beer-garden/beer-garden/blob/develop/docker/docker-compose/docker-compose.yml)
is available that should work out of the box, while also acting as a useful
starting point for configuring your own beer-garden stack.

### Configure using command line arguments

```shell
$ docker run --name beergarden -d bgio/beer-garden:<tag> \
    --mq-host <rabbitmq host> \
    --mq-connections-message-user <rabbitmq user> \
    --mq-connections-message-password <rabbitmq password> \
    --mq-connections-admin-user <rabbitmq user> \
    --mq-connections-admin-password <rabbitmq password> \
    --db-connection-host <mongodb host> \
    --db-connection-port <mongodb port> \
    --db-connection-username <mongodb username> \
    --db-connection-password <mongodb password>
```

To see the full list of available command line arguments:

```shell
$ docker run --rm --name beergarden bgio/beer-garden:<tag> --help
```

### Configure using environment variables

Environment variables can be used in place of command line arguments. Each
available argument can be set instead by an environment variable of the same
name, except it is all uppercase, contains underscores in place of dashes, and
is prefixed with BG\_. For example, the equivalent of `--mq-host` would be
`BG_MQ_HOST`.

```shell
$ docker run --name beergarden \
    -e BG_MQ_HOST=<rabbitmq host> \
    -e BG_MQ_CONNECTIONS_MESSAGE_USER <rabbitmq user> \
    -e BG_MQ_CONNECTIONS_MESSAGE_PASSWORD <rabbitmq password> \
    -e BG_MQ_CONNECTIONS_ADMIN_USER <rabbitmq user> \
    -e BG_MQ_CONNECTIONS_ADMIN_PASSWORD <rabbitmq password> \
    -e BG_DB_CONNECTION_HOST <mongodb host> \
    -e BG_DB_CONNECTION_PORT <mongodb port> \
    -e BG_DB_CONNECTION_USERNAME <mongodb username> \
    -e BG_DB_CONNECTION_PASSWORD <mongodb password> \
    -d bgio/beer-garden:<tag>
```

### Configure using a configuration file

You can also mount in a configuration file and instruct beer-garden to use it:

```shell
$ docker run --name beergarden \
    -v /path/to/config.yaml:/conf/config.yaml \
    -d bgio/beer-garden:<tag> \
    --configuration-file /conf/config.yaml
```

The beer-garden repo has an
[example configuration file](https://github.com/beer-garden/beer-garden/blob/develop/src/app/example_configs/config.yaml)
that can be used as a reference for starting out.

## Local plugins

By default, beer-garden will look in `/plugins`. If you wish to run local
plugins, you should mount the directory containing the plugins on the host to
that directory on the container.

> **NOTE**: Currently local plugins can only be configured via a configuration
> file, as described above. Plugins will not be able to read required
> configuration that is supplied via command line arguments or environment
> variables.

### Adding plugin dependencies

When the beer-garden container starts, it will install any python dependencies
listed in `/conf/requirements.txt`. If your local plugins have dependencies
beyond what is required to run beer-garden itself, you can volume mount your own
`requirements.txt` to that location to have them installed during container
startup.

> **NOTE**: The ability to install additional dependencies is provided as a
> convenience, but is **not recommended** due to the inherent risks involved.
> Sepcifically, it is very possible to install a non-compatible version of a
> dependency that beer-garden itself relies on, breaking your beer-garden
> instance in both obvious and not-so-obvious ways. If you have additional
> dependencies for your plugins, it is recommended that you use
> [remote plugins](https://beer-garden.io/docs/plugins/python/remote-guide/)
> rather than local plugins.

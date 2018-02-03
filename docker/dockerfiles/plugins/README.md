# Dockerfile for beer-garden Plugins

These docker files contain an environment ready for plugin development.

### Description

Each python environment is loaded with an ubuntu base image and pyenv installed.
The images also come with a version of python installed based on which tag
you pull down.

### Supported Tags

`beer-garden/plugins` image currently supports the below tags.
Each link is its Dockerfile:

* `python2` [(python2/Dockerfile)][1]
* `python3` [(python3/Dockerfile)][2]
* `python2-onbuild` [(python2/onbuild/Dockerfile)][3]
* `python3-onbuild` [(python3/onbuild/Dockerfile)][4]


### Usage

In order to run your plugin as a docker container, you first need to create a
plugin. Let's assume you have a running beer-garden on `localhost` and you've
written your plugin in python as follows:

```python
from brewtils.decorators import command_registrar, plugin_param
from brewtils.plugin import RemotePlugin

@command_registrar
class HelloWorld(object):

  @plugin_param(key="message", type="String")
  def do_something(self, message):
    print(message)
    return message

if __name__ == "__main__":
  my_client = HelloWorld()
  my_plugin = RemotePlugin(my_client, name='hello-world', version='0.0.1',
                           bg_host='localhost', bg_port=2337, ssl_enabled=False)
  my_plugin.run()
```

Save that off as a file `__main__.py`. You should be able to run:

```
docker run -v $(pwd):/src beer-garden/plugins:python2
```

Congratulations! Your plugin works! If you want to name your file something else
you can do that, you just need to modify the run statement:

```
docker run -v $(pwd):/src beer-garden/plugins:python2 python /src/my_cool_filename.py
```


### onbuild Usage

The `onbuild` is useful if you have additional dependencies. It operates on two
different files:

1. `requirements.txt`
2. `install-prereqs.sh`

For python images, it will take your `requirements.txt` file and feed it
automatically to `pip` in order to make building derivative images easier. For
most use cases, creating a `Dockerfile` in the base of your project directory
with the line
`FROM beer-garden/plugins:python3-onbuild` will be
enough to create a stand-alone image for your project. If you have non-python
dependencies that you need installed, you can write whatever you like in
`install-prereqs.sh` and it will execute that. Let's assume you have a
dependency on `libssl-devel`, you could add the following to your
`install-prereqs.sh`:

```
apt-get install libssl-devel
```

Then you simply build your image and all the python & additional dependencies
will be built for you.

While the `onbuild` variant is really useful for "getting off the ground
running" (zero to Dockerized in a short period of time), it's not recommend for
long-term usage within a project due to the lack of control over __when__ on
`ONBUILD` triggers fire. Once you've got handle on how your project functions
within Docker, you'll probably want to adjust your `Dockerfile` to inherit from
a non-`onbuild` variant and copy the commands from the `onbuild` variant
`Dockerfile` (moving the `ONBUILD` lines to the end and remove the `ONBUILD`
keywords) into your own file so that you have tighter control over them and
more transparency for yourself and others looking at your `Dockerfile` as to
what it does. This also makes it easier to add additional requirements as time
goes on (such as installing more packages before performing the
previously-`ONBUILD` steps).

### Author

loganasherjones
[1]: https://github.com/beer-garden/beer-garden/blob/master/docker/dockerfiles/plugins/python2/Dockerfile
[2]: https://github.com/beer-garden/beer-garden/blob/master/docker/dockerfiles/plugins/python3/Dockerfile
[3]: https://github.com/beer-garden/beer-garden/blob/master/docker/dockerfiles/plugins/python2/onbuild/Dockerfile
[4]: https://github.com/beer-garden/beer-garden/blob/master/docker/dockerfiles/plugins/python3/onbuild/Dockerfile

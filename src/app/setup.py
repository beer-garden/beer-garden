import re

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


setup(
    name="beer-garden",
    version=find_version("beer_garden/__version__.py"),
    description="Beergarden Application",
    long_description=readme,
    author="The Beer Garden Team",
    author_email="beer@beer-garden.io",
    url="https://beer-garden.io",
    packages=(find_packages(exclude=["test", "test.*"])),
    license="MIT",
    keywords="beer beer-garden beergarden",
    install_requires=[
        "apispec<0.39",
        "apscheduler<4",
        "python-box>=3.3.0",
        "brewtils>=3.28.0",
        "marshmallow<3",
        "mongoengine<0.21",
        "more-itertools<9",
        "motor<3",
        "passlib<1.8",
        "prometheus-client<1",
        "pyyaml<5.4",
        "pyrabbit2<2",
        "pytz<2021",
        "pyjwt>=2.4.0",
        "ruamel.yaml<0.17",
        "stomp.py<6.2.0",
        "tornado<7",
        "urllib3<2",
        "watchdog>2.1.0",
        "wrapt",
        "yapconf>=1.0.0",
        "elastic-apm"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "beergarden=beer_garden.__main__:main",
            "generate_config=beer_garden.__main__:generate_config",
            "migrate_config=beer_garden.__main__:migrate_config",
            "generate_app_logging_config=beer_garden.__main__:generate_app_logging_config",
            "generate_plugin_logging_config=beer_garden.__main__:generate_plugin_logging_config",
            # For backwards compatibility
            "migrate_bartender_config=beer_garden.__main__:deprecate_config",
            "migrate_brew_view_config=beer_garden.__main__:deprecate_config",
        ]
    },
)

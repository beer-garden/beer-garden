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
    name="beer_garden",
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
        # "brewtils>=3.29.0",
        
        "apispec>=6.7,<7",
        "apispec-webframeworks>1,<2",

        "apscheduler<4",

        # YAPCONF Conflict with python-box
        "python-box<4",

        "marshmallow<4,>=3.3",
        "more-itertools<11", 

        # pymongo dependency between motor and mongoengine
        "pymongo>=4.9,<4.10",
        "mongoengine>=0.29.1",
        "motor>3,<4",

        "passlib<1.8",
        "prometheus-client<1",
        "pyyaml<7",
        "pyasn1<0.6.0",
        "pyrabbit2<2",
        "pyjwt>=2.4.0",

        # Can go to 18 after yapconf 0.4 is released
        "ruamel.yaml<0.18",
        "stomp.py<9",
        "tornado<7",
        "urllib3<3",
        "watchdog<6",
        "wrapt",
        "yapconf<1.0",
        "elastic-apm",
        "ldap3>=2.9.1"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
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

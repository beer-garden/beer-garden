import re

from setuptools import find_packages, setup

# read the contents of the README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


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
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="The Beer Garden Team",
    author_email="beer@beer-garden.io",
    url="https://beer-garden.io",
    packages=(find_packages(exclude=["test", "test.*"])),
    license="MIT",
    keywords="beer beer-garden beergarden",
    install_requires=[
        "brewtils>=3.31.1",

        # Using Latest Version   
        "apispec>=6.7,<7", # Latest 6.8.4
        "apispec-webframeworks>1,<2", # Latest 1.2.0
        "apscheduler<4", # Latest 3.11.0
        "more-itertools<11", # Latest 10.8.0
        "wrapt", # Latest 1.17.3      
        "elastic-apm", # Latest 6.24.0
        "ldap3>=2.9.1", # Latest 2.9.1
        "pyrabbit2<2", # Latest 1.0.7
        "pyjwt>=2.4.0", # Latest 2.10.1
        "passlib<1.8", # Latest 1.7.4
        "prometheus-client<1", # Latest 0.23.1
        "pyyaml<7", # Latest 6.0.3
        "stomp.py>=7,<9", # Latest 8.2.0
        "tornado<7", # Latest 6.5.2
        "urllib3<3", # Latest 2.5.0
        "watchdog<6.1", # Latest 6.0.0

        # Pymongo needs 4.9 for Async features from motor
        # Pymongo needs mockmongo to fix issue #912 before we can go past
        # pymongo 4.11
        "pymongo>=4.9,<4.11", # Latest 4.15.1
        "mongoengine>=0.29.1", # Latest 0.29.1
        
        # YAPCONF Conflict with python-box
        "python-box<4", # Latest 7.3.2     
        # Can't go to 18 after yapconf migrates away from _safe functions
        "ruamel.yaml<0.18", # Latest 0.18.5
        "yapconf<0.5", # Latest 0.4.0

        # Brewtils drives marshmallow version
        "marshmallow<4.1,>=4.0", # Latest 4.0.1
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
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

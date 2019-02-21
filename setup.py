import re

from setuptools import setup, find_packages


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


setup(
    name="bg-utils",
    version=find_version("bg_utils/_version.py"),
    description="Shared utilities for beer-garden application components",
    url="https://beer-garden.io/",
    author="The beer-garden Team",
    author_email=" ",
    license="MIT",
    packages=find_packages(exclude=["test", "test.*"]),
    package_data={"": ["README.md"], "bg_utils": ["thrift/*.thrift"]},
    install_requires=[
        "brewtils>=2.3.0",
        "mongoengine<0.16",
        "passlib<1.8",
        "pytz<2019",
        "ruamel.yaml<0.16",
        "thriftpy2<0.5",
        "yapconf>=0.3.3",
    ],
)

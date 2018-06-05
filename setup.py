import re

from setuptools import setup, find_packages


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


setup(
    name='bg-utils',
    version=find_version('bg_utils/_version.py'),
    description='Shared utilities for beer-garden application components',
    url=' ',
    author='The beer-garden Team',
    author_email=' ',
    license='MIT',
    packages=find_packages(exclude=['test', 'test.*']),
    package_data={'': ['README.md'], 'bg_utils': ['thrift/*.thrift']},
    install_requires=[
        'brewtils>=2.3.0',
        'mongoengine',
        'thriftpy',
        'yapconf<=0.2.3',
    ]
)

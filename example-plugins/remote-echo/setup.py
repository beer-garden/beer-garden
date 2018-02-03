import re

from setuptools import setup


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


setup(
    name='remote-echo',
    version=find_version('remote_echo/_version.py'),
    description='Remote plugin that echos input strings',
    url=' ',
    author='The beer-garden Team',
    author_email=' ',
    license='MIT',
    packages=['remote_echo'],
    install_requires=[
        'brewtils==2.2.0',
        'click==6.7'
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ]
)


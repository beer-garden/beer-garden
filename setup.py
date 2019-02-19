import re

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


setup(
    name="bartender",
    version=find_version("bartender/_version.py"),
    description="Beergarden Backend",
    long_description=readme,
    author="The beer-garden Team",
    author_email="bartender@beer-garden.io",
    url="https://beer-garden.io",
    packages=(find_packages(exclude=["test", "test.*"])),
    license="MIT",
    keywords="bartender beer beer-garden beergarden",
    install_requires=["bg-utils>=2.4.4", "brewtils>=2.4.0", "pyrabbit2==1.0.5"],
    extras_require={
        ':python_version=="2.7"': [
            "future>=0.16.0",
            "futures>=3.1.1",
            "subprocess32>=3.2.7",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    entry_points={
        "console_scripts": [
            "generate_bartender_config=bartender.__main__:generate_config",
            "migrate_bartender_config=bartender.__main__:migrate_config",
            "generate_bartender_log_config=bartender.__main__:generate_logging_config",
            "bartender=bartender.__main__:main",
        ]
    },
)

import re

from setuptools import setup, find_packages


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


with open("README.rst") as readme_file:
    readme = readme_file.read()


setup(
    name="brew-view",
    version=find_version("brew_view/_version.py"),
    description="Beergarden Frontend",
    long_description=readme,
    url="https://beer-garden.io/",
    author="The beer-garden Team",
    author_email=" ",
    license="MIT",
    packages=(find_packages(exclude=["test", "test.*"])),
    include_package_data=True,
    install_requires=[
        "apispec==0.38.0",
        "apscheduler==3.5.1",
        "bg-utils>=2.4.4",
        "brewtils>=2.4.0",
        "prometheus_client==0.3.1",
        "tornado==5.1",
    ],
    extras_require={':python_version=="2.7"': ["futures>=3.1.1"]},
    entry_points={
        "console_scripts": [
            "generate_brew_view_config=brew_view.__main__:generate_config",
            "migrate_brew_view_config=brew_view.__main__:migrate_config",
            "generate_brew_view_log_config=brew_view.__main__:generate_logging_config",
            "brew-view=brew_view.__main__:main",
        ]
    },
)

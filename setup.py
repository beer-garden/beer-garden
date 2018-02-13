import re

from setuptools import setup, find_packages


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


setup(
    name='bartender',
    version=find_version('bartender/_version.py'),
    description='Beergarden Backend',
    url=' ',
    author='The beer-garden Team',
    author_email=' ',
    license='MIT',
    packages=(find_packages(exclude=['test', 'test.*'])),
    install_requires=[
        'bg-utils>=2.3.1',
        'pika==0.11.0',
        'pyrabbit2==1.0.0',
        'futures==3.1.1;python_version<"3.0"',
        'subprocess32==3.2.7;python_version<"3.0"'
    ],
    entry_points={
        'console_scripts': [
            'generate_bartender_config=bartender.__main__:generate_config',
            'migrate_bartender_config=bartender.__main__:migrate_config',
            'generate_bartender_log_config=bartender.__main__:generate_logging_config',
            'bartender=bartender.__main__:main'
        ]
    }
)

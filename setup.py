import re

from setuptools import setup, find_packages


def find_version(version_file):
    version_line = open(version_file, "rt").read()
    match_object = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_line, re.M)

    if not match_object:
        raise RuntimeError("Unable to find version string in %s" % version_file)

    return match_object.group(1)


setup(
    name='brew-view',
    version=find_version('brew_view/_version.py'),
    description='Beergarden Frontend',
    url=' ',
    author='The beer-garden Team',
    author_email=' ',
    license='MIT',
    packages=(find_packages(exclude=['tests', 'tests.*'])),
    package_data={
        '': ['*.txt', '*.js', '*.html', '*.css', '*.scss', '*.less', '*.otf', '*.eot', '*.svg', '*.gif', '*.png',
             '*.ttf', '*.woff', '*.woff2']
    },
    include_package_data=True,
    install_requires=[
        "apispec==0.25.4",
        "bg-utils==2.4.0",
        "tornado==4.5.2",
        'futures==3.1.1;python_version<"3.0"'
    ],
    entry_points={
        'console_scripts': [
            'generate_brew_view_config=brew_view.__main__:generate_config',
            'migrate_brew_view_config=brew_view.__main__:migrate_config',
            'generate_brew_view_log_config=brew_view.__main__:generate_logging_config',
            'brew-view=brew_view.__main__:main'
        ]
    }
)

from setuptools import setup, find_packages

setup(
    name="sleeper",
    description="A really lazy plugin.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={'console_scripts': 'sleeper=main:main'},
    install_requires=['bg-utils']
)

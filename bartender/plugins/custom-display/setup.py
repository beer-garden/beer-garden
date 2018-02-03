from setuptools import setup, find_packages

setup(
    name="custom-display",
    description="Plugin that likes to play pretend.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=['bg-utils']
)

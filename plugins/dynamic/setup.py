from setuptools import setup, find_packages

setup(
    name="dynamic",
    description="Plugin that repeats very specific stuff.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={'console_scripts': 'dynamic=main:main'},
    install_requires=['bg-utils']
)

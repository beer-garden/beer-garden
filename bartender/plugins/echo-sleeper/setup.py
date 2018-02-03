from setuptools import setup, find_packages

setup(
    name="echo-sleeper",
    description="A plugin that's annoying AND lazy.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={'console_scripts': 'echo-sleeper=main:main'},
    install_requires=['bg-utils']
)

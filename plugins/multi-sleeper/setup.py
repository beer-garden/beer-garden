from setuptools import setup, find_packages

setup(
    name="multi-sleeper",
    description="Multithreaded for more efficient laziness.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={'console_scripts': 'multi-sleeper=main:main'},
    install_requires=['bg-utils']
)

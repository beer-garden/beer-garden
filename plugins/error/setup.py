from setuptools import setup, find_packages

setup(
    name="error",
    description="All commands end in errors. There is no hope.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={'console_scripts': 'error=main:main'},
    install_requires=['bg-utils']
)

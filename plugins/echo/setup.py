from setuptools import setup, find_packages

setup(
    name="echo",
    description="Annoying plugin that just repeats stuff",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={'console_scripts': 'echo=main:main'},
    install_requires=['bg-utils']
)

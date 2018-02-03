from setuptools import setup, find_packages

setup(
    name="multi-echo-sleeper",
    description="This plugin is the worst.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    entry_points={'console_scripts': 'multi-echo-sleeper=main:main'},
    install_requires=['bg-utils']
)

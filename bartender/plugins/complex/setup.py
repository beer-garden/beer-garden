from setuptools import setup, find_packages

setup(
    name="complex",
    description="Plugin that shows all the cool things Beergarden can do.",
    version="1.0.0.dev",
    py_modules=['main'],
    packages=find_packages(exclude=['test', 'test.*']),
    install_requires=['bg-utils']
)

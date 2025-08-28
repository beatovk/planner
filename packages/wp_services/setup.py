from setuptools import setup, find_packages

setup(
    name="wp_services",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
    ],
)

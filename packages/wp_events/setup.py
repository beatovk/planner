from setuptools import setup, find_packages

setup(
    name="wp_events",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "httpx>=0.24.0",
    ],
)

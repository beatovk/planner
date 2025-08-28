from setuptools import setup, find_packages

setup(
    name="wp_places",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "sqlite-utils>=3.35.0",
    ],
)

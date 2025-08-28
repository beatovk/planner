from setuptools import setup, find_packages

setup(
    name="wp_cache",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "redis>=4.5.0",
    ],
)

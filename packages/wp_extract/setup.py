from setuptools import setup, find_packages

setup(
    name="wp_extract",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
        "beautifulsoup4>=4.12.0",
    ],
)

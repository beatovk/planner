from setuptools import setup, find_packages

setup(
    name="wp_tags",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    package_data={
        "wp_tags": ["*.yaml", "*.yml"],
    },
)

"""
Logging configuration for places package.
"""

import logging

# Create logger for places package
logger = logging.getLogger("places")

# Set default level
logger.setLevel(logging.INFO)

# Create console handler if none exists
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

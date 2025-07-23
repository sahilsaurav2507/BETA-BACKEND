#!/usr/bin/env python3
"""
Install Async Dependencies Script
=================================

This script installs the required async dependencies for the performance
optimizations to work properly.
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_package(package):
    """Install a package using pip."""
    try:
        logger.info(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logger.info(f"Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package}: {e}")
        return False

def main():
    """Install all required async dependencies."""
    logger.info("Installing async dependencies for performance optimizations...")
    
    # Required packages for async functionality
    packages = [
        "aiomysql",  # Async MySQL driver
        "brotli",    # Brotli compression
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    logger.info(f"Installation complete: {success_count}/{len(packages)} packages installed successfully")
    
    if success_count == len(packages):
        logger.info("All async dependencies installed successfully!")
        logger.info("You can now use the async performance optimizations.")
    else:
        logger.warning("Some packages failed to install. Async features may not work properly.")
    
    # Test imports
    logger.info("Testing imports...")
    try:
        import aiomysql
        logger.info("✓ aiomysql imported successfully")
    except ImportError:
        logger.error("✗ aiomysql import failed")
    
    try:
        import brotli
        logger.info("✓ brotli imported successfully")
    except ImportError:
        logger.error("✗ brotli import failed")

if __name__ == "__main__":
    main()

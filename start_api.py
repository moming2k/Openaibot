#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Newsletter API Server Startup Script
Starts the FastAPI server for newsletter content submission
"""
import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use standard logging if loguru not available
try:
    from loguru import logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info = logging.info
    logger.warning = logging.warning
    logger.error = logging.error

# Banner
BANNER = """
██╗     ██╗     ███╗   ███╗██╗  ██╗██╗██████╗  █████╗
██║     ██║     ████╗ ████║██║ ██╔╝██║██╔══██╗██╔══██╗
██║     ██║     ██╔████╔██║█████╔╝ ██║██████╔╝███████║
██║     ██║     ██║╚██╔╝██║██╔═██╗ ██║██╔══██╗██╔══██║
███████╗███████╗██║ ╚═╝ ██║██║  ██╗██║██║  ██║██║  ██║
╚══════╝╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
Newsletter API Server
"""


def main():
    logger.info(BANNER)

    # Check required environment variables
    if not os.getenv("PLUGIN_NEWS_CHANNEL_ID"):
        logger.warning("⚠️ PLUGIN_NEWS_CHANNEL_ID not set - API will not work")

    if not os.getenv("NEWSLETTER_API_KEY"):
        logger.warning("⚠️ NEWSLETTER_API_KEY not set - API endpoints will be unprotected!")

    if not os.getenv("AMQP_DSN"):
        logger.error("❌ AMQP_DSN not set - cannot connect to message queue")
        sys.exit(1)

    # Import and run the server
    import uvicorn
    from app.api.server import app

    port = int(os.getenv("NEWSLETTER_API_PORT", "8765"))
    host = os.getenv("NEWSLETTER_API_HOST", "0.0.0.0")

    logger.info(f"🚀 Starting Newsletter API server on {host}:{port}")
    logger.info(f"📝 Swagger UI available at: http://{host}:{port}/docs")
    logger.info(f"📊 ReDoc available at: http://{host}:{port}/redoc")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

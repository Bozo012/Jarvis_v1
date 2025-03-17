import os
import sys
import time
import signal
from loguru import logger

from mcp.controller import MicroservicesControlPlane
from config.settings import settings


def main():
    """Main entry point for the Local AI Assistant."""
    # Configure logger
    log_level = settings.general.log_level
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    logger.add(f"logs/local-ai-assistant.log", rotation="10 MB", level=log_level)
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    logger.info("Starting Local AI Assistant...")
    
    # Initialize and start MCP
    mcp = MicroservicesControlPlane()
    if not mcp.initialize():
        logger.error("Failed to initialize MCP")
        return 1
        
    if not mcp.start():
        logger.error("Failed to start MCP")
        return 1
        
    logger.info("Local AI Assistant started successfully")
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down...")
        mcp.stop()
        logger.info("Local AI Assistant stopped")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        mcp.stop()
        logger.info("Local AI Assistant stopped")
        
    return 0


if __name__ == "__main__":
    sys.exit(main())

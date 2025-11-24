#!/usr/bin/env python3
"""Main entry point for Graffiti Graph MCP Server.

This is the primary entry point for running the MCP server.

Usage:
    python main.py
    or
    uv run main.py
    or
    python -m src
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from src.mcp_server import run_server


def main():
    """Main entry point for the MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,  # Log to stderr to avoid interfering with MCP stdio
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Graffiti Graph MCP Server...")
    logger.info("Server name: graffiti-graph-mcp")
    logger.info("Server version: 0.1.0")
    logger.info("Transport: stdio")
    
    try:
        # Run the server
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


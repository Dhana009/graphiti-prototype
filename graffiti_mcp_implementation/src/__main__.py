"""Entry point for Graffiti Graph MCP Server.

This module allows the package to be run as a module:
    python -m src

Or via the entry point defined in pyproject.toml:
    graffiti-mcp-server
"""

import asyncio
import logging
import sys

from .mcp_server import run_server


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


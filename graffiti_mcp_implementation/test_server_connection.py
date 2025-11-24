#!/usr/bin/env python3
"""Quick test script to verify MCP server can start and list tools."""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp_server import handle_list_tools, server
from src.database import DatabaseConnection, initialize_database
from src.config import get_neo4j_config


async def test_server():
    """Test that the server can initialize and list tools."""
    print("Testing MCP Server...")
    print()
    
    # Test 1: List tools
    print("1. Testing tool listing...")
    try:
        tools = await handle_list_tools()
        print(f"   [OK] Successfully listed {len(tools)} tools")
        print(f"   Tools: {', '.join([t.name for t in tools[:5]])}...")
    except Exception as e:
        print(f"   [FAIL] Failed to list tools: {e}")
        return False
    
    # Test 2: Database connection
    print()
    print("2. Testing database connection...")
    try:
        config = get_neo4j_config()
        async with DatabaseConnection(config=config) as connection:
            await initialize_database(connection)
            print(f"   [OK] Successfully connected to Neo4j at {config.uri}")
    except Exception as e:
        print(f"   [FAIL] Failed to connect to database: {e}")
        return False
    
    # Test 3: Server initialization
    print()
    print("3. Testing server initialization...")
    try:
        print(f"   [OK] Server name: {server.name}")
        print(f"   [OK] Server ready for stdio transport")
    except Exception as e:
        print(f"   [FAIL] Server initialization failed: {e}")
        return False
    
    print()
    print("[OK] All tests passed! Server is ready to use.")
    print()
    print("Next steps:")
    print("1. Add the configuration from mcp-config.json to your MCP client")
    print("2. Restart your MCP client (Cursor/Claude Desktop)")
    print("3. The server will start automatically when the client connects")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_server())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[WARN] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


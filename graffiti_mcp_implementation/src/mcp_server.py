"""MCP Server Implementation for Graffiti Graph.

This module implements the MCP server that exposes Graffiti Graph operations
as MCP tools for AI assistants.
"""

import asyncio
import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .config import get_neo4j_config
from .database import DatabaseConnection, initialize_database
from .entities import (
    add_entity,
    get_entity_by_id,
    get_entities_by_type,
    update_entity,
    delete_entity,
    restore_entity,
    EntityError,
    EntityNotFoundError,
    DuplicateEntityError,
)
from .relationships import (
    add_relationship,
    get_entity_relationships,
    soft_delete_relationship,
    restore_relationship,
    hard_delete_relationship,
    RelationshipError,
)
from .search import search_nodes
from .memory import add_memory, update_memory
from .mcp_tools import get_tool_schemas

logger = logging.getLogger(__name__)

# Export handler functions for testing
__all__ = [
    "handle_list_tools",
    "handle_call_tool",
    "server_lifespan",
    "server",
    "run_server",
    # Handler functions for testing
    "_handle_add_entity",
    "_handle_add_relationship",
    "_handle_get_entity_by_id",
    "_handle_get_entities_by_type",
    "_handle_get_entity_relationships",
    "_handle_search_nodes",
    "_handle_add_memory",
    "_handle_update_memory",
    "_handle_soft_delete_entity",
    "_handle_soft_delete_relationship",
    "_handle_restore_entity",
    "_handle_restore_relationship",
    "_handle_hard_delete_entity",
    "_handle_hard_delete_relationship",
]


@asynccontextmanager
async def server_lifespan(_server: Server) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle.
    
    Initializes database connection on startup and cleans up on shutdown.
    """
    config = get_neo4j_config()
    connection = DatabaseConnection(config=config)
    
    try:
        await connection.connect()
        await initialize_database(connection)
        logger.info("Database connection established and initialized")
        
        yield {"connection": connection}
    finally:
        await connection.close()
        logger.info("Database connection closed")


# Create MCP server instance with lifespan management
server = Server("graffiti-graph-mcp", lifespan=server_lifespan)


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available MCP tools."""
    return get_tool_schemas()


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> list[types.TextContent]:
    """Handle MCP tool calls and route to appropriate internal functions.
    
    Args:
        name: Tool name
        arguments: Tool arguments as dictionary
        
    Returns:
        List of TextContent objects with tool results
        
    Raises:
        ValueError: If tool name is unknown
    """
    # Get database connection from lifespan context
    ctx = server.request_context
    connection: DatabaseConnection = ctx.lifespan_context["connection"]
    
    # Log tool call with arguments (sanitize sensitive data)
    import json
    sanitized_args = {k: v for k, v in arguments.items() if 'password' not in k.lower() and 'key' not in k.lower()}
    logger.info(f"Tool called: {name} with arguments: {json.dumps(sanitized_args, default=str)}")
    
    try:
        # Route tool calls to appropriate handlers
        if name == "add_entity":
            result = await _handle_add_entity(connection, arguments)
        elif name == "add_relationship":
            result = await _handle_add_relationship(connection, arguments)
        elif name == "get_entity_by_id":
            result = await _handle_get_entity_by_id(connection, arguments)
        elif name == "get_entities_by_type":
            result = await _handle_get_entities_by_type(connection, arguments)
        elif name == "get_entity_relationships":
            result = await _handle_get_entity_relationships(connection, arguments)
        elif name == "search_nodes":
            result = await _handle_search_nodes(connection, arguments)
        elif name == "add_memory":
            result = await _handle_add_memory(connection, arguments)
        elif name == "update_memory":
            result = await _handle_update_memory(connection, arguments)
        elif name == "soft_delete_entity":
            result = await _handle_soft_delete_entity(connection, arguments)
        elif name == "soft_delete_relationship":
            result = await _handle_soft_delete_relationship(connection, arguments)
        elif name == "restore_entity":
            result = await _handle_restore_entity(connection, arguments)
        elif name == "restore_relationship":
            result = await _handle_restore_relationship(connection, arguments)
        elif name == "hard_delete_entity":
            result = await _handle_hard_delete_entity(connection, arguments)
        elif name == "hard_delete_relationship":
            result = await _handle_hard_delete_relationship(connection, arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Convert result to JSON string for TextContent
        import json
        result_json = json.dumps(result, indent=2, default=str)
        
        # Log successful tool execution
        logger.info(f"Tool {name} executed successfully")
        
        return [types.TextContent(type="text", text=result_json)]
        
    except (EntityNotFoundError, DuplicateEntityError, RelationshipError) as e:
        # Domain-specific errors - return as structured error
        logger.error(f"Tool {name} failed with domain error: {e}")
        error_result = {
            "error": {
                "type": type(e).__name__,
                "message": str(e),
            }
        }
        import json
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
    except (ValueError, TypeError) as e:
        # Validation errors
        logger.error(f"Tool {name} failed with validation error: {e}")
        error_result = {
            "error": {
                "type": "ValidationError",
                "message": str(e),
            }
        }
        import json
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
    except Exception as e:
        # Unexpected errors
        logger.exception(f"Tool {name} failed with unexpected error: {e}")
        error_result = {
            "error": {
                "type": "InternalError",
                "message": f"Internal server error: {str(e)}",
            }
        }
        import json
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]


# Tool handler functions

async def _handle_add_entity(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle add_entity tool call."""
    return await add_entity(
        connection=connection,
        entity_id=args["entity_id"],
        entity_type=args["entity_type"],
        name=args["name"],
        properties=args.get("properties"),
        summary=args.get("summary"),
        group_id=args.get("group_id"),
        episode_uuid=args.get("episode_uuid"),
    )


async def _handle_add_relationship(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle add_relationship tool call."""
    return await add_relationship(
        connection=connection,
        source_entity_id=args["source_entity_id"],
        target_entity_id=args["target_entity_id"],
        relationship_type=args["relationship_type"],
        properties=args.get("properties"),
        fact=args.get("fact"),
        t_valid=args.get("t_valid"),
        t_invalid=args.get("t_invalid"),
        group_id=args.get("group_id"),
    )


async def _handle_get_entity_by_id(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_entity_by_id tool call."""
    try:
        entity = await get_entity_by_id(
            connection=connection,
            entity_id=args["entity_id"],
            group_id=args.get("group_id"),
            include_deleted=args.get("include_deleted", False),
        )
        return entity
    except EntityNotFoundError:
        return {"error": "Entity not found"}


async def _handle_get_entities_by_type(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_entities_by_type tool call."""
    entities = await get_entities_by_type(
        connection=connection,
        entity_type=args["entity_type"],
        group_id=args.get("group_id"),
        limit=args.get("limit"),
    )
    return {"entities": entities, "count": len(entities)}


async def _handle_get_entity_relationships(
    connection: DatabaseConnection, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle get_entity_relationships tool call."""
    relationships = await get_entity_relationships(
        connection=connection,
        entity_id=args["entity_id"],
        direction=args.get("direction", "both"),
        relationship_types=args.get("relationship_types"),
        limit=args.get("limit"),
        group_id=args.get("group_id"),
        include_deleted=args.get("include_deleted", False),
    )
    return {"relationships": relationships, "count": len(relationships)}


async def _handle_search_nodes(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle search_nodes tool call."""
    return await search_nodes(
        connection=connection,
        query=args["query"],
        max_nodes=args.get("max_nodes", 10),
        entity_types=args.get("entity_types"),
        group_id=args.get("group_id"),
    )


async def _handle_add_memory(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle add_memory tool call."""
    return await add_memory(
        connection=connection,
        name=args["name"],
        episode_body=args["episode_body"],
        source=args.get("source", "text"),
        source_description=args.get("source_description"),
        group_id=args.get("group_id"),
        uuid=args.get("uuid"),
    )


async def _handle_update_memory(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update_memory tool call."""
    return await update_memory(
        connection=connection,
        uuid=args["uuid"],
        episode_body=args["episode_body"],
        group_id=args.get("group_id"),
        update_strategy=args.get("update_strategy", "incremental"),
    )


async def _handle_soft_delete_entity(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle soft_delete_entity tool call."""
    return await delete_entity(
        connection=connection,
        entity_id=args["entity_id"],
        group_id=args.get("group_id"),
        hard=False,
    )


async def _handle_soft_delete_relationship(
    connection: DatabaseConnection, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle soft_delete_relationship tool call."""
    return await soft_delete_relationship(
        connection=connection,
        source_entity_id=args["source_entity_id"],
        target_entity_id=args["target_entity_id"],
        relationship_type=args["relationship_type"],
        group_id=args.get("group_id"),
    )


async def _handle_restore_entity(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle restore_entity tool call."""
    return await restore_entity(
        connection=connection,
        entity_id=args["entity_id"],
        group_id=args.get("group_id"),
    )


async def _handle_restore_relationship(
    connection: DatabaseConnection, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle restore_relationship tool call."""
    return await restore_relationship(
        connection=connection,
        source_entity_id=args["source_entity_id"],
        target_entity_id=args["target_entity_id"],
        relationship_type=args["relationship_type"],
        group_id=args.get("group_id"),
    )


async def _handle_hard_delete_entity(connection: DatabaseConnection, args: Dict[str, Any]) -> Dict[str, Any]:
    """Handle hard_delete_entity tool call."""
    return await delete_entity(
        connection=connection,
        entity_id=args["entity_id"],
        group_id=args.get("group_id"),
        hard=True,
    )


async def _handle_hard_delete_relationship(
    connection: DatabaseConnection, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle hard_delete_relationship tool call."""
    return await hard_delete_relationship(
        connection=connection,
        source_entity_id=args["source_entity_id"],
        target_entity_id=args["target_entity_id"],
        relationship_type=args["relationship_type"],
        group_id=args.get("group_id"),
    )


async def run_server():
    """Run the MCP server with stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="graffiti-graph-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main():
    """Main entry point for the MCP server (for use as entry point script)."""
    # Configure logging - use DEBUG level if LOG_LEVEL env var is set to DEBUG
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level, logging.INFO)
    
    logging.basicConfig(
        level=log_level,
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


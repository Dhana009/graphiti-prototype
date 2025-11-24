"""MCP Tool Schema Definitions for Graffiti Graph.

This module defines the MCP tool schemas for all Graffiti Graph operations.
These schemas are used by the MCP server to expose tools to AI assistants.
"""

from typing import Any, Dict, List, Optional
import mcp.types as types


def get_tool_schemas() -> List[types.Tool]:
    """Get all MCP tool schemas for Graffiti Graph operations.
    
    Returns:
        List[types.Tool]: List of all available MCP tools with their schemas
    """
    return [
        _get_add_entity_schema(),
        _get_add_relationship_schema(),
        _get_get_entity_by_id_schema(),
        _get_get_entities_by_type_schema(),
        _get_get_entity_relationships_schema(),
        _get_search_nodes_schema(),
        _get_add_memory_schema(),
        _get_update_memory_schema(),
        _get_soft_delete_entity_schema(),
        _get_soft_delete_relationship_schema(),
        _get_restore_entity_schema(),
        _get_restore_relationship_schema(),
        _get_hard_delete_entity_schema(),
        _get_hard_delete_relationship_schema(),
    ]


def _get_add_entity_schema() -> types.Tool:
    """Schema for add_entity tool."""
    return types.Tool(
        name="add_entity",
        description="Create a new entity in the knowledge graph",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Unique identifier for the entity (required)"
                },
                "entity_type": {
                    "type": "string",
                    "description": "Type of the entity (required)"
                },
                "name": {
                    "type": "string",
                    "description": "Human-readable name for the entity (required)"
                },
                "properties": {
                    "type": "object",
                    "description": "Optional key-value properties (flat only, max 50 properties)",
                    "additionalProperties": True
                },
                "summary": {
                    "type": "string",
                    "description": "Optional brief description of the entity"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                },
                "episode_uuid": {
                    "type": "string",
                    "description": "Optional UUID for tracking which episode created this entity"
                }
            },
            "required": ["entity_id", "entity_type", "name"]
        }
    )


def _get_add_relationship_schema() -> types.Tool:
    """Schema for add_relationship tool."""
    return types.Tool(
        name="add_relationship",
        description="Create a relationship between two entities in the knowledge graph",
        inputSchema={
            "type": "object",
            "properties": {
                "source_entity_id": {
                    "type": "string",
                    "description": "Source entity ID (required)"
                },
                "target_entity_id": {
                    "type": "string",
                    "description": "Target entity ID (required)"
                },
                "relationship_type": {
                    "type": "string",
                    "description": "Type of relationship (required)"
                },
                "properties": {
                    "type": "object",
                    "description": "Optional key-value properties for the relationship",
                    "additionalProperties": True
                },
                "fact": {
                    "type": "string",
                    "description": "Optional fact statement describing the relationship"
                },
                "t_valid": {
                    "type": "integer",
                    "description": "Optional timestamp when relationship becomes valid"
                },
                "t_invalid": {
                    "type": "integer",
                    "description": "Optional timestamp when relationship becomes invalid"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["source_entity_id", "target_entity_id", "relationship_type"]
        }
    )


def _get_get_entity_by_id_schema() -> types.Tool:
    """Schema for get_entity_by_id tool."""
    return types.Tool(
        name="get_entity_by_id",
        description="Retrieve an entity by its entity_id",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Unique identifier for the entity (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                },
                "include_deleted": {
                    "type": "boolean",
                    "description": "If true, include soft-deleted entities (default: false)"
                }
            },
            "required": ["entity_id"]
        }
    )


def _get_get_entities_by_type_schema() -> types.Tool:
    """Schema for get_entities_by_type tool."""
    return types.Tool(
        name="get_entities_by_type",
        description="Retrieve all entities of a specific type",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "description": "Type of entities to retrieve (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                },
                "limit": {
                    "type": "integer",
                    "description": "Optional maximum number of entities to return"
                },
                "offset": {
                    "type": "integer",
                    "description": "Optional offset for pagination"
                }
            },
            "required": ["entity_type"]
        }
    )


def _get_get_entity_relationships_schema() -> types.Tool:
    """Schema for get_entity_relationships tool."""
    return types.Tool(
        name="get_entity_relationships",
        description="Retrieve relationships for an entity (incoming, outgoing, or both)",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID to get relationships for (required)"
                },
                "direction": {
                    "type": "string",
                    "enum": ["incoming", "outgoing", "both"],
                    "description": "Relationship direction - 'incoming', 'outgoing', or 'both' (default: 'both')"
                },
                "relationship_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of relationship types to filter by"
                },
                "limit": {
                    "type": "integer",
                    "description": "Optional maximum number of relationships to return"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                },
                "include_deleted": {
                    "type": "boolean",
                    "description": "If true, include soft-deleted relationships (default: false)"
                }
            },
            "required": ["entity_id"]
        }
    )


def _get_search_nodes_schema() -> types.Tool:
    """Schema for search_nodes tool."""
    return types.Tool(
        name="search_nodes",
        description="Semantic search for entities in the knowledge graph",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text (required)"
                },
                "max_nodes": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 10, max: 100)"
                },
                "entity_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of entity types to filter by"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["query"]
        }
    )


def _get_add_memory_schema() -> types.Tool:
    """Schema for add_memory tool."""
    return types.Tool(
        name="add_memory",
        description="Add unstructured text and automatically extract entities/relationships using LLM",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Episode name/identifier (required)"
                },
                "episode_body": {
                    "type": "string",
                    "description": "Unstructured text content (required)"
                },
                "source": {
                    "type": "string",
                    "enum": ["text", "json", "message"],
                    "description": "Content type - 'text', 'json', or 'message' (default: 'text')"
                },
                "source_description": {
                    "type": "string",
                    "description": "Optional description of the source"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                },
                "uuid": {
                    "type": "string",
                    "description": "Optional UUID for deduplication"
                }
            },
            "required": ["name", "episode_body"]
        }
    )


def _get_update_memory_schema() -> types.Tool:
    """Schema for update_memory tool."""
    return types.Tool(
        name="update_memory",
        description="Update existing memory by comparing old vs new content and updating only changed entities/relationships",
        inputSchema={
            "type": "object",
            "properties": {
                "uuid": {
                    "type": "string",
                    "description": "UUID of the memory episode to update (required)"
                },
                "episode_body": {
                    "type": "string",
                    "description": "New unstructured text content (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                },
                "update_strategy": {
                    "type": "string",
                    "enum": ["incremental", "replace"],
                    "description": "Update strategy - 'incremental' (update only changed items) or 'replace' (soft-delete old and re-add) (default: 'incremental')"
                }
            },
            "required": ["uuid", "episode_body"]
        }
    )


def _get_soft_delete_entity_schema() -> types.Tool:
    """Schema for soft_delete_entity tool.
    
    Note: This maps to delete_entity() with hard=False.
    """
    return types.Tool(
        name="soft_delete_entity",
        description="Soft delete an entity (marks as deleted but doesn't remove from database). Maps to delete_entity with hard=False.",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Unique identifier for the entity (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["entity_id"]
        }
    )


def _get_soft_delete_relationship_schema() -> types.Tool:
    """Schema for soft_delete_relationship tool."""
    return types.Tool(
        name="soft_delete_relationship",
        description="Soft delete a relationship (marks as deleted but doesn't remove from database)",
        inputSchema={
            "type": "object",
            "properties": {
                "source_entity_id": {
                    "type": "string",
                    "description": "Source entity ID (required)"
                },
                "target_entity_id": {
                    "type": "string",
                    "description": "Target entity ID (required)"
                },
                "relationship_type": {
                    "type": "string",
                    "description": "Relationship type (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["source_entity_id", "target_entity_id", "relationship_type"]
        }
    )


def _get_restore_entity_schema() -> types.Tool:
    """Schema for restore_entity tool."""
    return types.Tool(
        name="restore_entity",
        description="Restore a soft-deleted entity",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Unique identifier for the entity (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["entity_id"]
        }
    )


def _get_restore_relationship_schema() -> types.Tool:
    """Schema for restore_relationship tool."""
    return types.Tool(
        name="restore_relationship",
        description="Restore a soft-deleted relationship",
        inputSchema={
            "type": "object",
            "properties": {
                "source_entity_id": {
                    "type": "string",
                    "description": "Source entity ID (required)"
                },
                "target_entity_id": {
                    "type": "string",
                    "description": "Target entity ID (required)"
                },
                "relationship_type": {
                    "type": "string",
                    "description": "Relationship type (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["source_entity_id", "target_entity_id", "relationship_type"]
        }
    )


def _get_hard_delete_entity_schema() -> types.Tool:
    """Schema for hard_delete_entity tool.
    
    Note: This maps to delete_entity() with hard=True.
    """
    return types.Tool(
        name="hard_delete_entity",
        description="Hard delete an entity (permanently removes from database, including all relationships). Maps to delete_entity with hard=True.",
        inputSchema={
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Unique identifier for the entity (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["entity_id"]
        }
    )


def _get_hard_delete_relationship_schema() -> types.Tool:
    """Schema for hard_delete_relationship tool."""
    return types.Tool(
        name="hard_delete_relationship",
        description="Hard delete a relationship (permanently removes from database)",
        inputSchema={
            "type": "object",
            "properties": {
                "source_entity_id": {
                    "type": "string",
                    "description": "Source entity ID (required)"
                },
                "target_entity_id": {
                    "type": "string",
                    "description": "Target entity ID (required)"
                },
                "relationship_type": {
                    "type": "string",
                    "description": "Relationship type (required)"
                },
                "group_id": {
                    "type": "string",
                    "description": "Optional group ID for multi-tenancy (defaults to 'main'). Reserved IDs: 'default', 'global', 'system', 'admin'"
                }
            },
            "required": ["source_entity_id", "target_entity_id", "relationship_type"]
        }
    )


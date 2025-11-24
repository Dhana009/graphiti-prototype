"""Graffiti Graph MCP Implementation.

This package provides the Graffiti Graph MCP server implementation
for storing and retrieving structured knowledge graphs.
"""

from .config import Neo4jConfig, get_neo4j_config
from .database import DatabaseConnection, initialize_database
from .validation import (
    validate_entity_id,
    validate_entity_type,
    validate_name,
    validate_properties,
    validate_group_id,
    validate_relationship_type,
    validate_relationship_input,
    MAX_PROPERTIES,
    MAX_KEY_LENGTH,
    MAX_VALUE_LENGTH,
)
from .search import search_nodes
from .entities import (
    add_entity,
    get_entity_by_id,
    get_entities_by_type,
    update_entity,
    delete_entity,
    EntityError,
    DuplicateEntityError,
    EntityNotFoundError,
)
from .relationships import (
    add_relationship,
    get_entity_relationships,
    validate_entities_exist,
    RelationshipError,
)
from .search import search_nodes
from .embeddings import generate_embedding, generate_entity_embedding, cosine_similarity
from .memory import add_memory, update_memory, _call_llm_for_extraction
from .mcp_tools import get_tool_schemas

__all__ = [
    'Neo4jConfig',
    'get_neo4j_config',
    'DatabaseConnection',
    'initialize_database',
    'validate_entity_id',
    'validate_entity_type',
    'validate_name',
    'validate_properties',
    'validate_group_id',
    'validate_relationship_type',
    'validate_relationship_input',
    'MAX_PROPERTIES',
    'MAX_KEY_LENGTH',
    'MAX_VALUE_LENGTH',
    'add_entity',
    'get_entity_by_id',
    'get_entities_by_type',
    'update_entity',
    'delete_entity',
    'EntityError',
    'DuplicateEntityError',
    'EntityNotFoundError',
    'add_relationship',
    'get_entity_relationships',
    'validate_entities_exist',
    'RelationshipError',
    'search_nodes',
    'generate_embedding',
    'generate_entity_embedding',
    'cosine_similarity',
    'add_memory',
    'update_memory',
    '_call_llm_for_extraction',
    'get_tool_schemas',
]

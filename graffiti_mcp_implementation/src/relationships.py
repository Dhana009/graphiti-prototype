"""Relationship operations for Graffiti Graph.

This module provides functions for creating and managing relationships
between entities in the knowledge graph.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from .database import DatabaseConnection
from .validation import (
    validate_relationship_input,
    validate_group_id,
    validate_entity_id,
)
from .entities import get_entity_by_id, EntityNotFoundError as EntityNotFoundErrorBase

logger = logging.getLogger(__name__)


class RelationshipError(Exception):
    """Base exception for relationship operations."""

    pass


# Alias for consistency with entity module
EntityNotFoundError = EntityNotFoundErrorBase


async def validate_entities_exist(
    connection: DatabaseConnection,
    source_entity_id: str,
    target_entity_id: str,
    group_id: Optional[str] = None,
) -> None:
    """Validate that both source and target entities exist.

    Args:
        connection: DatabaseConnection instance (must be connected)
        source_entity_id: Source entity ID to check
        target_entity_id: Target entity ID to check
        group_id: Optional group ID for multi-tenancy

    Raises:
        EntityNotFoundError: If source or target entity doesn't exist
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     await validate_entities_exist(
        ...         conn,
        ...         source_entity_id='user:1',
        ...         target_entity_id='module:1',
        ...         group_id='my_group'
        ...     )
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Check source entity
    try:
        await get_entity_by_id(connection, source_entity_id, group_id)
    except EntityNotFoundError:
        raise EntityNotFoundError(
            f"Source entity with ID '{source_entity_id}' not found in group '{group_id or 'main'}'"
        )

    # Check target entity
    try:
        await get_entity_by_id(connection, target_entity_id, group_id)
    except EntityNotFoundError:
        raise EntityNotFoundError(
            f"Target entity with ID '{target_entity_id}' not found in group '{group_id or 'main'}'"
        )


async def add_relationship(
    connection: DatabaseConnection,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    properties: Optional[Dict[str, Any]] = None,
    fact: Optional[str] = None,
    t_valid: Optional[datetime] = None,
    t_invalid: Optional[datetime] = None,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a relationship between two entities in the knowledge graph.

    Args:
        connection: DatabaseConnection instance (must be connected)
        source_entity_id: Source entity ID (required)
        target_entity_id: Target entity ID (required)
        relationship_type: Relationship type (required, e.g., 'USES', 'DEPENDS_ON')
        properties: Optional relationship properties (key-value pairs)
        fact: Optional human-readable description of the relationship
        t_valid: Optional datetime when relationship became valid (for temporal queries)
        t_invalid: Optional datetime when relationship was invalidated (for temporal queries)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')

    Returns:
        Dict[str, Any]: Relationship data including source_entity_id, target_entity_id,
                       relationship_type, properties, fact, group_id, created_at

    Raises:
        EntityNotFoundError: If source or target entity doesn't exist
        ValueError: If validation fails
        TypeError: If validation fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     relationship = await add_relationship(
        ...         conn,
        ...         source_entity_id='user:john_doe',
        ...         target_entity_id='module:auth',
        ...         relationship_type='USES',
        ...         properties={'since': '2024-01-01', 'permission': 'read'},
        ...         fact='John Doe uses Authentication Module for login',
        ...         group_id='my_group'
        ...     )
        >>> print(relationship['relationship_type'])
        'USES'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_source_id, validated_target_id, validated_type, validated_properties = validate_relationship_input(
        source_entity_id, target_entity_id, relationship_type, properties
    )
    validated_group_id = validate_group_id(group_id)

    # Validate that entities exist
    await validate_entities_exist(connection, validated_source_id, validated_target_id, validated_group_id)

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def create_relationship_tx(tx):
            # Build property SET clauses
            property_clauses = []
            params = {
                'source_id': validated_source_id,
                'target_id': validated_target_id,
                'group_id': validated_group_id,
                'relationship_type': validated_type,
            }

            # Add core relationship properties
            property_clauses.append('r.relationship_type = $relationship_type')
            property_clauses.append('r.group_id = $group_id')
            property_clauses.append('r.created_at = timestamp()')

            # Add optional properties
            if validated_properties:
                for key, value in validated_properties.items():
                    param_key = f'prop_{key}'
                    property_clauses.append(f'r.{key} = ${param_key}')
                    params[param_key] = value

            # Add optional fact
            if fact is not None:
                property_clauses.append('r.fact = $fact')
                params['fact'] = fact

            # Add optional temporal properties
            if t_valid is not None:
                property_clauses.append('r.t_valid = $t_valid')
                params['t_valid'] = t_valid.isoformat() if isinstance(t_valid, datetime) else t_valid

            if t_invalid is not None:
                property_clauses.append('r.t_invalid = $t_invalid')
                params['t_invalid'] = t_invalid.isoformat() if isinstance(t_invalid, datetime) else t_invalid

            # Use MERGE for idempotency (creates or updates existing relationship)
            # Note: Neo4j requires relationship types to be known at query time, so we construct
            # the query dynamically. We use the relationship_type as both a property and try to
            # match on it. For proper type-based queries, we'll use a generic RELATIONSHIP type
            # and store the actual type as a property (this is a common pattern for dynamic types).
            
            # Escape relationship type for use in query (basic safety check)
            # Relationship types should be simple strings, but we validate this in validation layer
            rel_type_escaped = validated_type.replace('`', '``')  # Escape backticks if any
            
            # Use a generic RELATIONSHIP type and store the actual type as a property
            # This allows us to query by type while maintaining flexibility
            query = f"""
            MATCH (s:Entity {{entity_id: $source_id, group_id: $group_id}})
            MATCH (t:Entity {{entity_id: $target_id, group_id: $group_id}})
            MERGE (s)-[r:RELATIONSHIP {{relationship_type: $relationship_type, group_id: $group_id}}]->(t)
            SET {', '.join(property_clauses)}
            RETURN r.relationship_type as relationship_type,
                   r.group_id as group_id,
                   r.created_at as created_at,
                   r.fact as fact,
                   r.t_valid as t_valid,
                   r.t_invalid as t_invalid,
                   r
            """

            result = await tx.run(query, **params)
            return await result.single()

        try:
            record = await session.execute_write(create_relationship_tx)

            if record is None:
                raise RelationshipError('Failed to create relationship')

            # Extract properties (excluding core fields)
            relationship_properties = {}
            rel = record['r']
            for k, v in rel.items():
                if k not in ['relationship_type', 'group_id', 'created_at', 'fact', 't_valid', 't_invalid']:
                    relationship_properties[k] = v

            relationship = {
                'source_entity_id': validated_source_id,
                'target_entity_id': validated_target_id,
                'relationship_type': record['relationship_type'],
                'group_id': record['group_id'],
                'created_at': record['created_at'],
                'properties': relationship_properties,
            }

            if record.get('fact') is not None:
                relationship['fact'] = record['fact']
            if record.get('t_valid') is not None:
                relationship['t_valid'] = record['t_valid']
            if record.get('t_invalid') is not None:
                relationship['t_invalid'] = record['t_invalid']

            logger.info(
                f"Created relationship: {validated_source_id} --[{validated_type}]--> {validated_target_id} (group: {validated_group_id})"
            )

            return relationship

        except EntityNotFoundError:
            # Re-raise EntityNotFoundError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to create relationship: {e}")
            raise RelationshipError(f"Failed to create relationship: {e}") from e


async def get_entity_relationships(
    connection: DatabaseConnection,
    entity_id: str,
    direction: str = 'both',
    relationship_types: Optional[list[str]] = None,
    limit: Optional[int] = None,
    group_id: Optional[str] = None,
    include_deleted: bool = False,
) -> list[Dict[str, Any]]:
    """Retrieve relationships for an entity (incoming, outgoing, or both).

    Args:
        connection: DatabaseConnection instance (must be connected)
        entity_id: Entity ID to get relationships for (required)
        direction: Relationship direction - 'incoming', 'outgoing', or 'both' (default: 'both')
        relationship_types: Optional list of relationship types to filter by
        limit: Optional maximum number of relationships to return
        group_id: Optional group ID for multi-tenancy (defaults to 'main')
        include_deleted: If True, include soft-deleted relationships (default: False)

    Returns:
        list[Dict[str, Any]]: List of relationship objects, each containing:
            - source_entity_id
            - target_entity_id
            - relationship_type
            - properties
            - fact (if present)
            - group_id
            - created_at
            - t_valid, t_invalid (if present)

    Raises:
        EntityNotFoundError: If entity with given entity_id and group_id is not found
        ValueError: If validation fails (invalid direction, limit, etc.)
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     # Get all relationships
        ...     relationships = await get_entity_relationships(
        ...         conn,
        ...         entity_id='user:john_doe',
        ...         direction='both',
        ...         group_id='my_group'
        ...     )
        ...     # Get only outgoing USES relationships
        ...     uses_only = await get_entity_relationships(
        ...         conn,
        ...         entity_id='user:john_doe',
        ...         direction='outgoing',
        ...         relationship_types=['USES'],
        ...         limit=10,
        ...         group_id='my_group'
        ...     )
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_entity_id = validate_entity_id(entity_id)
    validated_group_id = validate_group_id(group_id)

    # Validate direction
    if direction not in ['incoming', 'outgoing', 'both']:
        raise ValueError(f"direction must be 'incoming', 'outgoing', or 'both', got '{direction}'")

    # Validate limit
    if limit is not None:
        if not isinstance(limit, int):
            raise TypeError(f'limit must be an integer, got {type(limit)}')
        if limit < 1:
            raise ValueError(f'limit must be at least 1, got {limit}')
        if limit > 1000:
            raise ValueError(f'limit cannot exceed 1000, got {limit}')

    # Validate relationship_types
    if relationship_types is not None:
        if not isinstance(relationship_types, list):
            raise TypeError(f'relationship_types must be a list, got {type(relationship_types)}')
        if not relationship_types:
            raise ValueError('relationship_types cannot be an empty list')
        for rel_type in relationship_types:
            if not isinstance(rel_type, str) or not rel_type.strip():
                raise ValueError(f'relationship_types must contain non-empty strings, got {rel_type}')

    # First, verify entity exists
    try:
        await get_entity_by_id(connection, validated_entity_id, validated_group_id)
    except EntityNotFoundError:
        raise EntityNotFoundError(
            f"Entity with ID '{validated_entity_id}' not found in group '{validated_group_id}'"
        )

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def get_relationships_tx(tx):
            # Build WHERE clause for soft-deleted filtering
            deleted_filter = ""
            if not include_deleted:
                deleted_filter = " AND (r._deleted IS NULL OR r._deleted = false)"
            
            # Build query based on direction
            if direction == 'outgoing':
                # Entity is source
                query = """
                MATCH (e:Entity {entity_id: $entity_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {group_id: $group_id})
                WHERE r.group_id = $group_id
                """
                query += deleted_filter
                if relationship_types:
                    query += " AND r.relationship_type IN $relationship_types"
                query += """
                RETURN r.relationship_type as relationship_type,
                       r.group_id as group_id,
                       r.created_at as created_at,
                       r.fact as fact,
                       r.t_valid as t_valid,
                       r.t_invalid as t_invalid,
                       r._deleted as _deleted,
                       r.deleted_at as deleted_at,
                       startNode(r).entity_id as source_entity_id,
                       endNode(r).entity_id as target_entity_id,
                       r
                ORDER BY r.created_at
                """
            elif direction == 'incoming':
                # Entity is target
                query = """
                MATCH (source:Entity {group_id: $group_id})-[r:RELATIONSHIP]->(e:Entity {entity_id: $entity_id, group_id: $group_id})
                WHERE r.group_id = $group_id
                """
                query += deleted_filter
                if relationship_types:
                    query += " AND r.relationship_type IN $relationship_types"
                query += """
                RETURN r.relationship_type as relationship_type,
                       r.group_id as group_id,
                       r.created_at as created_at,
                       r.fact as fact,
                       r.t_valid as t_valid,
                       r.t_invalid as t_invalid,
                       r._deleted as _deleted,
                       r.deleted_at as deleted_at,
                       startNode(r).entity_id as source_entity_id,
                       endNode(r).entity_id as target_entity_id,
                       r
                ORDER BY r.created_at
                """
            else:  # both
                query = """
                MATCH (e:Entity {entity_id: $entity_id, group_id: $group_id})
                OPTIONAL MATCH (e)-[r_out:RELATIONSHIP]->(target:Entity {group_id: $group_id})
                OPTIONAL MATCH (source:Entity {group_id: $group_id})-[r_in:RELATIONSHIP]->(e)
                WITH e, collect(DISTINCT r_out) as outgoing, collect(DISTINCT r_in) as incoming
                UNWIND (outgoing + incoming) as r
                WITH r
                WHERE r IS NOT NULL AND r.group_id = $group_id
                """
                query += deleted_filter
                if relationship_types:
                    query += " AND r.relationship_type IN $relationship_types"
                query += """
                RETURN r.relationship_type as relationship_type,
                       r.group_id as group_id,
                       r.created_at as created_at,
                       r.fact as fact,
                       r.t_valid as t_valid,
                       r.t_invalid as t_invalid,
                       r._deleted as _deleted,
                       r.deleted_at as deleted_at,
                       startNode(r).entity_id as source_entity_id,
                       endNode(r).entity_id as target_entity_id,
                       r
                ORDER BY r.created_at
                """

            if limit:
                query += f" LIMIT {limit}"

            params = {
                'entity_id': validated_entity_id,
                'group_id': validated_group_id,
            }
            if relationship_types:
                params['relationship_types'] = relationship_types

            result = await tx.run(query, **params)
            return [record async for record in result]

        records = await session.execute_read(get_relationships_tx)

        relationships = []
        for record in records:
            # Extract properties (excluding core fields)
            rel_properties = {}
            rel = record['r']
            for k, v in rel.items():
                if k not in ['relationship_type', 'group_id', 'created_at', 'fact', 't_valid', 't_invalid', '_deleted', 'deleted_at']:
                    rel_properties[k] = v

            relationship = {
                'source_entity_id': record['source_entity_id'],
                'target_entity_id': record['target_entity_id'],
                'relationship_type': record['relationship_type'],
                'group_id': record['group_id'],
                'created_at': record['created_at'],
                'properties': rel_properties,
            }

            if record.get('fact') is not None:
                relationship['fact'] = record['fact']
            if record.get('t_valid') is not None:
                relationship['t_valid'] = record['t_valid']
            if record.get('t_invalid') is not None:
                relationship['t_invalid'] = record['t_invalid']
            
            # Include deleted fields if include_deleted is True
            if include_deleted:
                relationship['_deleted'] = record.get('_deleted')
                relationship['deleted_at'] = record.get('deleted_at')

            relationships.append(relationship)

        logger.info(
            f"Retrieved {len(relationships)} relationships for entity {validated_entity_id} "
            f"(direction: {direction}, group: {validated_group_id})"
        )

        return relationships


async def soft_delete_relationship(
    connection: DatabaseConnection,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Soft delete a relationship (marks as deleted but doesn't remove from database).

    Args:
        connection: DatabaseConnection instance (must be connected)
        source_entity_id: Source entity ID (required)
        target_entity_id: Target entity ID (required)
        relationship_type: Relationship type (required)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')

    Returns:
        Dict[str, Any]: Deletion result with status, relationship info, and deleted_at timestamp

    Raises:
        RelationshipError: If deletion fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     result = await soft_delete_relationship(
        ...         conn,
        ...         source_entity_id='user:john',
        ...         target_entity_id='user:jane',
        ...         relationship_type='KNOWS',
        ...         group_id='my_group'
        ...     )
        >>> print(result['status'])
        'deleted'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_source_id, validated_target_id, validated_type, _ = validate_relationship_input(
        source_entity_id, target_entity_id, relationship_type, None
    )
    validated_group_id = validate_group_id(group_id)

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def soft_delete_tx(tx):
            # Check if relationship exists and if already deleted
            check_result = await tx.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                RETURN r._deleted as _deleted, r.deleted_at as deleted_at
                """,
                source_id=validated_source_id,
                target_id=validated_target_id,
                rel_type=validated_type,
                group_id=validated_group_id,
            )
            check_record = await check_result.single()

            if check_record is None:
                # Relationship doesn't exist - idempotent behavior: return success
                logger.warning(
                    f"Relationship {validated_source_id} --[{validated_type}]--> {validated_target_id} "
                    f"not found in group {validated_group_id}, but deletion is idempotent, so returning success"
                )
                return None

            # Check if already deleted (idempotent)
            is_already_deleted = check_record.get('_deleted') is True
            existing_deleted_at = check_record.get('deleted_at')

            if is_already_deleted:
                # Already deleted - return existing record (idempotent)
                return {
                    '_deleted': True,
                    'deleted_at': existing_deleted_at,
                }

            # Soft delete: mark as deleted (first time)
            result = await tx.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                SET r._deleted = true,
                    r.deleted_at = timestamp()
                RETURN r._deleted as _deleted, r.deleted_at as deleted_at
                """,
                source_id=validated_source_id,
                target_id=validated_target_id,
                rel_type=validated_type,
                group_id=validated_group_id,
            )
            return await result.single()

        try:
            record = await session.execute_write(soft_delete_tx)

            if record is None:
                # Relationship didn't exist, but deletion is idempotent
                return {
                    'status': 'deleted',
                    'source_entity_id': validated_source_id,
                    'target_entity_id': validated_target_id,
                    'relationship_type': validated_type,
                    'hard_delete': False,
                    'already_deleted': True,
                }

            logger.info(
                f"Soft deleted relationship: {validated_source_id} --[{validated_type}]--> {validated_target_id} (group: {validated_group_id})"
            )
            return {
                'status': 'deleted',
                'source_entity_id': validated_source_id,
                'target_entity_id': validated_target_id,
                'relationship_type': validated_type,
                'hard_delete': False,
                'deleted_at': record['deleted_at'],
            }
        except Exception as e:
            logger.error(f"Failed to soft delete relationship: {e}")
            raise RelationshipError(f"Failed to delete relationship: {e}") from e


async def restore_relationship(
    connection: DatabaseConnection,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Restore a soft-deleted relationship.

    Args:
        connection: DatabaseConnection instance (must be connected)
        source_entity_id: Source entity ID (required)
        target_entity_id: Target entity ID (required)
        relationship_type: Relationship type (required)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')

    Returns:
        Dict[str, Any]: Restoration result with status and relationship info

    Raises:
        RelationshipError: If restoration fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     result = await restore_relationship(
        ...         conn,
        ...         source_entity_id='user:john',
        ...         target_entity_id='user:jane',
        ...         relationship_type='KNOWS',
        ...         group_id='my_group'
        ...     )
        >>> print(result['status'])
        'restored'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_source_id, validated_target_id, validated_type, _ = validate_relationship_input(
        source_entity_id, target_entity_id, relationship_type, None
    )
    validated_group_id = validate_group_id(group_id)

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def restore_tx(tx):
            # Check if relationship exists
            check_result = await tx.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                RETURN r._deleted as _deleted
                """,
                source_id=validated_source_id,
                target_id=validated_target_id,
                rel_type=validated_type,
                group_id=validated_group_id,
            )
            check_record = await check_result.single()

            if check_record is None:
                raise RelationshipError(
                    f"Relationship {validated_source_id} --[{validated_type}]--> {validated_target_id} "
                    f"not found in group {validated_group_id}"
                )

            # Restore: clear deleted flag
            result = await tx.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                SET r._deleted = false,
                    r.deleted_at = null
                RETURN r._deleted as _deleted
                """,
                source_id=validated_source_id,
                target_id=validated_target_id,
                rel_type=validated_type,
                group_id=validated_group_id,
            )
            return await result.single()

        try:
            record = await session.execute_write(restore_tx)

            if record is None:
                raise RelationshipError("Failed to restore relationship")

            logger.info(
                f"Restored relationship: {validated_source_id} --[{validated_type}]--> {validated_target_id} (group: {validated_group_id})"
            )
            return {
                'status': 'restored',
                'source_entity_id': validated_source_id,
                'target_entity_id': validated_target_id,
                'relationship_type': validated_type,
            }
        except RelationshipError:
            raise
        except Exception as e:
            logger.error(f"Failed to restore relationship: {e}")
            raise RelationshipError(f"Failed to restore relationship: {e}") from e


async def hard_delete_relationship(
    connection: DatabaseConnection,
    source_entity_id: str,
    target_entity_id: str,
    relationship_type: str,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Hard delete a relationship (permanently removes from database).

    Args:
        connection: DatabaseConnection instance (must be connected)
        source_entity_id: Source entity ID (required)
        target_entity_id: Target entity ID (required)
        relationship_type: Relationship type (required)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')

    Returns:
        Dict[str, Any]: Deletion result with status, relationship info, and hard_delete flag

    Raises:
        RelationshipError: If deletion fails or relationship doesn't exist
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     result = await hard_delete_relationship(
        ...         conn,
        ...         source_entity_id='user:john',
        ...         target_entity_id='user:jane',
        ...         relationship_type='KNOWS',
        ...         group_id='my_group'
        ...     )
        >>> print(result['status'])
        'deleted'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_source_id, validated_target_id, validated_type, _ = validate_relationship_input(
        source_entity_id, target_entity_id, relationship_type, None
    )
    validated_group_id = validate_group_id(group_id)

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def hard_delete_tx(tx):
            # First check if relationship exists
            check_result = await tx.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                RETURN r
                """,
                source_id=validated_source_id,
                target_id=validated_target_id,
                rel_type=validated_type,
                group_id=validated_group_id,
            )
            check_record = await check_result.single()

            if check_record is None:
                raise RelationshipError(
                    f"Relationship {validated_source_id} --[{validated_type}]--> {validated_target_id} "
                    f"not found in group {validated_group_id}"
                )

            # Permanently delete relationship (not the nodes)
            delete_result = await tx.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                DELETE r
                RETURN count(r) as deleted_count
                """,
                source_id=validated_source_id,
                target_id=validated_target_id,
                rel_type=validated_type,
                group_id=validated_group_id,
            )
            return await delete_result.single()

        try:
            record = await session.execute_write(hard_delete_tx)
            logger.info(
                f"Hard deleted relationship: {validated_source_id} --[{validated_type}]--> {validated_target_id} (group: {validated_group_id})"
            )
            return {
                'status': 'deleted',
                'source_entity_id': validated_source_id,
                'target_entity_id': validated_target_id,
                'relationship_type': validated_type,
                'hard_delete': True,
            }
        except RelationshipError:
            raise
        except Exception as e:
            logger.error(f"Failed to hard delete relationship: {e}")
            raise RelationshipError(f"Failed to delete relationship: {e}") from e

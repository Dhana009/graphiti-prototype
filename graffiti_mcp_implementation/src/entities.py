"""Entity operations for Graffiti Graph.

This module provides functions for creating and managing entities
in the knowledge graph.
"""

import logging
from typing import Dict, Any, Optional, Union
from neo4j.exceptions import ConstraintError

from .database import DatabaseConnection
from .validation import (
    validate_entity_id,
    validate_entity_type,
    validate_name,
    validate_properties,
    validate_group_id,
)

logger = logging.getLogger(__name__)

# Sentinel value to distinguish "not provided" from "explicitly None"
_NOT_PROVIDED = object()


class EntityError(Exception):
    """Base exception for entity operations."""

    pass


class DuplicateEntityError(EntityError):
    """Raised when attempting to create a duplicate entity."""

    pass


class EntityNotFoundError(EntityError):
    """Raised when an entity is not found."""

    pass


async def add_entity(
    connection: DatabaseConnection,
    entity_id: str,
    entity_type: str,
    name: str,
    properties: Optional[Dict[str, Any]] = None,
    summary: Optional[str] = None,
    group_id: Optional[str] = None,
    episode_uuid: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new entity in the knowledge graph.

    Args:
        connection: DatabaseConnection instance (must be connected)
        entity_id: Unique identifier for the entity (required)
        entity_type: Type of the entity (required)
        name: Human-readable name for the entity (required)
        properties: Optional key-value properties (flat only)
        summary: Optional brief description
        group_id: Optional group ID for multi-tenancy (defaults to 'main')

    Returns:
        Dict[str, Any]: Created entity data including entity_id, entity_type, name, etc.

    Raises:
        DuplicateEntityError: If entity with same (group_id, entity_id) already exists
        ValueError: If validation fails
        TypeError: If validation fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     entity = await add_entity(
        ...         conn,
        ...         entity_id='user:john_doe',
        ...         entity_type='User',
        ...         name='John Doe',
        ...         properties={'email': 'john@example.com'},
        ...         group_id='my_group'
        ...     )
        >>> print(entity['entity_id'])
        'user:john_doe'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_entity_id = validate_entity_id(entity_id)
    validated_entity_type = validate_entity_type(entity_type)
    validated_name = validate_name(name)
    validated_properties = validate_properties(properties)
    validated_group_id = validate_group_id(group_id)

    # Sanitize entity_type for use as Neo4j label (remove special characters)
    # Neo4j labels can contain letters, numbers, and underscores
    label_safe_type = ''.join(
        c if c.isalnum() or c == '_' else '_' for c in validated_entity_type
    )

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def create_entity_tx(tx):
            # Build properties dictionary for CREATE
            # Start with core properties
            entity_props = {
                'entity_id': validated_entity_id,
                'entity_type': validated_entity_type,
                'name': validated_name,
                'group_id': validated_group_id,
            }

            # Add optional summary
            if summary is not None:
                entity_props['summary'] = summary

            # Add optional episode_uuid (for tracking which episode created this entity)
            if episode_uuid is not None:
                entity_props['episode_uuid'] = episode_uuid

            # Merge validated properties into entity properties
            entity_props.update(validated_properties)

            # Create entity with both Entity label and entity_type label
            # Use CREATE (not MERGE) to enforce uniqueness via constraint
            query = f"""
            CREATE (e:Entity:{label_safe_type} $props)
            RETURN e.entity_id as entity_id,
                   e.entity_type as entity_type,
                   e.name as name,
                   e.group_id as group_id,
                   e.summary as summary,
                   e
            """

            result = await tx.run(query, props=entity_props)
            record = await result.single()

            if record is None:
                raise EntityError('Failed to create entity')

            # Extract properties (excluding core fields)
            # Note: Neo4j doesn't store null values, so properties with None won't appear
            entity_properties = {}
            for k, v in record['e'].items():
                if k not in ['entity_id', 'entity_type', 'name', 'group_id', 'summary']:
                    entity_properties[k] = v

            # Include None values from validated_properties that weren't stored
            for k, v in validated_properties.items():
                if v is None and k not in entity_properties:
                    entity_properties[k] = None

            return {
                'entity_id': record['entity_id'],
                'entity_type': record['entity_type'],
                'name': record['name'],
                'group_id': record['group_id'],
                'summary': record.get('summary'),
                'properties': entity_properties,
            }

        try:
            # Create the entity (constraint will prevent duplicates)
            entity = await session.execute_write(create_entity_tx)

            # Generate and store embedding for semantic search
            try:
                from .embeddings import generate_entity_embedding
                embedding = generate_entity_embedding(validated_name, summary)
                
                # Store embedding on the entity
                async def store_embedding_tx(tx):
                    await tx.run(
                        """
                        MATCH (e:Entity {entity_id: $entity_id, group_id: $group_id})
                        SET e.embedding = $embedding
                        """,
                        entity_id=validated_entity_id,
                        group_id=validated_group_id,
                        embedding=embedding,
                    )
                
                await session.execute_write(store_embedding_tx)
                logger.debug(f"Generated and stored embedding for entity: {validated_entity_id}")
            except Exception as e:
                # Log but don't fail entity creation if embedding generation fails
                logger.warning(f"Failed to generate embedding for entity {validated_entity_id}: {e}")

            logger.info(
                f"Created entity: {validated_entity_id} (type: {validated_entity_type}, group: {validated_group_id})"
            )

            return entity

        except ConstraintError as e:
            # Constraint violation means duplicate
            logger.warning(
                f"Constraint violation creating entity {validated_entity_id}: {e}"
            )
            raise DuplicateEntityError(
                f"Entity with ID '{validated_entity_id}' already exists in group '{validated_group_id}'"
            ) from e


async def get_entity_by_id(
    connection: DatabaseConnection,
    entity_id: str,
    group_id: Optional[str] = None,
    include_deleted: bool = False,
) -> Dict[str, Any]:
    """Retrieve an entity by its entity_id.

    Args:
        connection: DatabaseConnection instance (must be connected)
        entity_id: Unique identifier for the entity (required)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')
        include_deleted: If True, include soft-deleted entities (default: False)

    Returns:
        Dict[str, Any]: Entity data including entity_id, entity_type, name, properties, etc.
        If include_deleted=True and entity is deleted, includes _deleted and deleted_at fields.

    Raises:
        EntityNotFoundError: If entity with given entity_id and group_id is not found
        ValueError: If validation fails
        TypeError: If validation fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     entity = await get_entity_by_id(
        ...         conn,
        ...         entity_id='user:john_doe',
        ...         group_id='my_group'
        ...     )
        >>> print(entity['name'])
        'John Doe'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_entity_id = validate_entity_id(entity_id)
    validated_group_id = validate_group_id(group_id)

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def get_entity_tx(tx):
            # Build WHERE clause based on include_deleted flag
            where_clause = ""
            if not include_deleted:
                where_clause = "WHERE e._deleted IS NULL OR e._deleted = false"
            
            query = f"""
                MATCH (e:Entity {{
                    entity_id: $entity_id,
                    group_id: $group_id
                }})
                {where_clause}
                RETURN e.entity_id as entity_id,
                       e.entity_type as entity_type,
                       e.name as name,
                       e.group_id as group_id,
                       e.summary as summary,
                       e._deleted as _deleted,
                       e.deleted_at as deleted_at,
                       e
                """
            result = await tx.run(
                query,
                entity_id=validated_entity_id,
                group_id=validated_group_id,
            )
            return await result.single()

        record = await session.execute_read(get_entity_tx)

        if record is None:
            raise EntityNotFoundError(
                f"Entity with ID '{validated_entity_id}' not found in group '{validated_group_id}'"
            )

        # Extract properties (excluding core fields)
        entity_properties = {}
        entity = record['e']
        for k, v in entity.items():
            if k not in ['entity_id', 'entity_type', 'name', 'group_id', 'summary', '_deleted', 'deleted_at']:
                entity_properties[k] = v

        result = {
            'entity_id': record['entity_id'],
            'entity_type': record['entity_type'],
            'name': record['name'],
            'group_id': record['group_id'],
            'summary': record.get('summary'),
            'properties': entity_properties,
        }
        
        # Include deleted fields if include_deleted is True
        if include_deleted:
            result['_deleted'] = record.get('_deleted')
            result['deleted_at'] = record.get('deleted_at')
        
        return result


async def get_entities_by_type(
    connection: DatabaseConnection,
    entity_type: str,
    group_id: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[Dict[str, Any]]:
    """Retrieve all entities of a specific type.

    Args:
        connection: DatabaseConnection instance (must be connected)
        entity_type: Type of entities to retrieve (required)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')
        limit: Optional maximum number of results to return (default: 50, max: 1000)

    Returns:
        list[Dict[str, Any]]: List of entity objects, empty list if none found

    Raises:
        ValueError: If validation fails or limit exceeds maximum
        TypeError: If validation fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     entities = await get_entities_by_type(
        ...         conn,
        ...         entity_type='User',
        ...         group_id='my_group',
        ...         limit=10
        ...     )
        >>> print(len(entities))
        10
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validation constants
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 1000

    # Validate inputs
    validated_entity_type = validate_entity_type(entity_type)
    validated_group_id = validate_group_id(group_id)

    # Validate and set limit
    if limit is None:
        limit = DEFAULT_LIMIT
    elif limit > MAX_LIMIT:
        raise ValueError(f'Limit cannot exceed {MAX_LIMIT}, got {limit}')
    elif limit < 1:
        raise ValueError(f'Limit must be at least 1, got {limit}')

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def get_entities_tx(tx):
            result = await tx.run(
                """
                MATCH (e:Entity {
                    entity_type: $entity_type,
                    group_id: $group_id
                })
                WHERE e._deleted IS NULL OR e._deleted = false
                RETURN e.entity_id as entity_id,
                       e.entity_type as entity_type,
                       e.name as name,
                       e.group_id as group_id,
                       e.summary as summary,
                       e
                ORDER BY e.entity_id
                LIMIT $limit
                """,
                entity_type=validated_entity_type,
                group_id=validated_group_id,
                limit=limit,
            )
            return [record async for record in result]

        records = await session.execute_read(get_entities_tx)

        entities = []
        for record in records:
            # Extract properties (excluding core fields)
            entity_properties = {}
            entity = record['e']
            for k, v in entity.items():
                if k not in ['entity_id', 'entity_type', 'name', 'group_id', 'summary']:
                    entity_properties[k] = v

            entities.append({
                'entity_id': record['entity_id'],
                'entity_type': record['entity_type'],
                'name': record['name'],
                'group_id': record['group_id'],
                'summary': record.get('summary'),
                'properties': entity_properties,
            })

        return entities


async def update_entity(
    connection: DatabaseConnection,
    entity_id: str,
    name: Union[str, type(_NOT_PROVIDED)] = _NOT_PROVIDED,
    properties: Union[Dict[str, Any], type(_NOT_PROVIDED)] = _NOT_PROVIDED,
    summary: Union[str, None, type(_NOT_PROVIDED)] = _NOT_PROVIDED,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update an existing entity in the knowledge graph.

    Args:
        connection: DatabaseConnection instance (must be connected)
        entity_id: Unique identifier for the entity (required)
        name: Optional new name for the entity
        properties: Optional new properties (replaces all properties if provided)
        summary: Optional new summary (None to remove summary)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')

    Returns:
        Dict[str, Any]: Updated entity data including entity_id, entity_type, name, etc.

    Raises:
        EntityNotFoundError: If entity with given entity_id and group_id is not found
        ValueError: If validation fails
        TypeError: If validation fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     entity = await update_entity(
        ...         conn,
        ...         entity_id='user:john_doe',
        ...         name='John Updated',
        ...         properties={'email': 'new@example.com'},
        ...         group_id='my_group'
        ...     )
        >>> print(entity['name'])
        'John Updated'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_entity_id = validate_entity_id(entity_id)
    validated_group_id = validate_group_id(group_id)

    # Validate optional fields if provided
    validated_name = validate_name(name) if name is not _NOT_PROVIDED and name is not None else None
    validated_properties = validate_properties(properties) if properties is not _NOT_PROVIDED and properties is not None else None

    # Validate summary (if provided, must be string; None is allowed to remove)
    if summary is not _NOT_PROVIDED and summary is not None and not isinstance(summary, str):
        raise TypeError(f'summary must be a string or None, got {type(summary)}')
    validated_summary = summary if summary is not _NOT_PROVIDED else None

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def update_entity_tx(tx):
            # First, check if entity exists
            check_result = await tx.run(
                """
                MATCH (e:Entity {
                    entity_id: $entity_id,
                    group_id: $group_id
                })
                RETURN e { .*, labels: labels(e) } AS entity
                """,
                entity_id=validated_entity_id,
                group_id=validated_group_id,
            )
            check_record = await check_result.single()

            if check_record is None:
                raise EntityNotFoundError(
                    f"Entity with ID '{validated_entity_id}' not found in group '{validated_group_id}'"
                )

            existing_entity = check_record['entity']

            # Build SET clause dynamically based on what's being updated
            set_clauses = []
            params = {
                'entity_id': validated_entity_id,
                'group_id': validated_group_id,
            }

            # Update name if provided
            if name is not _NOT_PROVIDED and validated_name is not None:
                set_clauses.append('e.name = $name')
                params['name'] = validated_name

            # Update summary if explicitly provided (including None to remove)
            if summary is not _NOT_PROVIDED:
                if summary is None:
                    # Remove summary by setting to null (explicitly provided None)
                    set_clauses.append('e.summary = null')
                else:
                    # Update summary
                    set_clauses.append('e.summary = $summary')
                    params['summary'] = summary

            # Update properties if provided
            if properties is not _NOT_PROVIDED and validated_properties is not None:
                # Remove all existing properties (except core fields) and set new ones
                # We'll use a different approach: remove all non-core properties, then add new ones
                # First, get all property keys to remove
                core_fields = {'entity_id', 'entity_type', 'name', 'group_id', 'summary'}
                existing_props = {k: v for k, v in existing_entity.items() if k not in core_fields}

                # Remove existing properties
                for prop_key in existing_props.keys():
                    set_clauses.append(f'e.{prop_key} = null')

                # Add new properties
                for prop_key, prop_value in validated_properties.items():
                    if prop_value is None:
                        # Skip null values (Neo4j doesn't store them)
                        continue
                    set_clauses.append(f'e.{prop_key} = $prop_{prop_key}')
                    params[f'prop_{prop_key}'] = prop_value

            # Always update updated_at timestamp
            set_clauses.append('e.updated_at = timestamp()')

            if not set_clauses:
                # Nothing to update, return existing entity
                return existing_entity

            # Build and execute update query
            query = f"""
            MATCH (e:Entity {{
                entity_id: $entity_id,
                group_id: $group_id
            }})
            SET {', '.join(set_clauses)}
            RETURN e.entity_id as entity_id,
                   e.entity_type as entity_type,
                   e.name as name,
                   e.group_id as group_id,
                   e.summary as summary,
                   e
            """

            result = await tx.run(query, params)
            record = await result.single()

            if record is None:
                raise EntityError('Failed to update entity')

            # Extract properties (excluding core fields)
            entity_properties = {}
            entity = record['e']
            for k, v in entity.items():
                if k not in ['entity_id', 'entity_type', 'name', 'group_id', 'summary', 'updated_at']:
                    entity_properties[k] = v

            return {
                'entity_id': record['entity_id'],
                'entity_type': record['entity_type'],
                'name': record['name'],
                'group_id': record['group_id'],
                'summary': record.get('summary'),
                'properties': entity_properties,
            }

        # Get existing entity first to compare values
        async def get_existing_entity_tx(tx):
            result = await tx.run(
                """
                MATCH (e:Entity {entity_id: $entity_id, group_id: $group_id})
                RETURN e.name as name, e.summary as summary
                """,
                entity_id=validated_entity_id,
                group_id=validated_group_id,
            )
            return await result.single()
        
        existing_entity_check = await session.execute_read(get_existing_entity_tx)
        existing_name = existing_entity_check['name'] if existing_entity_check else None
        existing_summary = existing_entity_check.get('summary') if existing_entity_check else None
        
        try:
            updated_entity = await session.execute_write(update_entity_tx)

            # Regenerate embedding only if name or summary actually changed
            name_actually_changed = (name is not _NOT_PROVIDED and 
                                   validated_name is not None and 
                                   validated_name != existing_name)
            summary_actually_changed = (summary is not _NOT_PROVIDED and 
                                      validated_summary != existing_summary)
            
            if name_actually_changed or summary_actually_changed:
                try:
                    from .embeddings import generate_entity_embedding
                    # Get current name and summary for embedding
                    current_name = validated_name if name_actually_changed else updated_entity['name']
                    current_summary = validated_summary if summary_actually_changed else updated_entity.get('summary')
                    embedding = generate_entity_embedding(current_name, current_summary)
                    
                    # Store updated embedding
                    async def update_embedding_tx(tx):
                        await tx.run(
                            """
                            MATCH (e:Entity {entity_id: $entity_id, group_id: $group_id})
                            SET e.embedding = $embedding
                            """,
                            entity_id=validated_entity_id,
                            group_id=validated_group_id,
                            embedding=embedding,
                        )
                    
                    await session.execute_write(update_embedding_tx)
                    logger.debug(f"Regenerated embedding for updated entity: {validated_entity_id}")
                except Exception as e:
                    # Log but don't fail update if embedding generation fails
                    logger.warning(f"Failed to regenerate embedding for entity {validated_entity_id}: {e}")

            logger.info(
                f"Updated entity: {validated_entity_id} (group: {validated_group_id})"
            )

            return updated_entity

        except EntityNotFoundError:
            # Re-raise EntityNotFoundError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to update entity {validated_entity_id}: {e}")
            raise EntityError(f"Failed to update entity: {e}") from e


async def delete_entity(
    connection: DatabaseConnection,
    entity_id: str,
    group_id: Optional[str] = None,
    hard: bool = False,
) -> Dict[str, Any]:
    """Delete an entity from the knowledge graph.

    Args:
        connection: DatabaseConnection instance (must be connected)
        entity_id: Unique identifier for the entity (required)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')
        hard: If True, permanently delete entity (hard delete). If False, soft delete (default).

    Returns:
        Dict[str, Any]: Deletion result with status and entity_id

    Raises:
        EntityNotFoundError: If entity with given entity_id and group_id is not found (only for hard delete)
        ValueError: If validation fails
        TypeError: If validation fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     result = await delete_entity(
        ...         conn,
        ...         entity_id='user:john_doe',
        ...         group_id='my_group',
        ...         hard=False  # Soft delete (default)
        ...     )
        >>> print(result['status'])
        'deleted'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_entity_id = validate_entity_id(entity_id)
    validated_group_id = validate_group_id(group_id)

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        if hard:
            # Hard delete: permanently remove entity and all relationships
            async def hard_delete_tx(tx):
                # First check if entity exists
                check_result = await tx.run(
                    """
                    MATCH (e:Entity {
                        entity_id: $entity_id,
                        group_id: $group_id
                    })
                    RETURN e.entity_id as entity_id
                    """,
                    entity_id=validated_entity_id,
                    group_id=validated_group_id,
                )
                check_record = await check_result.single()

                if check_record is None:
                    raise EntityNotFoundError(
                        f"Entity with ID '{validated_entity_id}' not found in group '{validated_group_id}'"
                    )

                # Permanently delete entity and all relationships
                delete_result = await tx.run(
                    """
                    MATCH (e:Entity {
                        entity_id: $entity_id,
                        group_id: $group_id
                    })
                    DETACH DELETE e
                    RETURN count(e) as deleted_count
                    """,
                    entity_id=validated_entity_id,
                    group_id=validated_group_id,
                )
                return await delete_result.single()

            try:
                record = await session.execute_write(hard_delete_tx)
                logger.info(
                    f"Hard deleted entity: {validated_entity_id} (group: {validated_group_id})"
                )
                return {
                    'status': 'deleted',
                    'entity_id': validated_entity_id,
                    'hard_delete': True,
                }
            except EntityNotFoundError:
                raise
            except Exception as e:
                logger.error(f"Failed to hard delete entity {validated_entity_id}: {e}")
                raise EntityError(f"Failed to delete entity: {e}") from e

        else:
            # Soft delete: mark entity as deleted
            async def soft_delete_tx(tx):
                # Check if entity exists and if already deleted
                check_result = await tx.run(
                    """
                    MATCH (e:Entity {
                        entity_id: $entity_id,
                        group_id: $group_id
                    })
                    RETURN e.entity_id as entity_id, 
                           e._deleted as _deleted,
                           e.deleted_at as deleted_at
                    """,
                    entity_id=validated_entity_id,
                    group_id=validated_group_id,
                )
                check_record = await check_result.single()

                if check_record is None:
                    # Entity doesn't exist - idempotent behavior: return success
                    logger.warning(
                        f"Entity {validated_entity_id} not found in group {validated_group_id}, "
                        "but deletion is idempotent, so returning success"
                    )
                    return None

                # Check if already deleted (idempotent)
                is_already_deleted = check_record.get('_deleted') is True
                existing_deleted_at = check_record.get('deleted_at')

                if is_already_deleted:
                    # Already deleted - return existing record (idempotent)
                    return {
                        'entity_id': check_record['entity_id'],
                        '_deleted': True,
                        'deleted_at': existing_deleted_at,
                    }

                # Soft delete: mark as deleted (first time)
                result = await tx.run(
                    """
                    MATCH (e:Entity {
                        entity_id: $entity_id,
                        group_id: $group_id
                    })
                    SET e._deleted = true,
                        e.deleted_at = timestamp()
                    RETURN e.entity_id as entity_id,
                           e._deleted as _deleted,
                           e.deleted_at as deleted_at
                    """,
                    entity_id=validated_entity_id,
                    group_id=validated_group_id,
                )
                return await result.single()

            try:
                record = await session.execute_write(soft_delete_tx)

                if record is None:
                    # Entity didn't exist, but deletion is idempotent
                    return {
                        'status': 'deleted',
                        'entity_id': validated_entity_id,
                        'hard_delete': False,
                        'already_deleted': True,
                    }

                logger.info(
                    f"Soft deleted entity: {validated_entity_id} (group: {validated_group_id})"
                )
                return {
                    'status': 'deleted',
                    'entity_id': validated_entity_id,
                    'hard_delete': False,
                    'deleted_at': record['deleted_at'],
                }
            except Exception as e:
                logger.error(f"Failed to soft delete entity {validated_entity_id}: {e}")
                raise EntityError(f"Failed to delete entity: {e}") from e


async def restore_entity(
    connection: DatabaseConnection,
    entity_id: str,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Restore a soft-deleted entity.

    Args:
        connection: DatabaseConnection instance (must be connected)
        entity_id: Unique identifier for the entity (required)
        group_id: Optional group ID for multi-tenancy (defaults to 'main')

    Returns:
        Dict[str, Any]: Restoration result with status and entity_id

    Raises:
        EntityError: If restoration fails
        EntityNotFoundError: If entity doesn't exist
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     result = await restore_entity(
        ...         conn,
        ...         entity_id='user:john_doe',
        ...         group_id='my_group'
        ...     )
        >>> print(result['status'])
        'restored'
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    validated_entity_id = validate_entity_id(entity_id)
    validated_group_id = validate_group_id(group_id)

    driver = connection.get_driver()

    async with driver.session(database=connection.database) as session:
        async def restore_tx(tx):
            # Check if entity exists
            check_result = await tx.run(
                """
                MATCH (e:Entity {
                    entity_id: $entity_id,
                    group_id: $group_id
                })
                RETURN e.entity_id as entity_id, e._deleted as _deleted
                """,
                entity_id=validated_entity_id,
                group_id=validated_group_id,
            )
            check_record = await check_result.single()

            if check_record is None:
                raise EntityNotFoundError(
                    f"Entity with ID '{validated_entity_id}' not found in group '{validated_group_id}'"
                )

            # Restore: clear deleted flag
            result = await tx.run(
                """
                MATCH (e:Entity {
                    entity_id: $entity_id,
                    group_id: $group_id
                })
                SET e._deleted = false,
                    e.deleted_at = null
                RETURN e.entity_id as entity_id, e._deleted as _deleted
                """,
                entity_id=validated_entity_id,
                group_id=validated_group_id,
            )
            return await result.single()

        try:
            record = await session.execute_write(restore_tx)

            if record is None:
                raise EntityError("Failed to restore entity")

            logger.info(
                f"Restored entity: {validated_entity_id} (group: {validated_group_id})"
            )
            return {
                'status': 'restored',
                'entity_id': validated_entity_id,
            }
        except EntityNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to restore entity {validated_entity_id}: {e}")
            raise EntityError(f"Failed to restore entity: {e}") from e


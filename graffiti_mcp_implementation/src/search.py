"""Semantic search operations for Graffiti Graph.

This module provides functions for searching entities using natural language
queries with semantic similarity (vector embeddings) and lexical search (BM25).
"""

import logging
from typing import Dict, Any, Optional, List

from .database import DatabaseConnection
from .validation import validate_group_id
from .embeddings import cosine_similarity, generate_embedding

logger = logging.getLogger(__name__)


async def search_nodes(
    connection: DatabaseConnection,
    query: str,
    max_nodes: int = 10,
    entity_types: Optional[List[str]] = None,
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Search for entities using natural language query with semantic similarity.

    Args:
        connection: DatabaseConnection instance (must be connected)
        query: Natural language search query (required)
        max_nodes: Maximum number of results to return (default: 10, max: 100)
        entity_types: Optional list of entity types to filter by
        group_id: Optional group ID for multi-tenancy (defaults to 'default')

    Returns:
        Dict[str, Any]: Search results containing:
            - entities: List of matching entities with relevance scores
            - total: Total number of matching entities
            - query: The original search query

    Raises:
        ValueError: If validation fails
        RuntimeError: If connection is not initialized

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
        ...     results = await search_nodes(
        ...         conn,
        ...         query='authentication modules',
        ...         max_nodes=5,
        ...         entity_types=['Module'],
        ...         group_id='my_group'
        ...     )
        >>> print(results['total'])
        3
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    # Validate inputs
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be a non-empty string')

    if not isinstance(max_nodes, int) or max_nodes < 1:
        raise ValueError('max_nodes must be a positive integer')
    if max_nodes > 100:
        raise ValueError('max_nodes cannot exceed 100')

    validated_group_id = validate_group_id(group_id)

    # Generate query embedding
    query_embedding = generate_embedding(query)

    # Search for entities
    driver = connection.get_driver()
    async with driver.session(database=connection.database) as session:
        async def search_entities_tx(tx):
            # Build query to get all entities with embeddings
            cypher_query = """
            MATCH (e:Entity {group_id: $group_id})
            WHERE e._deleted IS NULL OR e._deleted = false
            """
            params = {'group_id': validated_group_id}

            # Filter by entity types if provided
            if entity_types:
                cypher_query += " AND e.entity_type IN $entity_types"
                params['entity_types'] = entity_types

            cypher_query += """
            RETURN e.entity_id as entity_id,
                   e.entity_type as entity_type,
                   e.name as name,
                   e.group_id as group_id,
                   e.summary as summary,
                   e.embedding as embedding,
                   e
            """

            result = await tx.run(cypher_query, **params)
            return [record async for record in result]

        records = await session.execute_read(search_entities_tx)

        # Calculate similarity scores
        results = []
        for record in records:
            entity_embedding = record.get('embedding')
            if entity_embedding is None:
                # Skip entities without embeddings (they need to be generated first)
                continue

            # Calculate cosine similarity
            similarity = cosine_similarity(query_embedding, entity_embedding)

            # Build entity result
            entity = {
                'entity_id': record['entity_id'],
                'entity_type': record['entity_type'],
                'name': record['name'],
                'group_id': record['group_id'],
                'score': float(similarity),
            }

            if record.get('summary'):
                entity['summary'] = record['summary']

            # Extract properties
            e = record['e']
            properties = {}
            for k, v in e.items():
                if k not in ['entity_id', 'entity_type', 'name', 'group_id', 'summary', 'embedding', '_deleted', 'deleted_at', 'created_at', 'updated_at']:
                    properties[k] = v
            if properties:
                entity['properties'] = properties

            results.append(entity)

        # Sort by score (descending) and limit
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:max_nodes]

        logger.info(
            f"Semantic search for '{query}' found {len(results)} entities "
            f"(group: {validated_group_id})"
        )

        return {
            'entities': results,
            'total': len(results),
            'query': query,
        }




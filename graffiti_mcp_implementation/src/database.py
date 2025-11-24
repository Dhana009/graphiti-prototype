"""Database connection and management for Graffiti Graph.

This module provides the database connection interface and initialization
for the Graffiti Graph MCP server.
"""

import logging
from typing import Optional
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError

from .config import Neo4jConfig, get_neo4j_config

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages Neo4j database connection and initialization."""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        config: Optional[Neo4jConfig] = None,
    ):
        """Initialize database connection.

        Args:
            uri: Neo4j connection URI (defaults to config or environment)
            user: Neo4j username (defaults to config or environment)
            password: Neo4j password (defaults to config or environment)
            database: Neo4j database name (defaults to config or environment)
            config: Optional Neo4jConfig object (if not provided, loads from environment)

        Example:
            >>> connection = DatabaseConnection()
            >>> await connection.connect()
            >>> await connection.verify_connection()
        """
        if config is None:
            config = get_neo4j_config()

        self.uri = uri or config.uri
        self.user = user or config.user
        self.password = password or config.password
        self.database = database or config.database
        self.driver: Optional[AsyncGraphDatabase] = None

    async def connect(self) -> None:
        """Create and verify database connection.

        Raises:
            ServiceUnavailable: If Neo4j is not available
            AuthError: If authentication fails
            Exception: For other connection errors

        Example:
            >>> connection = DatabaseConnection()
            >>> await connection.connect()
        """
        try:
            logger.info(f'Connecting to Neo4j at {self.uri}')
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
            )

            # Verify connection by running a simple query
            await self.verify_connection()
            logger.info('Successfully connected to Neo4j')

        except ServiceUnavailable as e:
            logger.error(f'Neo4j service unavailable: {e}')
            raise
        except AuthError as e:
            logger.error(f'Neo4j authentication failed: {e}')
            raise
        except Exception as e:
            logger.error(f'Failed to connect to Neo4j: {e}')
            raise

    async def verify_connection(self) -> None:
        """Verify the database connection is working.

        Raises:
            RuntimeError: If driver is not initialized
            Exception: If connection verification fails

        Example:
            >>> await connection.verify_connection()
        """
        if self.driver is None:
            raise RuntimeError('Driver not initialized. Call connect() first.')

        async with self.driver.session(database=self.database) as session:
            result = await session.run('RETURN 1 as value')
            record = await result.single()

            if record is None or record['value'] != 1:
                raise RuntimeError('Connection verification failed')

    async def close(self) -> None:
        """Close the database connection.

        Example:
            >>> await connection.close()
        """
        if self.driver is not None:
            await self.driver.close()
            self.driver = None
            logger.info('Database connection closed')

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def get_driver(self) -> AsyncGraphDatabase:
        """Get the Neo4j driver instance.

        Returns:
            AsyncGraphDatabase: The Neo4j async driver

        Raises:
            RuntimeError: If driver is not initialized

        Example:
            >>> driver = connection.get_driver()
            >>> async with driver.session() as session:
            ...     result = await session.run('MATCH (n) RETURN count(n)')
        """
        if self.driver is None:
            raise RuntimeError('Driver not initialized. Call connect() first.')
        return self.driver


async def initialize_database(connection: DatabaseConnection) -> None:
    """Initialize database with required constraints and indexes.

    This function creates all necessary constraints and indexes for the
    Graffiti Graph system. It is idempotent and can be run multiple times
    without errors.

    Args:
        connection: DatabaseConnection instance (must be connected)

    Raises:
        RuntimeError: If connection is not initialized
        Exception: For database errors during initialization

    Example:
        >>> async with DatabaseConnection() as conn:
        ...     await initialize_database(conn)
    """
    if connection.driver is None:
        raise RuntimeError('Connection not initialized. Call connect() first.')

    driver = connection.get_driver()

    # Define constraints and indexes based on implementation decisions
    # Using IF NOT EXISTS for idempotency
    constraints_and_indexes = [
        # Constraint: Composite uniqueness on (group_id, entity_id)
        (
            'unique_entity_per_group',
            'CREATE CONSTRAINT unique_entity_per_group IF NOT EXISTS '
            'FOR (e:Entity) REQUIRE (e.group_id, e.entity_id) IS UNIQUE',
        ),
        # Index: Entity type for fast filtering
        (
            'entity_type_index',
            'CREATE INDEX entity_type_index IF NOT EXISTS '
            'FOR (e:Entity) ON (e.entity_type)',
        ),
        # Index: Group ID for multi-tenant isolation
        (
            'entity_group_index',
            'CREATE INDEX entity_group_index IF NOT EXISTS '
            'FOR (e:Entity) ON (e.group_id)',
        ),
        # Index: Relationship type for fast relationship queries
        # Note: Using RELATES_TO as a generic relationship type for indexing
        # The actual relationship_type property will be stored on the relationship
        (
            'relationship_type_index',
            'CREATE INDEX relationship_type_index IF NOT EXISTS '
            'FOR ()-[r:RELATES_TO]-() ON (r.relationship_type)',
        ),
    ]

    async with driver.session(database=connection.database) as session:
        for name, query in constraints_and_indexes:
            try:
                await session.run(query)
                logger.info(f'Created constraint/index: {name}')
            except Exception as e:
                # IF NOT EXISTS should prevent errors, but log warnings if they occur
                logger.warning(
                    f'Constraint/index {name} may already exist or error occurred: {e}'
                )
                # Continue with other constraints/indexes even if one fails
                continue

    logger.info('Database initialization completed')


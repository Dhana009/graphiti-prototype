"""Integration tests for database connection module.

These tests verify that the DatabaseConnection module works correctly
with a running Neo4j instance.
"""

import pytest
from src.database import DatabaseConnection
from src.config import get_neo4j_config


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection_connect():
    """Test that DatabaseConnection can connect to Neo4j."""
    connection = DatabaseConnection()
    await connection.connect()

    try:
        # Verify connection is working
        await connection.verify_connection()

        # Verify we can run queries
        driver = connection.get_driver()
        async with driver.session() as session:
            result = await session.run('RETURN 1 as value')
            record = await result.single()
            assert record is not None
            assert record['value'] == 1

    finally:
        await connection.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection_context_manager():
    """Test DatabaseConnection as async context manager."""
    async with DatabaseConnection() as connection:
        # Verify connection is working
        await connection.verify_connection()

        # Verify we can run queries
        driver = connection.get_driver()
        async with driver.session() as session:
            result = await session.run('RETURN 1 as value')
            record = await result.single()
            assert record is not None
            assert record['value'] == 1

    # Connection should be closed automatically


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection_with_config():
    """Test DatabaseConnection with explicit configuration."""
    config = get_neo4j_config()
    connection = DatabaseConnection(config=config)
    await connection.connect()

    try:
        await connection.verify_connection()
    finally:
        await connection.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection_query_execution():
    """Test that DatabaseConnection can execute queries."""
    async with DatabaseConnection() as connection:
        driver = connection.get_driver()

        async with driver.session() as session:
            # Test node count query
            result = await session.run('MATCH (n) RETURN count(n) as count')
            record = await result.single()
            assert record is not None
            count = record['count']
            assert isinstance(count, int)
            assert count >= 0

            # Test relationship count query
            result = await session.run('MATCH ()-[r]->() RETURN count(r) as count')
            record = await result.single()
            assert record is not None
            rel_count = record['count']
            assert isinstance(rel_count, int)
            assert rel_count >= 0

            # Test creating and querying a test node
            result = await session.run(
                'CREATE (t:TestNode {id: "test_db_connection"}) RETURN t.id as id'
            )
            record = await result.single()
            assert record is not None
            assert record['id'] == 'test_db_connection'

            # Clean up test node
            await session.run('MATCH (t:TestNode {id: "test_db_connection"}) DELETE t')


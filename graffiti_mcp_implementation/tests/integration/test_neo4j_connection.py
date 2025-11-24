"""Integration test to verify Neo4j connection.

This test verifies that we can successfully connect to Neo4j
and perform basic operations.
"""

import os
import pytest
from neo4j import AsyncGraphDatabase


@pytest.mark.integration
@pytest.mark.asyncio
async def test_neo4j_connection():
    """Test basic Neo4j connection and query execution."""
    # Get connection details from environment or use defaults
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'testpassword')

    # Create driver
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    try:
        # Verify connection by running a simple query
        async with driver.session() as session:
            result = await session.run('RETURN 1 as value')
            record = await result.single()

            # Verify we got a result
            assert record is not None
            assert record['value'] == 1

            # Test database version query
            result = await session.run('CALL dbms.components() YIELD name, versions, edition')
            records = await result.values()

            # Verify we got version information
            assert len(records) > 0
            assert any('Neo4j' in str(record) for record in records)

    finally:
        # Always close the driver
        await driver.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_neo4j_database_info():
    """Test retrieving database information."""
    uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'testpassword')

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    try:
        async with driver.session() as session:
            # Verify we can query node count (should be 0 for fresh database)
            result = await session.run('MATCH (n) RETURN count(n) as count')
            record = await result.single()
            assert record is not None
            count = record['count']
            assert isinstance(count, int)
            assert count >= 0  # Should be 0 or more

            # Test relationship count
            result = await session.run('MATCH ()-[r]->() RETURN count(r) as count')
            record = await result.single()
            assert record is not None
            rel_count = record['count']
            assert isinstance(rel_count, int)
            assert rel_count >= 0

            # Test that we can create and query a test node
            result = await session.run(
                'CREATE (t:TestNode {id: "test_connection"}) RETURN t.id as id'
            )
            record = await result.single()
            assert record is not None
            assert record['id'] == 'test_connection'

            # Clean up test node
            await session.run('MATCH (t:TestNode {id: "test_connection"}) DELETE t')

    finally:
        await driver.close()


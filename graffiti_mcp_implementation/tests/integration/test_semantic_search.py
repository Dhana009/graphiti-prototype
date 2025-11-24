"""Integration tests for semantic search operations.

These tests verify that entities can be found using natural language queries
with semantic similarity search.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import numpy as np
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity
from src.search import search_nodes


@pytest.fixture(autouse=True)
async def clean_db_for_semantic_search_tests():
    """Fixture to clean up all nodes and relationships before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_nodes_by_natural_language_query():
    """Test searching for entities using natural language query."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entities
        await add_entity(
            connection,
            entity_id='test:auth_module',
            entity_type='Module',
            name='Authentication Module',
            summary='Handles user authentication and login',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='test:db_module',
            entity_type='Module',
            name='Database Module',
            summary='Manages database connections',
            group_id='test_group',
        )

        # Mock OpenAI embedding generation
        mock_embedding = np.random.rand(1536).tolist()  # text-embedding-3-small dimension

        with patch('src.search.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[MagicMock(embedding=mock_embedding)])
            )

            # Search for authentication-related entities
            results = await search_nodes(
                connection,
                query='authentication and login',
                max_nodes=10,
                group_id='test_group',
            )

            assert len(results['entities']) > 0
            assert results['total'] > 0
            assert results['query'] == 'authentication and login'

            # Verify auth module is in results
            entity_ids = [e['entity_id'] for e in results['entities']]
            assert 'test:auth_module' in entity_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_nodes_returns_relevance_scores():
    """Test that search results include relevance scores (0.0 to 1.0)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            summary='Admin user with full access',
            group_id='test_group',
        )

        mock_embedding = np.random.rand(1536).tolist()

        with patch('src.search.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[MagicMock(embedding=mock_embedding)])
            )

            results = await search_nodes(
                connection,
                query='admin user',
                max_nodes=10,
                group_id='test_group',
            )

            if results['entities']:
                for entity in results['entities']:
                    assert 'score' in entity
                    assert 0.0 <= entity['score'] <= 1.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_nodes_filters_by_entity_type():
    """Test that search can filter by entity type."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities of different types
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='test:module1',
            entity_type='Module',
            name='Auth Module',
            group_id='test_group',
        )

        mock_embedding = np.random.rand(1536).tolist()

        with patch('src.search.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[MagicMock(embedding=mock_embedding)])
            )

            # Search only for User entities
            results = await search_nodes(
                connection,
                query='john',
                max_nodes=10,
                entity_types=['User'],
                group_id='test_group',
            )

            # All results should be User type
            for entity in results['entities']:
                assert entity['entity_type'] == 'User'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_nodes_respects_max_nodes_limit():
    """Test that search respects the max_nodes limit."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create multiple entities
        for i in range(20):
            await add_entity(
                connection,
                entity_id=f'test:entity{i}',
                entity_type='TestEntity',
                name=f'Entity {i}',
                group_id='test_group',
            )

        mock_embedding = np.random.rand(1536).tolist()

        with patch('src.search.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[MagicMock(embedding=mock_embedding)])
            )

            # Search with limit of 5
            results = await search_nodes(
                connection,
                query='entity',
                max_nodes=5,
                group_id='test_group',
            )

            assert len(results['entities']) <= 5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_nodes_returns_empty_array_if_no_matches():
    """Test that search returns empty array if no matches found."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        await add_entity(
            connection,
            entity_id='test:entity1',
            entity_type='TestEntity',
            name='Test Entity',
            group_id='test_group',
        )

        mock_embedding = np.random.rand(1536).tolist()

        with patch('src.search.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[MagicMock(embedding=mock_embedding)])
            )

            # Search for something completely unrelated
            results = await search_nodes(
                connection,
                query='completely unrelated query that will not match',
                max_nodes=10,
                group_id='test_group',
            )

            assert results['entities'] == []
            assert results['total'] == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_nodes_group_isolation():
    """Test that search respects group_id isolation."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities in different groups
        await add_entity(
            connection,
            entity_id='test:entity1',
            entity_type='TestEntity',
            name='Entity in Group 1',
            group_id='group1',
        )
        await add_entity(
            connection,
            entity_id='test:entity1',
            entity_type='TestEntity',
            name='Entity in Group 2',
            group_id='group2',
        )

        mock_embedding = np.random.rand(1536).tolist()

        with patch('src.search.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[MagicMock(embedding=mock_embedding)])
            )

            # Search in group1
            results1 = await search_nodes(
                connection,
                query='entity',
                max_nodes=10,
                group_id='group1',
            )

            # Search in group2
            results2 = await search_nodes(
                connection,
                query='entity',
                max_nodes=10,
                group_id='group2',
            )

            # Results should be isolated
            for entity in results1['entities']:
                assert entity['group_id'] == 'group1'
            for entity in results2['entities']:
                assert entity['group_id'] == 'group2'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_nodes_performance_target():
    """Test that search meets performance target (< 300ms)."""
    import time
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entities
        for i in range(10):
            await add_entity(
                connection,
                entity_id=f'test:entity{i}',
                entity_type='TestEntity',
                name=f'Entity {i}',
                summary=f'Description for entity {i}',
                group_id='test_group',
            )

        mock_embedding = np.random.rand(1536).tolist()

        with patch('src.search.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.embeddings.create = AsyncMock(
                return_value=MagicMock(data=[MagicMock(embedding=mock_embedding)])
            )

            start = time.time()
            results = await search_nodes(
                connection,
                query='test query',
                max_nodes=10,
                group_id='test_group',
            )
            elapsed = (time.time() - start) * 1000  # Convert to milliseconds

            assert elapsed < 300, f"Search took {elapsed}ms, expected < 300ms"
            assert results is not None


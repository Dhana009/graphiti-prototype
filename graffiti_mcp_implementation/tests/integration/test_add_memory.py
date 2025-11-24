"""Integration tests for automatic entity/relationship extraction (add_memory).

These tests verify that entities and relationships can be automatically extracted
from unstructured text using LLM.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.database import DatabaseConnection, initialize_database
from src.entities import get_entity_by_id, get_entities_by_type
from src.relationships import get_entity_relationships
from src.memory import add_memory


@pytest.fixture(autouse=True)
async def clean_db_for_add_memory_tests():
    """Fixture to clean up all nodes and relationships before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_extracts_entities_from_text():
    """Test that add_memory extracts entities from unstructured text."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = """
        John Doe is a software engineer who works on the Authentication Module.
        The Authentication Module handles user login and password verification.
        John uses the Database Module to store user credentials.
        """

        # Mock LLM response
        mock_llm_response = {
            "entities": [
                {
                    "entity_id": "user:john_doe",
                    "entity_type": "User",
                    "name": "John Doe",
                    "summary": "Software engineer",
                    "properties": {"role": "software engineer"}
                },
                {
                    "entity_id": "module:auth",
                    "entity_type": "Module",
                    "name": "Authentication Module",
                    "summary": "Handles user login and password verification"
                },
                {
                    "entity_id": "module:db",
                    "entity_type": "Module",
                    "name": "Database Module",
                    "summary": "Stores user credentials"
                }
            ],
            "relationships": [
                {
                    "source_entity_id": "user:john_doe",
                    "target_entity_id": "module:auth",
                    "relationship_type": "WORKS_ON",
                    "fact": "John Doe works on the Authentication Module"
                },
                {
                    "source_entity_id": "user:john_doe",
                    "target_entity_id": "module:db",
                    "relationship_type": "USES",
                    "fact": "John uses the Database Module"
                }
            ]
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm:
            mock_llm.return_value = mock_llm_response

            result = await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="test_group",
            )

            assert result is not None
            assert 'entities_created' in result
            assert 'relationships_created' in result
            assert result['entities_created'] == 3
            assert result['relationships_created'] == 2

            # Verify entities were created
            john = await get_entity_by_id(connection, "user:john_doe", "test_group")
            assert john is not None
            assert john['name'] == "John Doe"
            assert john['entity_type'] == "User"

            auth_module = await get_entity_by_id(connection, "module:auth", "test_group")
            assert auth_module is not None
            assert auth_module['name'] == "Authentication Module"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_extracts_relationships_from_text():
    """Test that add_memory extracts relationships from unstructured text."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = "The Authentication Module depends on the Database Module for storing user data."

        mock_llm_response = {
            "entities": [
                {"entity_id": "module:auth", "entity_type": "Module", "name": "Authentication Module"},
                {"entity_id": "module:db", "entity_type": "Module", "name": "Database Module"}
            ],
            "relationships": [
                {
                    "source_entity_id": "module:auth",
                    "target_entity_id": "module:db",
                    "relationship_type": "DEPENDS_ON",
                    "fact": "Authentication Module depends on Database Module"
                }
            ]
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm:
            mock_llm.return_value = mock_llm_response

            result = await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="test_group",
            )

            # Verify relationship was created
            relationships = await get_entity_relationships(
                connection,
                entity_id="module:auth",
                direction="outgoing",
                group_id="test_group",
            )

            assert len(relationships) == 1
            assert relationships[0]['relationship_type'] == "DEPENDS_ON"
            assert relationships[0]['target_entity_id'] == "module:db"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_deduplicates_entities():
    """Test that add_memory automatically deduplicates entities."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = "John Doe works on Auth Module. John also uses the Database Module."

        # LLM might extract "John Doe" twice, but should deduplicate
        mock_llm_response = {
            "entities": [
                {"entity_id": "user:john_doe", "entity_type": "User", "name": "John Doe"},
                {"entity_id": "user:john_doe", "entity_type": "User", "name": "John Doe"},  # Duplicate
                {"entity_id": "module:auth", "entity_type": "Module", "name": "Auth Module"},
                {"entity_id": "module:db", "entity_type": "Module", "name": "Database Module"}
            ],
            "relationships": []
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm:
            mock_llm.return_value = mock_llm_response

            result = await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="test_group",
            )

            # Should only create 3 entities (John, Auth Module, DB Module), not 4
            assert result['entities_created'] == 3

            # Verify John exists only once
            users = await get_entities_by_type(connection, "User", "test_group")
            assert len(users) == 1
            assert users[0]['entity_id'] == "user:john_doe"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_generates_embeddings():
    """Test that add_memory generates embeddings for extracted entities."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = "The Authentication Module handles user login."

        mock_llm_response = {
            "entities": [
                {
                    "entity_id": "module:auth",
                    "entity_type": "Module",
                    "name": "Authentication Module",
                    "summary": "Handles user login"
                }
            ],
            "relationships": []
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm, \
             patch('src.embeddings.generate_entity_embedding') as mock_embedding:
            mock_llm.return_value = mock_llm_response
            mock_embedding.return_value = [0.1] * 1536  # Mock embedding

            result = await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="test_group",
            )

            # Verify embedding was generated (called for each entity)
            assert mock_embedding.called
            assert result['entities_created'] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_handles_extraction_failures():
    """Test that add_memory handles LLM extraction failures gracefully."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = "Some text that causes extraction to fail."

        with patch('src.memory._call_llm_for_extraction') as mock_llm:
            mock_llm.side_effect = Exception("LLM API error")

            with pytest.raises(Exception) as exc_info:
                await add_memory(
                    connection,
                    name="test_episode",
                    episode_body=text,
                    source="text",
                    group_id="test_group",
                )
            assert "extraction" in str(exc_info.value).lower() or "llm" in str(exc_info.value).lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_supports_different_source_types():
    """Test that add_memory supports different source types (text, json, message)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        mock_llm_response = {
            "entities": [
                {"entity_id": "test:entity1", "entity_type": "TestEntity", "name": "Test Entity"}
            ],
            "relationships": []
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm:
            mock_llm.return_value = mock_llm_response

            # Test text source
            result1 = await add_memory(
                connection,
                name="test_text",
                episode_body="Some text",
                source="text",
                group_id="test_group",
            )
            assert result1 is not None

            # Test json source
            result2 = await add_memory(
                connection,
                name="test_json",
                episode_body='{"key": "value"}',
                source="json",
                group_id="test_group",
            )
            assert result2 is not None

            # Test message source
            result3 = await add_memory(
                connection,
                name="test_message",
                episode_body="User message content",
                source="message",
                group_id="test_group",
            )
            assert result3 is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_group_isolation():
    """Test that add_memory respects group_id isolation."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = "John Doe is a user."

        mock_llm_response = {
            "entities": [
                {"entity_id": "user:john", "entity_type": "User", "name": "John Doe"}
            ],
            "relationships": []
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm:
            mock_llm.return_value = mock_llm_response

            # Add to group1
            await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="group1",
            )

            # Add to group2
            await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="group2",
            )

            # Verify entities are isolated
            entities_group1 = await get_entities_by_type(connection, "User", "group1")
            entities_group2 = await get_entities_by_type(connection, "User", "group2")

            assert len(entities_group1) == 1
            assert len(entities_group2) == 1
            assert entities_group1[0]['group_id'] == "group1"
            assert entities_group2[0]['group_id'] == "group2"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_memory_performance_small_text():
    """Test that add_memory meets performance target for small text (< 2s)."""
    import time
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = "John Doe is a user."  # Small text

        mock_llm_response = {
            "entities": [
                {"entity_id": "user:john", "entity_type": "User", "name": "John Doe"}
            ],
            "relationships": []
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm, \
             patch('src.embeddings.generate_entity_embedding') as mock_embedding:
            mock_llm.return_value = mock_llm_response
            mock_embedding.return_value = [0.1] * 1536

            start = time.time()
            await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="test_group",
            )
            elapsed = time.time() - start

            assert elapsed < 2.0, f"add_memory took {elapsed}s, expected < 2s for small text"


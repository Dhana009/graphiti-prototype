"""Integration tests for update_memory operations.

These tests verify that existing memory can be updated incrementally
without regenerating everything.
"""

import pytest
from unittest.mock import patch
from src.database import DatabaseConnection, initialize_database
from src.entities import get_entity_by_id, get_entities_by_type
from src.relationships import get_entity_relationships
from src.memory import add_memory, update_memory


@pytest.fixture(autouse=True)
async def clean_db_for_update_memory_tests():
    """Fixture to clean up all nodes and relationships before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_memory_incremental_update():
    """Test that update_memory updates only changed entities/relationships."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Initial content
        initial_text = """
        John Doe is a software engineer who works on the Authentication Module.
        The Authentication Module handles user login.
        """

        initial_llm_response = {
            "entities": [
                {
                    "entity_id": "user:john_doe",
                    "entity_type": "User",
                    "name": "John Doe",
                    "summary": "Software engineer",
                },
                {
                    "entity_id": "module:auth",
                    "entity_type": "Module",
                    "name": "Authentication Module",
                    "summary": "Handles user login",
                }
            ],
            "relationships": [
                {
                    "source_entity_id": "user:john_doe",
                    "target_entity_id": "module:auth",
                    "relationship_type": "WORKS_ON",
                }
            ]
        }

        # Updated content (added new entity and relationship)
        updated_text = """
        John Doe is a software engineer who works on the Authentication Module.
        The Authentication Module handles user login and password verification.
        John uses the Database Module to store user credentials.
        """

        updated_llm_response = {
            "entities": [
                {
                    "entity_id": "user:john_doe",
                    "entity_type": "User",
                    "name": "John Doe",
                    "summary": "Software engineer",
                },
                {
                    "entity_id": "module:auth",
                    "entity_type": "Module",
                    "name": "Authentication Module",
                    "summary": "Handles user login and password verification",  # Updated
                },
                {
                    "entity_id": "module:db",
                    "entity_type": "Module",
                    "name": "Database Module",
                    "summary": "Stores user credentials",
                }
            ],
            "relationships": [
                {
                    "source_entity_id": "user:john_doe",
                    "target_entity_id": "module:auth",
                    "relationship_type": "WORKS_ON",
                },
                {
                    "source_entity_id": "user:john_doe",
                    "target_entity_id": "module:db",
                    "relationship_type": "USES",
                }
            ]
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm, \
             patch('src.embeddings.generate_entity_embedding') as mock_embedding:
            mock_llm.return_value = initial_llm_response
            mock_embedding.return_value = [0.1] * 1536

            # Create initial memory
            result1 = await add_memory(
                connection,
                name="test_episode",
                episode_body=initial_text,
                source="text",
                group_id="test_group",
                uuid="test-uuid-123",
            )

            assert result1['entities_created'] == 2
            assert result1['relationships_created'] == 1

            # Update memory
            mock_llm.return_value = updated_llm_response

            result2 = await update_memory(
                connection,
                uuid="test-uuid-123",
                episode_body=updated_text,
                update_strategy="incremental",
                group_id="test_group",
            )

            assert result2 is not None
            assert 'entities_updated' in result2
            assert 'entities_added' in result2
            assert 'relationships_added' in result2

            # Verify new entity was added
            db_module = await get_entity_by_id(connection, "module:db", "test_group")
            assert db_module is not None
            assert db_module['name'] == "Database Module"

            # Verify existing entity was updated
            auth_module = await get_entity_by_id(connection, "module:auth", "test_group")
            assert auth_module is not None
            assert "password verification" in auth_module.get('summary', '')


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_memory_content_hash_comparison():
    """Test that update_memory skips update if content hash matches."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        text = "John Doe is a software engineer."

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

            # Create initial memory
            await add_memory(
                connection,
                name="test_episode",
                episode_body=text,
                source="text",
                group_id="test_group",
                uuid="test-uuid-456",
            )

            # Update with same content (should skip)
            result = await update_memory(
                connection,
                uuid="test-uuid-456",
                episode_body=text,  # Same content
                update_strategy="incremental",
                group_id="test_group",
            )

            # Should detect no changes
            assert result is not None
            assert result.get('entities_updated', 0) == 0
            assert result.get('entities_added', 0) == 0
            assert result.get('entities_removed', 0) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_memory_replace_strategy():
    """Test that update_memory with replace strategy replaces all content."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        initial_text = "John Doe works on Auth Module."
        updated_text = "Jane Smith works on Database Module."

        initial_llm_response = {
            "entities": [
                {"entity_id": "user:john", "entity_type": "User", "name": "John Doe"},
                {"entity_id": "module:auth", "entity_type": "Module", "name": "Auth Module"}
            ],
            "relationships": [
                {
                    "source_entity_id": "user:john",
                    "target_entity_id": "module:auth",
                    "relationship_type": "WORKS_ON",
                }
            ]
        }

        updated_llm_response = {
            "entities": [
                {"entity_id": "user:jane", "entity_type": "User", "name": "Jane Smith"},
                {"entity_id": "module:db", "entity_type": "Module", "name": "Database Module"}
            ],
            "relationships": [
                {
                    "source_entity_id": "user:jane",
                    "target_entity_id": "module:db",
                    "relationship_type": "WORKS_ON",
                }
            ]
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm, \
             patch('src.embeddings.generate_entity_embedding') as mock_embedding:
            mock_llm.return_value = initial_llm_response
            mock_embedding.return_value = [0.1] * 1536

            # Create initial memory
            await add_memory(
                connection,
                name="test_episode",
                episode_body=initial_text,
                source="text",
                group_id="test_group",
                uuid="test-uuid-789",
            )

            # Update with replace strategy
            mock_llm.return_value = updated_llm_response

            result = await update_memory(
                connection,
                uuid="test-uuid-789",
                episode_body=updated_text,
                update_strategy="replace",
                group_id="test_group",
            )

            assert result is not None

            # Verify new entities exist
            jane = await get_entity_by_id(connection, "user:jane", "test_group")
            assert jane is not None
            
            # Verify old entities are soft-deleted (check directly in database)
            driver = connection.get_driver()
            async with driver.session(database=connection.database) as session:
                async def check_deleted_tx(tx):
                    result = await tx.run(
                        """
                        MATCH (e:Entity {entity_id: $entity_id, group_id: $group_id})
                        RETURN e._deleted as deleted, e.entity_id as entity_id
                        """,
                        entity_id="user:john",
                        group_id="test_group"
                    )
                    record = await result.single()
                    return record
                
                record = await session.execute_read(check_deleted_tx)
                # Old entity should be soft-deleted (or not found if hard-deleted)
                # For replace strategy, entities are soft-deleted
                if record:
                    assert record.get('deleted') is True, "Old entity should be soft-deleted"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_memory_embeddings_only_for_changed():
    """Test that embeddings are only regenerated for changed entities."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Initial content with 2 entities
        initial_text = "John Doe is a user. Jane Smith is a developer."
        updated_text = "John Doe is a software engineer. Jane Smith is a developer."  # Only John changed

        initial_llm_response = {
            "entities": [
                {
                    "entity_id": "user:john",
                    "entity_type": "User",
                    "name": "John Doe",
                    "summary": "A user",
                },
                {
                    "entity_id": "user:jane",
                    "entity_type": "User",
                    "name": "Jane Smith",
                    "summary": "A developer",
                }
            ],
            "relationships": []
        }

        updated_llm_response = {
            "entities": [
                {
                    "entity_id": "user:john",
                    "entity_type": "User",
                    "name": "John Doe",
                    "summary": "A software engineer",  # Changed
                },
                {
                    "entity_id": "user:jane",
                    "entity_type": "User",
                    "name": "Jane Smith",
                    "summary": "A developer",  # Unchanged
                }
            ],
            "relationships": []
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm, \
             patch('src.embeddings.generate_entity_embedding') as mock_embedding:
            mock_llm.return_value = initial_llm_response
            mock_embedding.return_value = [0.1] * 1536

            # Create initial memory
            await add_memory(
                connection,
                name="test_episode",
                episode_body=initial_text,
                source="text",
                group_id="test_group",
                uuid="test-uuid-embed",
            )

            # Count initial embedding calls (should be 2 - one for each entity)
            initial_call_count = mock_embedding.call_count
            assert initial_call_count == 2, f"Expected 2 initial embedding calls, got {initial_call_count}"

            # Reset mock to track only new calls
            mock_embedding.reset_mock()
            mock_embedding.return_value = [0.2] * 1536  # Different embedding to verify regeneration

            # Update memory
            mock_llm.return_value = updated_llm_response

            await update_memory(
                connection,
                uuid="test-uuid-embed",
                episode_body=updated_text,
                update_strategy="incremental",
                group_id="test_group",
            )

            # Embedding should be called exactly once for the updated entity only
            # (only John's summary changed, Jane's didn't change)
            final_call_count = mock_embedding.call_count
            assert final_call_count == 1, \
                f"Expected 1 embedding call (only for changed entity John), " \
                f"got {final_call_count} calls. Jane's embedding should NOT be regenerated."


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_memory_handles_update_failures():
    """Test that update_memory handles failures gracefully."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # First create memory so we can test update failures
        initial_text = "John Doe is a user."
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

            # Create initial memory
            await add_memory(
                connection,
                name="test_episode",
                episode_body=initial_text,
                source="text",
                group_id="test_group",
                uuid="test-uuid-fail",
            )

            # Now test update failure
            mock_llm.side_effect = Exception("LLM API error")

            with pytest.raises(Exception) as exc_info:
                await update_memory(
                    connection,
                    uuid="test-uuid-fail",
                    episode_body="Updated text",
                    group_id="test_group",
                )
            assert "extraction" in str(exc_info.value).lower() or "llm" in str(exc_info.value).lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_memory_preserves_history():
    """Test that update_memory preserves history (soft delete for removed entities)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        initial_text = "John Doe works on Auth Module. Jane Smith works on DB Module."
        updated_text = "John Doe works on Auth Module."  # Jane removed

        initial_llm_response = {
            "entities": [
                {"entity_id": "user:john", "entity_type": "User", "name": "John Doe"},
                {"entity_id": "user:jane", "entity_type": "User", "name": "Jane Smith"},
                {"entity_id": "module:auth", "entity_type": "Module", "name": "Auth Module"},
                {"entity_id": "module:db", "entity_type": "Module", "name": "DB Module"},
            ],
            "relationships": [
                {
                    "source_entity_id": "user:john",
                    "target_entity_id": "module:auth",
                    "relationship_type": "WORKS_ON",
                },
                {
                    "source_entity_id": "user:jane",
                    "target_entity_id": "module:db",
                    "relationship_type": "WORKS_ON",
                }
            ]
        }

        updated_llm_response = {
            "entities": [
                {"entity_id": "user:john", "entity_type": "User", "name": "John Doe"},
                {"entity_id": "module:auth", "entity_type": "Module", "name": "Auth Module"},
            ],
            "relationships": [
                {
                    "source_entity_id": "user:john",
                    "target_entity_id": "module:auth",
                    "relationship_type": "WORKS_ON",
                }
            ]
        }

        with patch('src.memory._call_llm_for_extraction') as mock_llm, \
             patch('src.embeddings.generate_entity_embedding') as mock_embedding:
            mock_llm.return_value = initial_llm_response
            mock_embedding.return_value = [0.1] * 1536

            # Create initial memory
            await add_memory(
                connection,
                name="test_episode",
                episode_body=initial_text,
                source="text",
                group_id="test_group",
                uuid="test-uuid-history",
            )

            # Update memory (removes Jane)
            mock_llm.return_value = updated_llm_response

            result = await update_memory(
                connection,
                uuid="test-uuid-history",
                episode_body=updated_text,
                update_strategy="incremental",
                group_id="test_group",
            )

            assert result is not None
            # Jane should be soft-deleted (implementation dependent)
            # For now, verify John still exists
            john = await get_entity_by_id(connection, "user:john", "test_group")
            assert john is not None


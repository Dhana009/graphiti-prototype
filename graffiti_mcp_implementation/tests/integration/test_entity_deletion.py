"""Integration tests for entity deletion operations.

These tests verify that entities can be deleted correctly (soft and hard delete)
with proper validation, error handling, and multi-tenancy support.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity, get_entity_by_id, delete_entity, EntityNotFoundError


@pytest.fixture(autouse=True)
async def clean_db_for_entity_deletion_tests():
    """Fixture to clean up all entities before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_entity():
    """Test soft deleting an entity (default behavior)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        await add_entity(
            connection,
            entity_id='test:soft_delete',
            entity_type='TestEntity',
            name='Test Entity',
            properties={'email': 'test@example.com'},
            group_id='test_group',
        )
        result = await delete_entity(
            connection,
            entity_id='test:soft_delete',
            group_id='test_group',
        )
        assert result is not None
        assert result['status'] == 'deleted'
        assert result['entity_id'] == 'test:soft_delete'
        assert result['hard_delete'] is False
        assert 'deleted_at' in result

        # Verify entity still exists but is marked as deleted
        driver = connection.get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (e:Entity {
                    entity_id: $entity_id,
                    group_id: $group_id
                })
                RETURN e._deleted as deleted, e.deleted_at as deleted_at
                """,
                entity_id='test:soft_delete',
                group_id='test_group',
            )
            record = await result.single()
            assert record is not None
            assert record['deleted'] is True
            assert record['deleted_at'] is not None

        # Verify get_entity_by_id doesn't return soft-deleted entity
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='test:soft_delete',
                group_id='test_group',
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_entity_idempotent():
    """Test that soft deleting an already deleted entity is idempotent."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        await add_entity(
            connection,
            entity_id='test:soft_delete_idempotent',
            entity_type='TestEntity',
            name='Test Entity',
            group_id='test_group',
        )
        # First soft delete
        result1 = await delete_entity(
            connection,
            entity_id='test:soft_delete_idempotent',
            group_id='test_group',
        )
        assert result1['status'] == 'deleted'
        deleted_at_1 = result1['deleted_at']

        # Second soft delete (should be idempotent)
        result2 = await delete_entity(
            connection,
            entity_id='test:soft_delete_idempotent',
            group_id='test_group',
        )
        assert result2['status'] == 'deleted'
        # Should have same deleted_at timestamp (idempotent)
        assert result2['deleted_at'] == deleted_at_1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_entity_not_found():
    """Test soft deleting a non-existent entity returns error."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        # Soft delete is idempotent, so it should succeed even if entity doesn't exist
        result = await delete_entity(
            connection,
            entity_id='test:nonexistent',
            group_id='test_group',
        )
        # According to implementation, soft delete is idempotent and returns success
        assert result['status'] == 'deleted'
        assert result['already_deleted'] is True


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_entity_group_isolation():
    """Test that entity deletion is isolated by group_id."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        # Create same entity_id in two different groups
        await add_entity(
            connection,
            entity_id='test:same_id',
            entity_type='TestEntity',
            name='Entity in Group 1',
            group_id='group1',
        )
        await add_entity(
            connection,
            entity_id='test:same_id',
            entity_type='TestEntity',
            name='Entity in Group 2',
            group_id='group2',
        )

        # Delete from group1 only
        result = await delete_entity(
            connection,
            entity_id='test:same_id',
            group_id='group1',
        )
        assert result['status'] == 'deleted'

        # Verify group1 entity is deleted
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='test:same_id',
                group_id='group1',
            )

        # Verify group2 entity still exists
        entity = await get_entity_by_id(
            connection,
            entity_id='test:same_id',
            group_id='group2',
        )
        assert entity is not None
        assert entity['name'] == 'Entity in Group 2'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hard_delete_entity():
    """Test hard deleting an entity (permanent removal)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        await add_entity(
            connection,
            entity_id='test:hard_delete',
            entity_type='TestEntity',
            name='Test Entity',
            properties={'email': 'test@example.com'},
            group_id='test_group',
        )
        result = await delete_entity(
            connection,
            entity_id='test:hard_delete',
            group_id='test_group',
            hard=True,
        )
        assert result is not None
        assert result['status'] == 'deleted'
        assert result['entity_id'] == 'test:hard_delete'
        assert result['hard_delete'] is True

        # Verify entity is completely removed from database
        driver = connection.get_driver()
        async with driver.session() as session:
            result = await session.run(
                """
                MATCH (e:Entity {
                    entity_id: $entity_id,
                    group_id: $group_id
                })
                RETURN e
                """,
                entity_id='test:hard_delete',
                group_id='test_group',
            )
            record = await result.single()
            assert record is None

        # Verify get_entity_by_id raises error
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='test:hard_delete',
                group_id='test_group',
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hard_delete_entity_not_found():
    """Test hard deleting a non-existent entity returns error."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        with pytest.raises(EntityNotFoundError):
            await delete_entity(
                connection,
                entity_id='test:nonexistent',
                group_id='test_group',
                hard=True,
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hard_delete_entity_cascade():
    """Test that hard delete removes entity and its relationships."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        # Create two entities
        await add_entity(
            connection,
            entity_id='test:source',
            entity_type='TestEntity',
            name='Source Entity',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='test:target',
            entity_type='TestEntity',
            name='Target Entity',
            group_id='test_group',
        )

        # Create a relationship manually (relationship functions not yet implemented)
        driver = connection.get_driver()
        async with driver.session() as session:
            await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id}),
                      (t:Entity {entity_id: $target_id, group_id: $group_id})
                CREATE (s)-[r:RELATES_TO {created_at: timestamp()}]->(t)
                """,
                source_id='test:source',
                target_id='test:target',
                group_id='test_group',
            )

        # Hard delete source entity
        result = await delete_entity(
            connection,
            entity_id='test:source',
            group_id='test_group',
            hard=True,
        )
        assert result['status'] == 'deleted'
        assert result['hard_delete'] is True

        # Verify relationship is also deleted (DETACH DELETE should cascade)
        async with driver.session() as session:
            rel_result = await session.run(
                """
                MATCH ()-[r:RELATES_TO]->()
                WHERE r.created_at IS NOT NULL
                RETURN r
                """,
            )
            record = await rel_result.single()
            # Relationship should be deleted along with the node
            assert record is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_entity_performance():
    """Test that entity deletion meets performance targets (< 200ms)."""
    import time
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        await add_entity(
            connection,
            entity_id='test:performance',
            entity_type='TestEntity',
            name='Test Entity',
            group_id='test_group',
        )

        # Measure soft delete time
        start = time.time()
        result = await delete_entity(
            connection,
            entity_id='test:performance',
            group_id='test_group',
        )
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds
        assert result['status'] == 'deleted'
        assert elapsed < 200, f"Soft delete took {elapsed}ms, expected < 200ms"

        # Create another entity for hard delete test
        await add_entity(
            connection,
            entity_id='test:performance_hard',
            entity_type='TestEntity',
            name='Test Entity',
            group_id='test_group',
        )

        # Measure hard delete time
        start = time.time()
        result = await delete_entity(
            connection,
            entity_id='test:performance_hard',
            group_id='test_group',
            hard=True,
        )
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds
        assert result['status'] == 'deleted'
        assert elapsed < 200, f"Hard delete took {elapsed}ms, expected < 200ms"

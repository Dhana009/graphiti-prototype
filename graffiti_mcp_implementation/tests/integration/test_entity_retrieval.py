"""Integration tests for entity retrieval functions.

These tests verify that the get_entity_by_id and get_entities_by_type
functions work correctly.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import (
    add_entity,
    get_entity_by_id,
    get_entities_by_type,
    delete_entity,
    EntityNotFoundError,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_by_id_function_exists():
    """Test get_entity_by_id function when entity exists."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entity
        created_entity = await add_entity(
            connection,
            entity_id='test:get_by_id_func',
            entity_type='TestEntity',
            name='Test Entity for Get Function',
            properties={'email': 'test@example.com', 'age': 30},
            summary='Test entity for get function',
            group_id='test_group',
        )

        # Retrieve entity using function
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:get_by_id_func',
            group_id='test_group',
        )

        assert retrieved_entity is not None
        assert retrieved_entity['entity_id'] == 'test:get_by_id_func'
        assert retrieved_entity['entity_type'] == 'TestEntity'
        assert retrieved_entity['name'] == 'Test Entity for Get Function'
        assert retrieved_entity['group_id'] == 'test_group'
        assert retrieved_entity['summary'] == 'Test entity for get function'
        assert retrieved_entity['properties']['email'] == 'test@example.com'
        assert retrieved_entity['properties']['age'] == 30

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:get_by_id_func'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_by_id_function_not_exists():
    """Test get_entity_by_id function when entity doesn't exist."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Try to retrieve non-existent entity
        with pytest.raises(EntityNotFoundError, match='not found'):
            await get_entity_by_id(
                connection,
                entity_id='test:nonexistent_func',
                group_id='test_group',
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_by_id_function_default_group():
    """Test get_entity_by_id function with default group_id."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entity with default group
        await add_entity(
            connection,
            entity_id='test:get_default_group',
            entity_type='TestEntity',
            name='Default Group Entity',
        )

        # Retrieve with default group
        entity = await get_entity_by_id(
            connection,
            entity_id='test:get_default_group',
        )

        assert entity is not None
        assert entity['group_id'] == 'default'

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:get_default_group'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entities_by_type_function_single():
    """Test get_entities_by_type function with single result."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entity
        await add_entity(
            connection,
            entity_id='test:get_type_single',
            entity_type='User',
            name='Single User',
            group_id='test_group',
        )

        # Retrieve entities by type
        entities = await get_entities_by_type(
            connection,
            entity_type='User',
            group_id='test_group',
        )

        assert len(entities) == 1
        assert entities[0]['entity_id'] == 'test:get_type_single'
        assert entities[0]['entity_type'] == 'User'
        assert entities[0]['name'] == 'Single User'

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:get_type_single'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entities_by_type_function_multiple():
    """Test get_entities_by_type function with multiple results."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create multiple entities
        await add_entity(
            connection,
            entity_id='test:get_type_multi_1',
            entity_type='Module',
            name='Module 1',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='test:get_type_multi_2',
            entity_type='Module',
            name='Module 2',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='test:get_type_multi_3',
            entity_type='Module',
            name='Module 3',
            group_id='test_group',
        )

        # Retrieve entities by type
        entities = await get_entities_by_type(
            connection,
            entity_type='Module',
            group_id='test_group',
        )

        assert len(entities) == 3
        entity_ids = [e['entity_id'] for e in entities]
        assert 'test:get_type_multi_1' in entity_ids
        assert 'test:get_type_multi_2' in entity_ids
        assert 'test:get_type_multi_3' in entity_ids

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                for entity_id in ['test:get_type_multi_1', 'test:get_type_multi_2', 'test:get_type_multi_3']:
                    await tx.run("MATCH (e:Entity {entity_id: $id}) DELETE e", id=entity_id)

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entities_by_type_function_no_results():
    """Test get_entities_by_type function when no entities exist."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Retrieve entities by type that don't exist
        entities = await get_entities_by_type(
            connection,
            entity_type='NonexistentType',
            group_id='test_group',
        )

        assert len(entities) == 0
        assert entities == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entities_by_type_function_with_limit():
    """Test get_entities_by_type function with limit."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create multiple entities
        for i in range(5):
            await add_entity(
                connection,
                entity_id=f'test:get_limit_{i}',
                entity_type='LimitedType',
                name=f'Limited Entity {i}',
                group_id='test_group',
            )

        # Retrieve with limit
        entities = await get_entities_by_type(
            connection,
            entity_type='LimitedType',
            group_id='test_group',
            limit=3,
        )

        assert len(entities) == 3

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                for i in range(5):
                    await tx.run("MATCH (e:Entity {entity_id: $id}) DELETE e", id=f'test:get_limit_{i}')

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entities_by_type_function_default_limit():
    """Test get_entities_by_type function with default limit."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities (more than default limit of 50)
        for i in range(60):
            await add_entity(
                connection,
                entity_id=f'test:get_default_limit_{i}',
                entity_type='DefaultLimitType',
                name=f'Default Limit Entity {i}',
                group_id='test_group',
            )

        # Retrieve without specifying limit (should use default of 50)
        entities = await get_entities_by_type(
            connection,
            entity_type='DefaultLimitType',
            group_id='test_group',
        )

        assert len(entities) == 50  # Default limit

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                for i in range(60):
                    await tx.run("MATCH (e:Entity {entity_id: $id}) DELETE e", id=f'test:get_default_limit_{i}')

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entities_by_type_function_limit_validation():
    """Test get_entities_by_type function limit validation."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Test limit exceeds maximum
        with pytest.raises(ValueError, match='Limit cannot exceed'):
            await get_entities_by_type(
                connection,
                entity_type='TestType',
                group_id='test_group',
                limit=1001,  # Exceeds MAX_LIMIT of 1000
            )

        # Test limit is zero
        with pytest.raises(ValueError, match='Limit must be at least 1'):
            await get_entities_by_type(
                connection,
                entity_type='TestType',
                group_id='test_group',
                limit=0,
            )

        # Test limit is negative
        with pytest.raises(ValueError, match='Limit must be at least 1'):
            await get_entities_by_type(
                connection,
                entity_type='TestType',
                group_id='test_group',
                limit=-1,
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_by_id_filters_soft_deleted():
    """Test that get_entity_by_id filters out soft-deleted entities."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entity
        entity = await add_entity(
            connection,
            entity_id='test:soft_deleted_filter',
            entity_type='TestEntity',
            name='Test Entity',
            group_id='test_group',
        )

        # Soft delete the entity
        await delete_entity(
            connection,
            entity_id='test:soft_deleted_filter',
            group_id='test_group',
            hard_delete=False,
        )

        # Try to retrieve soft-deleted entity - should raise EntityNotFoundError
        with pytest.raises(EntityNotFoundError, match='not found'):
            await get_entity_by_id(
                connection,
                entity_id='test:soft_deleted_filter',
                group_id='test_group',
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entities_by_type_filters_soft_deleted():
    """Test that get_entities_by_type filters out soft-deleted entities."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create multiple entities
        await add_entity(connection, 'test:filter_1', 'FilterType', 'Entity 1', group_id='test_group')
        await add_entity(connection, 'test:filter_2', 'FilterType', 'Entity 2', group_id='test_group')
        await add_entity(connection, 'test:filter_3', 'FilterType', 'Entity 3', group_id='test_group')

        # Soft delete one entity
        await delete_entity(connection, 'test:filter_2', 'test_group', hard_delete=False)

        # Retrieve entities - should only return non-deleted ones
        entities = await get_entities_by_type(
            connection,
            entity_type='FilterType',
            group_id='test_group',
        )

        # Should only return 2 entities (filter_1 and filter_3)
        assert len(entities) == 2
        entity_ids = {e['entity_id'] for e in entities}
        assert 'test:filter_1' in entity_ids
        assert 'test:filter_3' in entity_ids
        assert 'test:filter_2' not in entity_ids


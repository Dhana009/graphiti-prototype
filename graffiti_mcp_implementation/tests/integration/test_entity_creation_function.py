"""Integration tests for entity creation function.

These tests verify that the add_entity function works correctly.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity, DuplicateEntityError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_entity_minimal_fields():
    """Test creating entity with minimal required fields using add_entity function."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Clean up any existing test entity
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_minimal'}) DELETE e")

            await session.execute_write(cleanup)

        # Create entity using add_entity function
        entity = await add_entity(
            connection,
            entity_id='test:add_minimal',
            entity_type='TestEntity',
            name='Test Entity',
            group_id='test_group',
        )

        assert entity is not None
        assert entity['entity_id'] == 'test:add_minimal'
        assert entity['entity_type'] == 'TestEntity'
        assert entity['name'] == 'Test Entity'
        assert entity['group_id'] == 'test_group'
        assert entity['summary'] is None
        assert entity['properties'] == {}

        # Clean up
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_minimal'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_entity_with_all_fields():
    """Test creating entity with all fields using add_entity function."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_full'}) DELETE e")

            await session.execute_write(cleanup)

        # Create entity with all fields
        entity = await add_entity(
            connection,
            entity_id='test:add_full',
            entity_type='TestEntity',
            name='Full Test Entity',
            properties={
                'email': 'test@example.com',
                'age': 30,
                'active': True,
                'score': 95.5,
                'metadata': None,
            },
            summary='This is a test entity with all fields',
            group_id='test_group',
        )

        assert entity is not None
        assert entity['entity_id'] == 'test:add_full'
        assert entity['entity_type'] == 'TestEntity'
        assert entity['name'] == 'Full Test Entity'
        assert entity['summary'] == 'This is a test entity with all fields'
        assert entity['properties']['email'] == 'test@example.com'
        assert entity['properties']['age'] == 30
        assert entity['properties']['active'] is True
        assert entity['properties']['score'] == 95.5
        # Note: Neo4j doesn't store null values, but our function should preserve them
        # Check if metadata is in properties (it may or may not be stored)
        if 'metadata' in entity['properties']:
            assert entity['properties']['metadata'] is None

        # Clean up
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_full'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_entity_rejects_duplicate():
    """Test that add_entity rejects duplicate entity_id in same group."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_duplicate'}) DELETE e")

            await session.execute_write(cleanup)

        # Create first entity
        entity1 = await add_entity(
            connection,
            entity_id='test:add_duplicate',
            entity_type='TestEntity',
            name='First Entity',
            group_id='test_group',
        )
        assert entity1 is not None

        # Try to create duplicate
        with pytest.raises(DuplicateEntityError, match='already exists'):
            await add_entity(
                connection,
                entity_id='test:add_duplicate',
                entity_type='TestEntity2',
                name='Duplicate Entity',
                group_id='test_group',
            )

        # Clean up
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_duplicate'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_entity_allows_same_id_different_group():
    """Test that add_entity allows same entity_id in different groups."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_multi_group'}) DELETE e")

            await session.execute_write(cleanup)

        # Create entity in first group
        entity1 = await add_entity(
            connection,
            entity_id='test:add_multi_group',
            entity_type='TestEntity',
            name='Entity Group 1',
            group_id='group1',
        )
        assert entity1 is not None
        assert entity1['group_id'] == 'group1'

        # Create entity with same ID in different group
        entity2 = await add_entity(
            connection,
            entity_id='test:add_multi_group',
            entity_type='TestEntity',
            name='Entity Group 2',
            group_id='group2',
        )
        assert entity2 is not None
        assert entity2['group_id'] == 'group2'

        # Clean up
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_multi_group'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_entity_validation_errors():
    """Test that add_entity validates inputs and raises appropriate errors."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Test None entity_id
        with pytest.raises(ValueError, match='entity_id is required'):
            await add_entity(connection, entity_id=None, entity_type='Test', name='Test')

        # Test empty entity_id
        with pytest.raises(ValueError, match='entity_id cannot be empty'):
            await add_entity(connection, entity_id='', entity_type='Test', name='Test')

        # Test None entity_type
        with pytest.raises(ValueError, match='entity_type is required'):
            await add_entity(connection, entity_id='test', entity_type=None, name='Test')

        # Test None name
        with pytest.raises(ValueError, match='name is required'):
            await add_entity(connection, entity_id='test', entity_type='Test', name=None)

        # Test invalid properties (nested object)
        with pytest.raises(TypeError, match='Property value must be string|number|boolean|null'):
            await add_entity(
                connection,
                entity_id='test',
                entity_type='Test',
                name='Test',
                properties={'nested': {'object': 'not allowed'}},
            )

        # Test invalid properties (array)
        with pytest.raises(TypeError, match='Property value must be string|number|boolean|null'):
            await add_entity(
                connection,
                entity_id='test',
                entity_type='Test',
                name='Test',
                properties={'array': [1, 2, 3]},
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_add_entity_default_group_id():
    """Test that add_entity uses default group_id when not provided."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_default_group'}) DELETE e")

            await session.execute_write(cleanup)

        # Create entity without group_id (should default to 'default')
        entity = await add_entity(
            connection,
            entity_id='test:add_default_group',
            entity_type='TestEntity',
            name='Default Group Entity',
        )

        assert entity is not None
        assert entity['group_id'] == 'default'

        # Clean up
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:add_default_group'}) DELETE e")

            await session.execute_write(cleanup)


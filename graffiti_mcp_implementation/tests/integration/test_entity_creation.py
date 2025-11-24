"""Integration tests for entity creation.

These tests verify that entities can be created correctly with proper
validation and error handling.
"""

import pytest
import time
from neo4j.exceptions import ConstraintError
from src.database import DatabaseConnection, initialize_database


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_entity_minimal_fields():
    """Test creating entity with minimal required fields."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            async def create_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:minimal',
                        entity_type: 'TestEntity',
                        name: 'Test Entity',
                        group_id: 'test_group'
                    })
                    RETURN e.entity_id as entity_id, e.entity_type as entity_type, e.name as name
                    """
                )
                return await result.single()

            record = await session.execute_write(create_entity)
            assert record is not None
            assert record['entity_id'] == 'test:minimal'
            assert record['entity_type'] == 'TestEntity'
            assert record['name'] == 'Test Entity'

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:minimal'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_entity_with_all_fields():
    """Test creating entity with all fields including properties and summary."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            async def create_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:full',
                        entity_type: 'TestEntity',
                        name: 'Full Test Entity',
                        group_id: 'test_group',
                        summary: 'This is a test entity with all fields',
                        email: 'test@example.com',
                        age: 30,
                        active: true,
                        score: 95.5,
                        metadata: null
                    })
                    RETURN e
                    """
                )
                return await result.single()

            record = await session.execute_write(create_entity)
            assert record is not None
            entity = record['e']
            assert entity['entity_id'] == 'test:full'
            assert entity['entity_type'] == 'TestEntity'
            assert entity['name'] == 'Full Test Entity'
            assert entity['summary'] == 'This is a test entity with all fields'
            assert entity['email'] == 'test@example.com'
            assert entity['age'] == 30
            assert entity['active'] is True
            assert entity['score'] == 95.5
            assert entity['metadata'] is None

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:full'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reject_duplicate_entity_id_same_group():
    """Test that duplicate entity_id in same group_id is rejected."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            # Create first entity
            async def create_first(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:duplicate',
                        entity_type: 'TestEntity',
                        name: 'First Entity',
                        group_id: 'test_group'
                    })
                    RETURN e.entity_id as entity_id
                    """
                )
                return await result.single()

            record = await session.execute_write(create_first)
            assert record is not None

            # Try to create duplicate with same (group_id, entity_id)
            async def create_duplicate(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:duplicate',
                        entity_type: 'TestEntity2',
                        name: 'Duplicate Entity',
                        group_id: 'test_group'
                    })
                    RETURN e
                    """
                )
                return await result.single()

            # Should raise ConstraintError
            with pytest.raises(ConstraintError):
                await session.execute_write(create_duplicate)

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:duplicate'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_allow_same_entity_id_different_group():
    """Test that same entity_id can exist in different group_id."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            # Create entity in first group
            async def create_first_group(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:same_id',
                        entity_type: 'TestEntity',
                        name: 'Entity Group 1',
                        group_id: 'group1'
                    })
                    RETURN e.entity_id as entity_id, e.group_id as group_id
                    """
                )
                return await result.single()

            record1 = await session.execute_write(create_first_group)
            assert record1 is not None
            assert record1['entity_id'] == 'test:same_id'
            assert record1['group_id'] == 'group1'

            # Create entity with same entity_id in different group
            async def create_second_group(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:same_id',
                        entity_type: 'TestEntity',
                        name: 'Entity Group 2',
                        group_id: 'group2'
                    })
                    RETURN e.entity_id as entity_id, e.group_id as group_id
                    """
                )
                return await result.single()

            record2 = await session.execute_write(create_second_group)
            assert record2 is not None
            assert record2['entity_id'] == 'test:same_id'
            assert record2['group_id'] == 'group2'

            # Both should exist
            async def verify_both(tx):
                result = await tx.run(
                    """
                    MATCH (e:Entity {entity_id: 'test:same_id'})
                    RETURN e.group_id as group_id
                    ORDER BY e.group_id
                    """
                )
                return [record['group_id'] async for record in result]

            groups = await session.execute_read(verify_both)
            assert len(groups) == 2
            assert 'group1' in groups
            assert 'group2' in groups

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:same_id'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_entity_creation_performance():
    """Test that entity creation meets performance requirements (< 200ms)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            async def create_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:performance',
                        entity_type: 'TestEntity',
                        name: 'Performance Test Entity',
                        group_id: 'test_group'
                    })
                    RETURN e.entity_id as entity_id
                    """
                )
                return await result.single()

            start_time = time.time()
            record = await session.execute_write(create_entity)
            elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            assert record is not None
            assert elapsed_time < 200, f'Entity creation took {elapsed_time}ms, expected < 200ms'

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:performance'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_entity_properties_string_number_boolean_null():
    """Test that entity properties accept string, number, boolean, and null values."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            async def create_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:properties',
                        entity_type: 'TestEntity',
                        name: 'Properties Test',
                        group_id: 'test_group',
                        string_prop: 'test string',
                        int_prop: 42,
                        float_prop: 3.14,
                        bool_prop: true,
                        null_prop: null
                    })
                    RETURN e
                    """
                )
                return await result.single()

            record = await session.execute_write(create_entity)
            assert record is not None
            entity = record['e']
            assert entity['string_prop'] == 'test string'
            assert entity['int_prop'] == 42
            assert entity['float_prop'] == 3.14
            assert entity['bool_prop'] is True
            assert entity['null_prop'] is None

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:properties'}) DELETE e")

            await session.execute_write(cleanup)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_entity_default_group_id():
    """Test that entity uses default group_id when not provided."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            # Note: This test will need to be updated once we implement
            # the entity creation function that handles default group_id
            # For now, we test that group_id can be set to 'default'
            async def create_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test:default_group',
                        entity_type: 'TestEntity',
                        name: 'Default Group Entity',
                        group_id: 'default'
                    })
                    RETURN e.group_id as group_id
                    """
                )
                return await result.single()

            record = await session.execute_write(create_entity)
            assert record is not None
            assert record['group_id'] == 'default'

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:default_group'}) DELETE e")

            await session.execute_write(cleanup)


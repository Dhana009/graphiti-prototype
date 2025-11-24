"""Integration tests for database initialization implementation.

These tests verify that the initialize_database function works correctly.
"""

import pytest
from src.database import DatabaseConnection, initialize_database


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialize_database_creates_constraints():
    """Test that initialize_database creates required constraints."""
    async with DatabaseConnection() as connection:
        # Run initialization
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            # Query for the constraint
            result = await session.run(
                "SHOW CONSTRAINTS YIELD name, type WHERE name = 'unique_entity_per_group' "
                "RETURN name, type"
            )
            record = await result.single()

            # Verify constraint exists
            assert record is not None
            assert record['name'] == 'unique_entity_per_group'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialize_database_creates_indexes():
    """Test that initialize_database creates required indexes."""
    async with DatabaseConnection() as connection:
        # Run initialization
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            # Query for indexes
            expected_indexes = [
                'entity_type_index',
                'entity_group_index',
                'relationship_type_index',
            ]

            for index_name in expected_indexes:
                result = await session.run(
                    f"SHOW INDEXES YIELD name WHERE name = '{index_name}' RETURN name"
                )
                record = await result.single()

                # Verify index exists
                assert record is not None, f'Index {index_name} should exist'
                assert record['name'] == index_name


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialize_database_is_idempotent():
    """Test that initialize_database can be run multiple times without errors."""
    async with DatabaseConnection() as connection:
        # Run initialization first time
        await initialize_database(connection)

        # Run initialization second time (should not error)
        await initialize_database(connection)

        # Run initialization third time (should not error)
        await initialize_database(connection)

        # Verify constraints and indexes still exist
        driver = connection.get_driver()
        async with driver.session() as session:
            # Check constraint
            result = await session.run(
                "SHOW CONSTRAINTS YIELD name WHERE name = 'unique_entity_per_group' "
                "RETURN name"
            )
            record = await result.single()
            assert record is not None

            # Check indexes
            for index_name in ['entity_type_index', 'entity_group_index', 'relationship_type_index']:
                result = await session.run(
                    f"SHOW INDEXES YIELD name WHERE name = '{index_name}' RETURN name"
                )
                record = await result.single()
                assert record is not None, f'Index {index_name} should still exist after multiple initializations'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_constraint_enforces_uniqueness():
    """Test that the unique constraint prevents duplicate entity_id per group_id."""
    async with DatabaseConnection() as connection:
        # Ensure initialization is done
        await initialize_database(connection)

        driver = connection.get_driver()
        async with driver.session() as session:
            # Clean up any existing test entities first
            async def cleanup_existing(tx):
                await tx.run(
                    "MATCH (e:Entity {entity_id: 'test_unique_constraint'}) DELETE e"
                )

            await session.execute_write(cleanup_existing)

            # Create first entity using write transaction
            async def create_first_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test_unique_constraint',
                        entity_type: 'TestEntity',
                        name: 'Test Entity',
                        group_id: 'test_group'
                    })
                    RETURN e.entity_id as entity_id
                    """
                )
                return await result.single()

            record = await session.execute_write(create_first_entity)
            assert record is not None
            assert record['entity_id'] == 'test_unique_constraint'

            # Try to create duplicate entity with same (group_id, entity_id)
            # This should fail due to constraint
            from neo4j.exceptions import ConstraintError

            async def create_duplicate_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test_unique_constraint',
                        entity_type: 'TestEntity2',
                        name: 'Test Entity 2',
                        group_id: 'test_group'
                    })
                    RETURN e
                    """
                )
                return await result.single()

            # This should raise ConstraintError
            with pytest.raises(ConstraintError):
                await session.execute_write(create_duplicate_entity)

            # But we CAN create entity with same entity_id but different group_id
            async def create_different_group_entity(tx):
                result = await tx.run(
                    """
                    CREATE (e:Entity {
                        entity_id: 'test_unique_constraint',
                        entity_type: 'TestEntity',
                        name: 'Test Entity Different Group',
                        group_id: 'different_group'
                    })
                    RETURN e.entity_id as entity_id
                    """
                )
                return await result.single()

            record = await session.execute_write(create_different_group_entity)
            assert record is not None
            assert record['entity_id'] == 'test_unique_constraint'

            # Clean up
            async def cleanup(tx):
                await tx.run(
                    "MATCH (e:Entity {entity_id: 'test_unique_constraint'}) DELETE e"
                )

            await session.execute_write(cleanup)


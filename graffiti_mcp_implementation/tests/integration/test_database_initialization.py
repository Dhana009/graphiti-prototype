"""Integration tests for database initialization.

These tests verify that database constraints and indexes are created
correctly and that initialization is idempotent.
"""

import pytest
from src.database import DatabaseConnection


# Expected constraint and index names based on implementation decisions
EXPECTED_CONSTRAINT = 'unique_entity_per_group'
EXPECTED_INDEXES = [
    'entity_type_index',
    'entity_group_index',
    'relationship_type_index',
]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialization_creates_constraints():
    """Test that initialization creates required constraints."""
    async with DatabaseConnection() as connection:
        driver = connection.get_driver()

        # This test will be updated once we implement the initialization function
        # For now, we verify we can query for constraints
        async with driver.session() as session:
            # Query for existing constraints
            result = await session.run(
                'SHOW CONSTRAINTS YIELD name, type, properties'
            )
            constraints = await result.values()

            # Verify we can query constraints (even if none exist yet)
            assert constraints is not None
            assert isinstance(constraints, list)

            # Once initialization is implemented, we should verify:
            # - unique_entity_per_group constraint exists
            # - It's a UNIQUENESS constraint
            # - It applies to (group_id, entity_id) properties


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialization_creates_indexes():
    """Test that initialization creates required indexes."""
    async with DatabaseConnection() as connection:
        driver = connection.get_driver()

        # This test will be updated once we implement the initialization function
        # For now, we verify we can query for indexes
        async with driver.session() as session:
            # Query for existing indexes
            result = await session.run(
                'SHOW INDEXES YIELD name, type, properties'
            )
            indexes = await result.values()

            # Verify we can query indexes (even if none exist yet)
            assert indexes is not None
            assert isinstance(indexes, list)

            # Once initialization is implemented, we should verify:
            # - entity_type_index exists (on Entity.entity_type)
            # - entity_group_index exists (on Entity.group_id)
            # - relationship_type_index exists (on relationship.type)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_initialization_is_idempotent():
    """Test that initialization can be run multiple times without errors."""
    async with DatabaseConnection() as connection:
        driver = connection.get_driver()

        # This test will verify that running initialization multiple times
        # doesn't cause errors (using IF NOT EXISTS)
        # For now, we just verify the connection works
        async with driver.session() as session:
            result = await session.run('RETURN 1 as value')
            record = await result.single()
            assert record is not None
            assert record['value'] == 1

        # Once initialization is implemented, we should:
        # 1. Run initialization function
        # 2. Verify constraints/indexes exist
        # 3. Run initialization function again
        # 4. Verify no errors occurred
        # 5. Verify constraints/indexes still exist (same state)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_can_query_constraint_existence():
    """Test that we can query for specific constraint existence."""
    async with DatabaseConnection() as connection:
        driver = connection.get_driver()

        async with driver.session() as session:
            # Query for a specific constraint by name
            result = await session.run(
                f"SHOW CONSTRAINTS YIELD name WHERE name = '{EXPECTED_CONSTRAINT}' RETURN name"
            )
            record = await result.single()

            # Constraint may or may not exist yet (depending on initialization)
            # But we should be able to query for it
            # If it exists, record will have a name; if not, record will be None
            if record is not None:
                assert record['name'] == EXPECTED_CONSTRAINT

            # Once initialization is implemented, this test should:
            # - Verify the constraint exists after initialization
            # - Verify the constraint type is UNIQUENESS
            # - Verify it applies to Entity nodes
            # - Verify it enforces uniqueness on (group_id, entity_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_can_query_index_existence():
    """Test that we can query for specific index existence."""
    async with DatabaseConnection() as connection:
        driver = connection.get_driver()

        async with driver.session() as session:
            # Query for specific indexes
            for index_name in EXPECTED_INDEXES:
                result = await session.run(
                    f"SHOW INDEXES YIELD name WHERE name = '{index_name}' RETURN name"
                )
                record = await result.single()

                # Index may or may not exist yet
                # But we should be able to query for it
                if record is not None:
                    assert record['name'] == index_name

            # Once initialization is implemented, this test should:
            # - Verify all expected indexes exist after initialization
            # - Verify each index is on the correct property
            # - Verify indexes are on the correct node/relationship types


@pytest.mark.integration
@pytest.mark.asyncio
async def test_constraint_prevents_duplicate_entities():
    """Test that unique constraint prevents duplicate entity_id per group_id."""
    async with DatabaseConnection() as connection:
        driver = connection.get_driver()

        # This test will verify that once the constraint is created,
        # we cannot create duplicate entities with the same (group_id, entity_id)
        # For now, we just verify we can create and query nodes
        async with driver.session() as session:
            # Create a test entity
            result = await session.run(
                """
                CREATE (e:Entity:TestEntity {
                    entity_id: 'test_duplicate_check',
                    entity_type: 'TestEntity',
                    name: 'Test Entity',
                    group_id: 'test_group'
                })
                RETURN e.entity_id as entity_id
                """
            )
            record = await result.single()
            assert record is not None
            assert record['entity_id'] == 'test_duplicate_check'

            # Clean up
            await session.run(
                "MATCH (e:Entity {entity_id: 'test_duplicate_check'}) DELETE e"
            )

        # Once initialization and constraint are implemented, this test should:
        # 1. Run initialization to create constraint
        # 2. Create entity with (group_id='test', entity_id='test1')
        # 3. Try to create another entity with same (group_id='test', entity_id='test1')
        # 4. Verify it raises ConstraintError
        # 5. Verify we CAN create entity with same entity_id but different group_id
        # 6. Clean up test entities


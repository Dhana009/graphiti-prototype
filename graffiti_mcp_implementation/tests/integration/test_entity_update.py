"""Integration tests for entity update operations.

These tests verify that entities can be updated correctly with proper
validation, error handling, and multi-tenancy support.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity, get_entity_by_id, update_entity, EntityNotFoundError


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_name():
    """Test updating an entity's name."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entity
        entity = await add_entity(
            connection,
            entity_id='test:update_name',
            entity_type='TestEntity',
            name='Original Name',
            group_id='test_group',
        )

        # Update name using update_entity function
        updated_entity = await update_entity(
            connection,
            entity_id='test:update_name',
            name='Updated Name',
            group_id='test_group',
        )

        assert updated_entity is not None
        assert updated_entity['name'] == 'Updated Name'
        assert updated_entity['entity_id'] == 'test:update_name'
        assert updated_entity['entity_type'] == 'TestEntity'

        # Verify update persisted
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:update_name',
            group_id='test_group',
        )
        assert retrieved_entity is not None
        assert retrieved_entity['name'] == 'Updated Name'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_properties():
    """Test updating an entity's properties."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entity with initial properties
        entity = await add_entity(
            connection,
            entity_id='test:update_props',
            entity_type='TestEntity',
            name='Test Entity',
            properties={'email': 'old@example.com', 'age': 25},
            group_id='test_group',
        )

        # Update properties
        updated_entity = await update_entity(
            connection,
            entity_id='test:update_props',
            properties={
                'email': 'new@example.com',
                'age': 30,
                'status': 'active',
            },
            group_id='test_group',
        )

        assert updated_entity is not None
        assert updated_entity['properties']['email'] == 'new@example.com'
        assert updated_entity['properties']['age'] == 30
        assert updated_entity['properties']['status'] == 'active'

        # Verify update persisted
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:update_props',
            group_id='test_group',
        )
        assert retrieved_entity['properties']['email'] == 'new@example.com'
        assert retrieved_entity['properties']['age'] == 30
        assert retrieved_entity['properties']['status'] == 'active'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_summary():
    """Test updating an entity's summary."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create test entity
        entity = await add_entity(
            connection,
            entity_id='test:update_summary',
            entity_type='TestEntity',
            name='Test Entity',
            summary='Original summary',
            group_id='test_group',
        )

        # Update summary
        updated_entity = await update_entity(
            connection,
            entity_id='test:update_summary',
            summary='Updated summary',
            group_id='test_group',
        )

        assert updated_entity is not None
        assert updated_entity['summary'] == 'Updated summary'

        # Verify update persisted
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:update_summary',
            group_id='test_group',
        )
        assert retrieved_entity['summary'] == 'Updated summary'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_not_found():
    """Test updating a non-existent entity returns error."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Try to update non-existent entity
        with pytest.raises(EntityNotFoundError, match="Entity with ID 'test:nonexistent' not found"):
            await update_entity(
                connection,
                entity_id='test:nonexistent',
                name='New Name',
                group_id='test_group',
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_group_isolation():
    """Test that entity updates are isolated by group_id."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entity in group1
        entity1 = await add_entity(
            connection,
            entity_id='test:update_isolation',
            entity_type='TestEntity',
            name='Entity in Group 1',
            group_id='group1',
        )

        # Create entity with same ID in group2
        entity2 = await add_entity(
            connection,
            entity_id='test:update_isolation',
            entity_type='TestEntity',
            name='Entity in Group 2',
            group_id='group2',
        )

        # Update entity in group1
        updated1 = await update_entity(
            connection,
            entity_id='test:update_isolation',
            name='Updated Group 1',
            group_id='group1',
        )

        assert updated1['name'] == 'Updated Group 1'
        assert updated1['group_id'] == 'group1'

        # Verify group1 entity was updated
        retrieved1 = await get_entity_by_id(
            connection,
            entity_id='test:update_isolation',
            group_id='group1',
        )
        assert retrieved1['name'] == 'Updated Group 1'

        # Verify group2 entity was NOT updated
        unchanged2 = await get_entity_by_id(
            connection,
            entity_id='test:update_isolation',
            group_id='group2',
        )
        assert unchanged2['name'] == 'Entity in Group 2'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_partial_update():
    """Test that partial updates only change specified fields."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entity with multiple fields
        entity = await add_entity(
            connection,
            entity_id='test:partial_update',
            entity_type='TestEntity',
            name='Original Name',
            properties={'email': 'original@example.com', 'age': 25},
            summary='Original summary',
            group_id='test_group',
        )

        # Update only name, leaving other fields unchanged
        updated_entity = await update_entity(
            connection,
            entity_id='test:partial_update',
            name='Updated Name Only',
            group_id='test_group',
        )

        assert updated_entity['name'] == 'Updated Name Only'
        # Other fields should remain unchanged
        assert updated_entity['properties']['email'] == 'original@example.com'
        assert updated_entity['properties']['age'] == 25
        assert updated_entity['summary'] == 'Original summary'

        # Verify partial update persisted
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:partial_update',
            group_id='test_group',
        )
        assert retrieved_entity['name'] == 'Updated Name Only'
        assert retrieved_entity['properties']['email'] == 'original@example.com'
        assert retrieved_entity['properties']['age'] == 25
        assert retrieved_entity['summary'] == 'Original summary'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_remove_property():
    """Test removing a property by not including it in update."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entity with properties
        entity = await add_entity(
            connection,
            entity_id='test:remove_prop',
            entity_type='TestEntity',
            name='Test Entity',
            properties={'email': 'test@example.com', 'age': 25},
            group_id='test_group',
        )

        # Update properties, removing email (by not including it)
        # Note: Our implementation replaces all properties, so we need to include age
        updated_entity = await update_entity(
            connection,
            entity_id='test:remove_prop',
            properties={'age': 25},  # Only include age, email will be removed
            group_id='test_group',
        )

        # Email should not be in properties
        assert 'email' not in updated_entity['properties']
        # Age should still be present
        assert updated_entity['properties']['age'] == 25

        # Verify property was removed
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:remove_prop',
            group_id='test_group',
        )
        # Email should not be in properties
        assert 'email' not in retrieved_entity['properties']
        # Age should still be present
        assert retrieved_entity['properties']['age'] == 25


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_remove_summary():
    """Test removing summary by setting it to None."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entity with summary
        entity = await add_entity(
            connection,
            entity_id='test:remove_summary',
            entity_type='TestEntity',
            name='Test Entity',
            summary='Original summary',
            group_id='test_group',
        )

        # Remove summary by setting to None
        updated_entity = await update_entity(
            connection,
            entity_id='test:remove_summary',
            summary=None,
            group_id='test_group',
        )

        # Summary should be None or not present
        assert updated_entity.get('summary') is None

        # Verify summary was removed
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:remove_summary',
            group_id='test_group',
        )
        assert retrieved_entity.get('summary') is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_entity_all_fields():
    """Test updating all fields at once."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entity
        entity = await add_entity(
            connection,
            entity_id='test:update_all',
            entity_type='TestEntity',
            name='Original Name',
            properties={'old': 'value'},
            summary='Original summary',
            group_id='test_group',
        )

        # Update all fields
        updated_entity = await update_entity(
            connection,
            entity_id='test:update_all',
            name='New Name',
            properties={'new': 'value', 'another': 42},
            summary='New summary',
            group_id='test_group',
        )

        assert updated_entity['name'] == 'New Name'
        assert updated_entity['properties']['new'] == 'value'
        assert updated_entity['properties']['another'] == 42
        assert 'old' not in updated_entity['properties']  # Old property removed
        assert updated_entity['summary'] == 'New summary'

        # Verify all updates persisted
        retrieved_entity = await get_entity_by_id(
            connection,
            entity_id='test:update_all',
            group_id='test_group',
        )
        assert retrieved_entity['name'] == 'New Name'
        assert retrieved_entity['properties']['new'] == 'value'
        assert retrieved_entity['properties']['another'] == 42
        assert 'old' not in retrieved_entity['properties']
        assert retrieved_entity['summary'] == 'New summary'


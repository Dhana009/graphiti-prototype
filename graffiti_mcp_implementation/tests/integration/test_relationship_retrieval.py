"""Integration tests for relationship retrieval operations.

These tests verify that relationships can be retrieved correctly with proper
filtering, error handling, and multi-tenancy support.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity, EntityNotFoundError
from src.relationships import add_relationship, get_entity_relationships


@pytest.fixture(autouse=True)
async def clean_db_for_relationship_retrieval_tests():
    """Fixture to clean up all nodes and relationships before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_outgoing_relationships():
    """Test retrieving outgoing relationships for an entity."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities
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
        await add_entity(
            connection,
            entity_id='test:module2',
            entity_type='Module',
            name='DB Module',
            group_id='test_group',
        )

        # Create outgoing relationships
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='test_group',
        )
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module2',
            relationship_type='OWNS',
            group_id='test_group',
        )

        # Get outgoing relationships
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            group_id='test_group',
        )

        assert len(relationships) == 2
        rel_types = [r['relationship_type'] for r in relationships]
        assert 'USES' in rel_types
        assert 'OWNS' in rel_types

        # Verify all relationships have correct source
        for rel in relationships:
            assert rel['source_entity_id'] == 'test:user1'
            assert rel['group_id'] == 'test_group'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_incoming_relationships():
    """Test retrieving incoming relationships for an entity."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='test:user2',
            entity_type='User',
            name='Jane Doe',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='test:module1',
            entity_type='Module',
            name='Auth Module',
            group_id='test_group',
        )

        # Create incoming relationships (others point to module1)
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='test_group',
        )
        await add_relationship(
            connection,
            source_entity_id='test:user2',
            target_entity_id='test:module1',
            relationship_type='OWNS',
            group_id='test_group',
        )

        # Get incoming relationships for module1
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:module1',
            direction='incoming',
            group_id='test_group',
        )

        assert len(relationships) == 2
        rel_types = [r['relationship_type'] for r in relationships]
        assert 'USES' in rel_types
        assert 'OWNS' in rel_types

        # Verify all relationships have correct target
        for rel in relationships:
            assert rel['target_entity_id'] == 'test:module1'
            assert rel['group_id'] == 'test_group'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_both_directions_relationships():
    """Test retrieving both incoming and outgoing relationships."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities
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
        await add_entity(
            connection,
            entity_id='test:module2',
            entity_type='Module',
            name='DB Module',
            group_id='test_group',
        )

        # Create outgoing relationship (user1 -> module1)
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='test_group',
        )

        # Create incoming relationship (module2 -> user1)
        await add_relationship(
            connection,
            source_entity_id='test:module2',
            target_entity_id='test:user1',
            relationship_type='CONTAINS',
            group_id='test_group',
        )

        # Get both directions
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='both',
            group_id='test_group',
        )

        assert len(relationships) == 2

        # Check outgoing
        outgoing = [r for r in relationships if r['source_entity_id'] == 'test:user1']
        assert len(outgoing) == 1
        assert outgoing[0]['relationship_type'] == 'USES'
        assert outgoing[0]['target_entity_id'] == 'test:module1'

        # Check incoming
        incoming = [r for r in relationships if r['target_entity_id'] == 'test:user1']
        assert len(incoming) == 1
        assert incoming[0]['relationship_type'] == 'CONTAINS'
        assert incoming[0]['source_entity_id'] == 'test:module2'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_relationships_filter_by_type():
    """Test filtering relationships by relationship type."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities
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
        await add_entity(
            connection,
            entity_id='test:module2',
            entity_type='Module',
            name='DB Module',
            group_id='test_group',
        )

        # Create relationships with different types
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='test_group',
        )
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module2',
            relationship_type='OWNS',
            group_id='test_group',
        )

        # Filter by USES only
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            relationship_types=['USES'],
            group_id='test_group',
        )

        assert len(relationships) == 1
        assert relationships[0]['relationship_type'] == 'USES'
        assert relationships[0]['target_entity_id'] == 'test:module1'

        # Filter by multiple types
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            relationship_types=['USES', 'OWNS'],
            group_id='test_group',
        )

        assert len(relationships) == 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_relationships_entity_with_no_relationships():
    """Test retrieving relationships for entity with no relationships returns empty array."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entity with no relationships
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )

        # Get relationships (should return empty array, not error)
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='both',
            group_id='test_group',
        )

        assert relationships == []
        assert isinstance(relationships, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_relationships_entity_not_found():
    """Test that retrieving relationships for non-existent entity returns error."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Try to get relationships for non-existent entity
        with pytest.raises(EntityNotFoundError) as exc_info:
            await get_entity_relationships(
                connection,
                entity_id='test:nonexistent',
                direction='both',
                group_id='test_group',
            )
        assert 'not found' in str(exc_info.value).lower()
        assert 'test:nonexistent' in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_relationships_with_limit():
    """Test that limit parameter works correctly."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        for i in range(5):
            await add_entity(
                connection,
                entity_id=f'test:module{i}',
                entity_type='Module',
                name=f'Module {i}',
                group_id='test_group',
            )
            await add_relationship(
                connection,
                source_entity_id='test:user1',
                target_entity_id=f'test:module{i}',
                relationship_type='USES',
                group_id='test_group',
            )

        # Get relationships with limit
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            limit=3,
            group_id='test_group',
        )

        assert len(relationships) == 3


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_relationships_group_isolation():
    """Test that relationship retrieval is isolated by group_id."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities in group1
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='User 1',
            group_id='group1',
        )
        await add_entity(
            connection,
            entity_id='test:module1',
            entity_type='Module',
            name='Module 1',
            group_id='group1',
        )

        # Create entities in group2 (same entity_ids)
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='User 1',
            group_id='group2',
        )
        await add_entity(
            connection,
            entity_id='test:module1',
            entity_type='Module',
            name='Module 1',
            group_id='group2',
        )

        # Create relationship in group1
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='group1',
        )

        # Create relationship in group2 (different type)
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='OWNS',
            group_id='group2',
        )

        # Get relationships from group1
        relationships1 = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            group_id='group1',
        )
        assert len(relationships1) == 1
        assert relationships1[0]['relationship_type'] == 'USES'
        assert relationships1[0]['group_id'] == 'group1'

        # Get relationships from group2
        relationships2 = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            group_id='group2',
        )
        assert len(relationships2) == 1
        assert relationships2[0]['relationship_type'] == 'OWNS'
        assert relationships2[0]['group_id'] == 'group2'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_relationships_with_properties():
    """Test that relationship properties are included in results."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities
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

        # Create relationship with properties
        await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            properties={'since': '2024-01-01', 'permission': 'read'},
            fact='John uses Auth Module for login',
            group_id='test_group',
        )

        # Get relationships
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            group_id='test_group',
        )

        assert len(relationships) == 1
        rel = relationships[0]
        assert rel['properties']['since'] == '2024-01-01'
        assert rel['properties']['permission'] == 'read'
        assert rel['fact'] == 'John uses Auth Module for login'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_relationships_performance():
    """Test that relationship retrieval meets performance target (< 200ms)."""
    import time
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create entities
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        for i in range(10):
            await add_entity(
                connection,
                entity_id=f'test:module{i}',
                entity_type='Module',
                name=f'Module {i}',
                group_id='test_group',
            )
            await add_relationship(
                connection,
                source_entity_id='test:user1',
                target_entity_id=f'test:module{i}',
                relationship_type='USES',
                group_id='test_group',
            )

        # Measure retrieval time
        start = time.time()
        relationships = await get_entity_relationships(
            connection,
            entity_id='test:user1',
            direction='outgoing',
            group_id='test_group',
        )
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        assert len(relationships) == 10
        assert elapsed < 200, f"Relationship retrieval took {elapsed}ms, expected < 200ms"


"""Integration tests for relationship creation operations.

These tests verify that relationships can be created correctly with proper
validation, error handling, and multi-tenancy support.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity, get_entity_by_id, EntityNotFoundError
from src.relationships import (
    add_relationship,
    RelationshipError,
)


@pytest.fixture(autouse=True)
async def clean_db_for_relationship_tests():
    """Fixture to clean up all nodes and relationships before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_between_existing_entities():
    """Test creating a relationship between two existing entities."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create source entity
        source = await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )

        # Create target entity
        target = await add_entity(
            connection,
            entity_id='test:module1',
            entity_type='Module',
            name='Auth Module',
            group_id='test_group',
        )

        # Create relationship
        relationship = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='test_group',
        )

        assert relationship is not None
        assert relationship['source_entity_id'] == 'test:user1'
        assert relationship['target_entity_id'] == 'test:module1'
        assert relationship['relationship_type'] == 'USES'
        assert relationship['group_id'] == 'test_group'

        # Verify relationship exists in database
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(t:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type
                RETURN r.relationship_type as type, r.group_id as group_id
                """,
                source_id='test:user1',
                target_id='test:module1',
                group_id='test_group',
                rel_type='USES',
            )
            record = await result.single()
            assert record is not None
            assert record['type'] == 'USES'
            assert record['group_id'] == 'test_group'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_reject_if_source_not_exists():
    """Test that creating a relationship fails if source entity doesn't exist."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create target entity only
        await add_entity(
            connection,
            entity_id='test:module1',
            entity_type='Module',
            name='Auth Module',
            group_id='test_group',
        )

        # Try to create relationship with non-existent source
        with pytest.raises(EntityNotFoundError) as exc_info:
            await add_relationship(
                connection,
                source_entity_id='test:nonexistent',
                target_entity_id='test:module1',
                relationship_type='USES',
                group_id='test_group',
            )
        assert 'not found' in str(exc_info.value).lower()
        assert 'test:nonexistent' in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_reject_if_target_not_exists():
    """Test that creating a relationship fails if target entity doesn't exist."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Create source entity only
        await add_entity(
            connection,
            entity_id='test:user1',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )

        # Try to create relationship with non-existent target
        with pytest.raises(EntityNotFoundError) as exc_info:
            await add_relationship(
                connection,
                source_entity_id='test:user1',
                target_entity_id='test:nonexistent',
                relationship_type='USES',
                group_id='test_group',
            )
        assert 'not found' in str(exc_info.value).lower()
        assert 'test:nonexistent' in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_with_properties():
    """Test creating a relationship with optional properties."""
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
        relationship = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            properties={
                'since': '2024-01-01',
                'permission': 'read',
                'weight': 0.8,
            },
            group_id='test_group',
        )

        assert relationship is not None
        assert relationship['properties']['since'] == '2024-01-01'
        assert relationship['properties']['permission'] == 'read'
        assert relationship['properties']['weight'] == 0.8

        # Verify properties in database
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(t:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type
                RETURN r.since as since, r.permission as permission, r.weight as weight
                """,
                source_id='test:user1',
                target_id='test:module1',
                group_id='test_group',
                rel_type='USES',
            )
            record = await result.single()
            assert record is not None
            assert record['since'] == '2024-01-01'
            assert record['permission'] == 'read'
            assert record['weight'] == 0.8


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_with_fact():
    """Test creating a relationship with optional fact (human-readable description)."""
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

        # Create relationship with fact
        fact_text = "John Doe uses Authentication Module for login"
        relationship = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            fact=fact_text,
            group_id='test_group',
        )

        assert relationship is not None
        assert relationship['fact'] == fact_text

        # Verify fact in database
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(t:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type
                RETURN r.fact as fact
                """,
                source_id='test:user1',
                target_id='test:module1',
                group_id='test_group',
                rel_type='USES',
            )
            record = await result.single()
            assert record is not None
            assert record['fact'] == fact_text


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_multiple_relationships_same_entities():
    """Test creating multiple relationships (different types) between same entities."""
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

        # Create first relationship
        rel1 = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='test_group',
        )

        # Create second relationship (different type)
        rel2 = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='OWNS',
            group_id='test_group',
        )

        assert rel1['relationship_type'] == 'USES'
        assert rel2['relationship_type'] == 'OWNS'

        # Verify both relationships exist
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id})-[r]->(t:Entity {entity_id: $target_id, group_id: $group_id})
                RETURN r.relationship_type as type
                ORDER BY type
                """,
                source_id='test:user1',
                target_id='test:module1',
                group_id='test_group',
            )
            records = [record async for record in result]
            assert len(records) == 2
            types = [r['type'] for r in records]
            assert 'USES' in types
            assert 'OWNS' in types


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_group_isolation():
    """Test that relationships are isolated by group_id."""
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
        rel1 = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='group1',
        )

        # Create relationship in group2 (different type)
        rel2 = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='OWNS',
            group_id='group2',
        )

        assert rel1['group_id'] == 'group1'
        assert rel2['group_id'] == 'group2'

        # Verify relationships are isolated
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            # Check group1
            result1 = await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id})-[r]->(t:Entity {entity_id: $target_id, group_id: $group_id})
                RETURN r.relationship_type as type, r.group_id as group_id
                """,
                source_id='test:user1',
                target_id='test:module1',
                group_id='group1',
            )
            record1 = await result1.single()
            assert record1 is not None
            assert record1['type'] == 'USES'
            assert record1['group_id'] == 'group1'

            # Check group2
            result2 = await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id})-[r]->(t:Entity {entity_id: $target_id, group_id: $group_id})
                RETURN r.relationship_type as type, r.group_id as group_id
                """,
                source_id='test:user1',
                target_id='test:module1',
                group_id='group2',
            )
            record2 = await result2.single()
            assert record2 is not None
            assert record2['type'] == 'OWNS'
            assert record2['group_id'] == 'group2'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_idempotent():
    """Test that creating the same relationship multiple times is idempotent (MERGE pattern)."""
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

        # Create relationship first time
        rel1 = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            properties={'since': '2024-01-01'},
            group_id='test_group',
        )

        # Create same relationship again (should update, not duplicate)
        rel2 = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            properties={'since': '2024-01-02'},  # Updated property
            group_id='test_group',
        )

        # Should return the same relationship (updated)
        assert rel1['source_entity_id'] == rel2['source_entity_id']
        assert rel1['target_entity_id'] == rel2['target_entity_id']
        assert rel1['relationship_type'] == rel2['relationship_type']
        assert rel2['properties']['since'] == '2024-01-02'  # Updated value

        # Verify only one relationship exists
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (s:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(t:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type
                RETURN count(r) as count
                """,
                source_id='test:user1',
                target_id='test:module1',
                group_id='test_group',
                rel_type='USES',
            )
            record = await result.single()
            assert record['count'] == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_relationship_performance():
    """Test that relationship creation meets performance target (< 200ms)."""
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
        await add_entity(
            connection,
            entity_id='test:module1',
            entity_type='Module',
            name='Auth Module',
            group_id='test_group',
        )

        # Measure relationship creation time
        start = time.time()
        relationship = await add_relationship(
            connection,
            source_entity_id='test:user1',
            target_entity_id='test:module1',
            relationship_type='USES',
            group_id='test_group',
        )
        elapsed = (time.time() - start) * 1000  # Convert to milliseconds

        assert relationship is not None
        assert elapsed < 200, f"Relationship creation took {elapsed}ms, expected < 200ms"


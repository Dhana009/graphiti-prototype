"""Integration tests for soft delete operations.

These tests verify that soft delete works correctly for entities and relationships,
including filtering, restoration, and querying with include_deleted flag.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity, get_entity_by_id, delete_entity, EntityNotFoundError
from src.relationships import add_relationship, get_entity_relationships


@pytest.fixture(autouse=True)
async def clean_db_for_soft_delete_tests():
    """Fixture to clean up all entities and relationships before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_entity_marks_as_deleted():
    """Test that soft delete entity marks entity as deleted (happy path)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create entity
        await add_entity(
            connection,
            entity_id='test:soft_delete',
            entity_type='TestEntity',
            name='Test Entity',
            group_id='test_group',
        )
        
        # Soft delete entity
        result = await delete_entity(
            connection,
            entity_id='test:soft_delete',
            group_id='test_group',
            hard=False,  # Soft delete
        )
        
        assert result is not None
        assert result['status'] == 'deleted'
        assert result['hard_delete'] is False
        assert 'deleted_at' in result
        
        # Verify entity still exists in database but is marked as deleted
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
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


@pytest.mark.integration
@pytest.mark.asyncio
async def test_soft_delete_relationship_marks_as_deleted():
    """Test that soft delete relationship marks relationship as deleted (happy path)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create entities
        await add_entity(
            connection,
            entity_id='user:john',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='user:jane',
            entity_type='User',
            name='Jane Smith',
            group_id='test_group',
        )
        
        # Create relationship
        relationship = await add_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        assert relationship is not None
        
        # Soft delete relationship (function doesn't exist yet - this test will fail until implemented)
        # TODO: Implement soft_delete_relationship function
        from src.relationships import soft_delete_relationship
        result = await soft_delete_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        assert result is not None
        assert result['status'] == 'deleted'
        assert result['hard_delete'] is False
        assert 'deleted_at' in result
        
        # Verify relationship still exists in database but is marked as deleted
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                RETURN r._deleted as deleted, r.deleted_at as deleted_at
                """,
                source_id='user:john',
                target_id='user:jane',
                rel_type='KNOWS',
                group_id='test_group',
            )
            record = await result.single()
            assert record is not None
            assert record['deleted'] is True
            assert record['deleted_at'] is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queries_automatically_filter_soft_deleted_entities():
    """Test that queries automatically filter out soft-deleted entities."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create entities
        await add_entity(
            connection,
            entity_id='user:active',
            entity_type='User',
            name='Active User',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='user:deleted',
            entity_type='User',
            name='Deleted User',
            group_id='test_group',
        )
        
        # Soft delete one entity
        await delete_entity(
            connection,
            entity_id='user:deleted',
            group_id='test_group',
            hard=False,
        )
        
        # Verify active entity can be retrieved
        active_entity = await get_entity_by_id(
            connection,
            entity_id='user:active',
            group_id='test_group',
        )
        assert active_entity is not None
        assert active_entity['name'] == 'Active User'
        
        # Verify deleted entity cannot be retrieved (filtered out)
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='user:deleted',
                group_id='test_group',
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_queries_automatically_filter_soft_deleted_relationships():
    """Test that queries automatically filter out soft-deleted relationships."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create entities
        await add_entity(
            connection,
            entity_id='user:john',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='user:jane',
            entity_type='User',
            name='Jane Smith',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='user:bob',
            entity_type='User',
            name='Bob Wilson',
            group_id='test_group',
        )
        
        # Create relationships
        await add_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        await add_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:bob',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        # Soft delete one relationship
        from src.relationships import soft_delete_relationship
        await soft_delete_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        # Verify only active relationship is returned
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
        )
        
        # Should only return the active relationship (to bob), not the deleted one (to jane)
        assert len(relationships) == 1
        assert relationships[0]['target_entity_id'] == 'user:bob'
        assert relationships[0]['relationship_type'] == 'KNOWS'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_can_restore_soft_deleted_entity():
    """Test that soft-deleted entities can be restored."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create and soft delete entity
        await add_entity(
            connection,
            entity_id='user:restore',
            entity_type='User',
            name='User to Restore',
            group_id='test_group',
        )
        await delete_entity(
            connection,
            entity_id='user:restore',
            group_id='test_group',
            hard=False,
        )
        
        # Verify entity is deleted
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='user:restore',
                group_id='test_group',
            )
        
        # Restore entity (function doesn't exist yet - this test will fail until implemented)
        from src.entities import restore_entity
        result = await restore_entity(
            connection,
            entity_id='user:restore',
            group_id='test_group',
        )
        
        assert result is not None
        assert result['status'] == 'restored'
        assert result['entity_id'] == 'user:restore'
        
        # Verify entity can be retrieved again
        entity = await get_entity_by_id(
            connection,
            entity_id='user:restore',
            group_id='test_group',
        )
        assert entity is not None
        assert entity['name'] == 'User to Restore'
        
        # Verify _deleted flag is cleared
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (e:Entity {
                    entity_id: $entity_id,
                    group_id: $group_id
                })
                RETURN e._deleted as deleted
                """,
                entity_id='user:restore',
                group_id='test_group',
            )
            record = await result.single()
            assert record is not None
            assert record['deleted'] is False or record['deleted'] is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_can_restore_soft_deleted_relationship():
    """Test that soft-deleted relationships can be restored."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create entities and relationship
        await add_entity(
            connection,
            entity_id='user:john',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='user:jane',
            entity_type='User',
            name='Jane Smith',
            group_id='test_group',
        )
        await add_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        # Soft delete relationship
        from src.relationships import soft_delete_relationship, restore_relationship
        await soft_delete_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        # Verify relationship is filtered out
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
        )
        assert len(relationships) == 0
        
        # Restore relationship
        result = await restore_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        assert result is not None
        assert result['status'] == 'restored'
        
        # Verify relationship can be retrieved again
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
        )
        assert len(relationships) == 1
        assert relationships[0]['target_entity_id'] == 'user:jane'


@pytest.mark.integration
@pytest.mark.asyncio
async def test_can_query_deleted_entities_with_include_deleted_flag():
    """Test that deleted entities can be queried with include_deleted flag."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create and soft delete entity
        await add_entity(
            connection,
            entity_id='user:deleted',
            entity_type='User',
            name='Deleted User',
            group_id='test_group',
        )
        await delete_entity(
            connection,
            entity_id='user:deleted',
            group_id='test_group',
            hard=False,
        )
        
        # Verify normal query doesn't return deleted entity
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='user:deleted',
                group_id='test_group',
            )
        
        # Query with include_deleted flag (functionality doesn't exist yet - this test will fail until implemented)
        # This will need to be updated to support include_deleted parameter
        entity = await get_entity_by_id(
            connection,
            entity_id='user:deleted',
            group_id='test_group',
            include_deleted=True,  # This parameter doesn't exist yet
        )
        
        assert entity is not None
        assert entity['name'] == 'Deleted User'
        assert entity.get('_deleted') is True
        assert 'deleted_at' in entity


@pytest.mark.integration
@pytest.mark.asyncio
async def test_can_query_deleted_relationships_with_include_deleted_flag():
    """Test that deleted relationships can be queried with include_deleted flag."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create entities and relationship
        await add_entity(
            connection,
            entity_id='user:john',
            entity_type='User',
            name='John Doe',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='user:jane',
            entity_type='User',
            name='Jane Smith',
            group_id='test_group',
        )
        await add_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        # Soft delete relationship
        from src.relationships import soft_delete_relationship
        await soft_delete_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        # Verify normal query doesn't return deleted relationship
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
        )
        assert len(relationships) == 0
        
        # Query with include_deleted flag (functionality doesn't exist yet - this test will fail until implemented)
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
            include_deleted=True,  # This parameter doesn't exist yet
        )
        
        assert len(relationships) == 1
        assert relationships[0]['target_entity_id'] == 'user:jane'
        assert relationships[0].get('_deleted') is True
        assert 'deleted_at' in relationships[0]


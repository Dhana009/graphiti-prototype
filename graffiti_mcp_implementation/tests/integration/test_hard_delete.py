"""Integration tests for hard delete operations.

These tests verify that hard delete works correctly for entities and relationships,
including permanent removal, cascade deletion, and that hard-deleted items cannot be restored.
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity, get_entity_by_id, delete_entity, restore_entity, EntityNotFoundError
from src.relationships import add_relationship, get_entity_relationships, soft_delete_relationship, restore_relationship


@pytest.fixture(autouse=True)
async def clean_db_for_hard_delete_tests():
    """Fixture to clean up all entities and relationships before each test."""
    async with DatabaseConnection() as conn:
        await initialize_database(conn)
        driver = conn.get_driver()
        async with driver.session(database=conn.database) as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hard_delete_entity_permanently_removes():
    """Test that hard delete entity permanently removes it from database (happy path)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create entity
        await add_entity(
            connection,
            entity_id='test:hard_delete',
            entity_type='TestEntity',
            name='Test Entity',
            properties={'email': 'test@example.com'},
            group_id='test_group',
        )
        
        # Hard delete entity
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
        async with driver.session(database=connection.database) as session:
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
        
        # Verify get_entity_by_id raises error (even with include_deleted=True)
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='test:hard_delete',
                group_id='test_group',
            )
        
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='test:hard_delete',
                group_id='test_group',
                include_deleted=True,
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hard_delete_relationship_permanently_removes():
    """Test that hard delete relationship permanently removes it from database (happy path)."""
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
        
        # Hard delete relationship (function doesn't exist yet - this test will fail until implemented)
        # TODO: Implement hard_delete_relationship function
        from src.relationships import hard_delete_relationship
        result = await hard_delete_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        
        assert result is not None
        assert result['status'] == 'deleted'
        assert result['hard_delete'] is True
        
        # Verify relationship is completely removed from database
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            result = await session.run(
                """
                MATCH (source:Entity {entity_id: $source_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $target_id, group_id: $group_id})
                WHERE r.relationship_type = $rel_type AND r.group_id = $group_id
                RETURN r
                """,
                source_id='user:john',
                target_id='user:jane',
                rel_type='KNOWS',
                group_id='test_group',
            )
            record = await result.single()
            assert record is None
        
        # Verify relationship is not returned by get_entity_relationships (even with include_deleted=True)
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
        )
        assert len(relationships) == 0
        
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
            include_deleted=True,
        )
        assert len(relationships) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hard_delete_entity_cascade_removes_all_relationships():
    """Test that hard delete entity cascade removes all its relationships (feature)."""
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
        
        # Create multiple relationships from john
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
        await add_relationship(
            connection,
            source_entity_id='user:jane',
            target_entity_id='user:john',
            relationship_type='LIKES',
            group_id='test_group',
        )
        
        # Verify relationships exist
        john_relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='both',
            group_id='test_group',
        )
        assert len(john_relationships) == 3  # 2 outgoing, 1 incoming
        
        # Hard delete john entity
        result = await delete_entity(
            connection,
            entity_id='user:john',
            group_id='test_group',
            hard=True,
        )
        assert result['status'] == 'deleted'
        assert result['hard_delete'] is True
        
        # Verify all relationships involving john are removed
        driver = connection.get_driver()
        async with driver.session(database=connection.database) as session:
            # Check outgoing relationships
            result = await session.run(
                """
                MATCH (source:Entity {entity_id: $entity_id, group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {group_id: $group_id})
                RETURN count(r) as count
                """,
                entity_id='user:john',
                group_id='test_group',
            )
            record = await result.single()
            assert record['count'] == 0
            
            # Check incoming relationships
            result = await session.run(
                """
                MATCH (source:Entity {group_id: $group_id})-[r:RELATIONSHIP]->(target:Entity {entity_id: $entity_id, group_id: $group_id})
                RETURN count(r) as count
                """,
                entity_id='user:john',
                group_id='test_group',
            )
            record = await result.single()
            assert record['count'] == 0
        
        # Verify other entities still exist
        jane = await get_entity_by_id(
            connection,
            entity_id='user:jane',
            group_id='test_group',
        )
        assert jane is not None
        
        bob = await get_entity_by_id(
            connection,
            entity_id='user:bob',
            group_id='test_group',
        )
        assert bob is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cannot_restore_hard_deleted_entity():
    """Test that hard-deleted entities cannot be restored (feature)."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create and hard delete entity
        await add_entity(
            connection,
            entity_id='user:hard_deleted',
            entity_type='User',
            name='Hard Deleted User',
            group_id='test_group',
        )
        
        result = await delete_entity(
            connection,
            entity_id='user:hard_deleted',
            group_id='test_group',
            hard=True,
        )
        assert result['hard_delete'] is True
        
        # Attempt to restore hard-deleted entity (should fail)
        with pytest.raises(EntityNotFoundError):
            await restore_entity(
                connection,
                entity_id='user:hard_deleted',
                group_id='test_group',
            )
        
        # Verify entity still doesn't exist
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='user:hard_deleted',
                group_id='test_group',
                include_deleted=True,
            )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cannot_restore_hard_deleted_relationship():
    """Test that hard-deleted relationships cannot be restored (feature)."""
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
        
        # Hard delete relationship
        from src.relationships import hard_delete_relationship
        result = await hard_delete_relationship(
            connection,
            source_entity_id='user:john',
            target_entity_id='user:jane',
            relationship_type='KNOWS',
            group_id='test_group',
        )
        assert result['hard_delete'] is True
        
        # Attempt to restore hard-deleted relationship (should fail)
        from src.relationships import RelationshipError
        with pytest.raises(RelationshipError):
            await restore_relationship(
                connection,
                source_entity_id='user:john',
                target_entity_id='user:jane',
                relationship_type='KNOWS',
                group_id='test_group',
            )
        
        # Verify relationship still doesn't exist
        relationships = await get_entity_relationships(
            connection,
            entity_id='user:john',
            direction='outgoing',
            group_id='test_group',
            include_deleted=True,
        )
        assert len(relationships) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_hard_delete_vs_soft_delete_entity():
    """Test that hard delete and soft delete behave differently."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)
        
        # Create two entities
        await add_entity(
            connection,
            entity_id='user:soft_deleted',
            entity_type='User',
            name='Soft Deleted User',
            group_id='test_group',
        )
        await add_entity(
            connection,
            entity_id='user:hard_deleted',
            entity_type='User',
            name='Hard Deleted User',
            group_id='test_group',
        )
        
        # Soft delete one
        soft_result = await delete_entity(
            connection,
            entity_id='user:soft_deleted',
            group_id='test_group',
            hard=False,
        )
        assert soft_result['hard_delete'] is False
        
        # Hard delete the other
        hard_result = await delete_entity(
            connection,
            entity_id='user:hard_deleted',
            group_id='test_group',
            hard=True,
        )
        assert hard_result['hard_delete'] is True
        
        # Verify soft-deleted entity can be retrieved with include_deleted=True
        soft_entity = await get_entity_by_id(
            connection,
            entity_id='user:soft_deleted',
            group_id='test_group',
            include_deleted=True,
        )
        assert soft_entity is not None
        assert soft_entity['_deleted'] is True
        
        # Verify soft-deleted entity can be restored
        restore_result = await restore_entity(
            connection,
            entity_id='user:soft_deleted',
            group_id='test_group',
        )
        assert restore_result['status'] == 'restored'
        
        # Verify hard-deleted entity cannot be retrieved even with include_deleted=True
        with pytest.raises(EntityNotFoundError):
            await get_entity_by_id(
                connection,
                entity_id='user:hard_deleted',
                group_id='test_group',
                include_deleted=True,
            )
        
        # Verify hard-deleted entity cannot be restored
        with pytest.raises(EntityNotFoundError):
            await restore_entity(
                connection,
                entity_id='user:hard_deleted',
                group_id='test_group',
            )


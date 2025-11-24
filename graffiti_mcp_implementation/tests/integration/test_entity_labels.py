"""Integration tests for entity labels.

These tests verify that entities are created with correct labels
(entity_type as both label and property).
"""

import pytest
from src.database import DatabaseConnection, initialize_database
from src.entities import add_entity


@pytest.mark.integration
@pytest.mark.asyncio
async def test_entity_has_entity_type_label():
    """Test that entity is created with entity_type as a label."""
    async with DatabaseConnection() as connection:
        await initialize_database(connection)

        # Clean up
        driver = connection.get_driver()
        async with driver.session() as session:
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:label_check'}) DELETE e")

            await session.execute_write(cleanup)

        # Create entity
        entity = await add_entity(
            connection,
            entity_id='test:label_check',
            entity_type='User',
            name='Test User',
            group_id='test_group',
        )

        assert entity is not None

        # Verify entity has both Entity and User labels
        async with driver.session() as session2:
            async def check_labels(tx):
                result = await tx.run(
                    """
                    MATCH (e:Entity {entity_id: 'test:label_check'})
                    RETURN labels(e) as labels, e.entity_type as entity_type
                    """
                )
                return await result.single()

            record = await session2.execute_read(check_labels)
            assert record is not None
            labels = record['labels']
            assert 'Entity' in labels
            # The entity_type should be sanitized and used as a label
            # 'User' should become 'User' label
            assert 'User' in labels or 'user' in labels
            assert record['entity_type'] == 'User'

            # Clean up
            async def cleanup(tx):
                await tx.run("MATCH (e:Entity {entity_id: 'test:label_check'}) DELETE e")

            await session2.execute_write(cleanup)


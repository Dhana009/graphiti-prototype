"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

try:
    from neo4j.exceptions import ClientError
    from neo4j import EagerResult
    from graphiti_core.driver.neo4j_driver import Neo4jDriver

    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    Neo4jDriver = None
    EagerResult = None


@pytest.mark.skipif(not HAS_NEO4J, reason='Neo4j driver is not available')
class TestNeo4jDriverErrorHandling:
    """Test suite for Neo4j driver error handling, specifically index creation errors."""

    @pytest.fixture
    def mock_neo4j_client(self):
        """Create a mock Neo4j client."""
        mock_client = MagicMock()
        mock_client.execute_query = AsyncMock()
        return mock_client

    @pytest.fixture
    def neo4j_driver(self, mock_neo4j_client):
        """Create a Neo4jDriver instance with mocked client."""
        driver = Neo4jDriver(uri='bolt://localhost:7687', user='neo4j', password='test')
        driver.client = mock_neo4j_client
        return driver

    @pytest.mark.asyncio
    async def test_execute_query_handles_equivalent_schema_rule_already_exists(
        self, neo4j_driver, mock_neo4j_client
    ):
        """
        Test that EquivalentSchemaRuleAlreadyExists errors are handled gracefully.
        
        When creating an index that already exists, Neo4j throws this error.
        The driver should catch it and return an empty result instead of raising.
        """
        # Simulate the Neo4j error for equivalent index already existing
        error = ClientError(
            'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists',
            'An equivalent index already exists, \'Index( id=12, name=\'relation_uuid\', '
            'type=\'RANGE\', schema=()-[:RELATES_TO {uuid}]-(), indexProvider=\'range-1.0\' )\'.'
        )
        
        mock_neo4j_client.execute_query.side_effect = error
        
        # Execute a query that would create an index
        result = await neo4j_driver.execute_query(
            'CREATE INDEX relation_uuid FOR ()-[r:RELATES_TO]-() ON (r.uuid)'
        )
        
        # Should return an empty result instead of raising
        assert isinstance(result, EagerResult)
        assert result.records == []
        assert result.keys == []
        assert result.summary is None

    @pytest.mark.asyncio
    async def test_execute_query_handles_equivalent_schema_rule_in_error_string(
        self, neo4j_driver, mock_neo4j_client
    ):
        """
        Test that errors containing 'EquivalentSchemaRuleAlreadyExists' in the string are handled.
        
        Some Neo4j error formats may have the error type in the string representation.
        """
        # Create a generic exception with the error string in it
        error = Exception(
            'Neo.ClientError.Schema.EquivalentSchemaRuleAlreadyExists: '
            'An equivalent index already exists'
        )
        
        mock_neo4j_client.execute_query.side_effect = error
        
        result = await neo4j_driver.execute_query(
            'CREATE INDEX entity_uuid FOR (e:Entity) ON (e.uuid)'
        )
        
        # Should return an empty result instead of raising
        assert isinstance(result, EagerResult)
        assert result.records == []
        assert result.keys == []
        assert result.summary is None

    @pytest.mark.asyncio
    async def test_execute_query_propagates_other_errors(
        self, neo4j_driver, mock_neo4j_client
    ):
        """
        Test that other errors are still propagated normally.
        
        Only EquivalentSchemaRuleAlreadyExists should be caught and handled.
        Other errors should be raised as normal.
        """
        # Create a different error
        error = ClientError(
            'Neo.ClientError.Statement.SyntaxError',
            'Invalid syntax in query'
        )
        
        mock_neo4j_client.execute_query.side_effect = error
        
        # Should raise the error
        with pytest.raises(ClientError) as exc_info:
            await neo4j_driver.execute_query('INVALID CYPHER QUERY')
        
        assert 'SyntaxError' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_query_successful_query_returns_result(
        self, neo4j_driver, mock_neo4j_client
    ):
        """Test that successful queries return results normally."""
        # Mock a successful query result
        mock_result = EagerResult(
            records=[{'name': 'test'}],
            keys=['name'],
            summary=None
        )
        mock_neo4j_client.execute_query.return_value = mock_result
        
        result = await neo4j_driver.execute_query('MATCH (n) RETURN n.name AS name LIMIT 1')
        
        # Should return the result normally
        assert result == mock_result
        assert len(result.records) == 1
        assert result.records[0]['name'] == 'test'


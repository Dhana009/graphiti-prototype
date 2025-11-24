"""
Pytest configuration and shared fixtures
"""

import pytest
from typing import Generator, Optional
import os
from pathlib import Path


@pytest.fixture(scope="session")
def neo4j_uri() -> str:
    """Get Neo4j connection URI from environment or use default."""
    return os.getenv("NEO4J_URI", "bolt://localhost:7687")


@pytest.fixture(scope="session")
def neo4j_user() -> str:
    """Get Neo4j username from environment or use default."""
    return os.getenv("NEO4J_USER", "neo4j")


@pytest.fixture(scope="session")
def neo4j_password() -> str:
    """Get Neo4j password from environment or use default."""
    # Default matches docker-compose.yml configuration
    return os.getenv("NEO4J_PASSWORD", "testpassword")


@pytest.fixture(scope="session")
def test_group_id() -> str:
    """Get test group_id for isolating test data."""
    return os.getenv("TEST_GROUP_ID", "test_group")


@pytest.fixture(autouse=True, scope="function")
async def clean_test_data_fixture():
    """
    Fixture to clean up all nodes and relationships before and after each test.
    This ensures tests don't interfere with each other.
    """
    # Cleanup before test (in case previous test failed)
    from src.database import DatabaseConnection
    async with DatabaseConnection() as conn:
        driver = conn.get_driver()
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
    yield
    # Cleanup after test
    async with DatabaseConnection() as conn:
        driver = conn.get_driver()
        async with driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def src_root(project_root: Path) -> Path:
    """Get the source code root directory."""
    return project_root / "src"


"""Configuration management for Graffiti Graph MCP server.

This module handles loading and validating configuration from environment variables.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Try to load .env from parent directory (graphiti/) if it exists
_PARENT_ENV_FILE = Path(__file__).parent.parent.parent / '.env'
if _PARENT_ENV_FILE.exists():
    # Load environment variables from parent .env file
    from dotenv import load_dotenv
    load_dotenv(_PARENT_ENV_FILE)


class Neo4jConfig(BaseSettings):
    """Neo4j database configuration."""

    uri: str = 'bolt://localhost:7687'
    user: str = 'neo4j'
    password: str = 'testpassword'
    database: str = 'neo4j'

    model_config = SettingsConfigDict(
        env_prefix='NEO4J_',
        case_sensitive=False,
        extra='ignore',
    )

    def __init__(self, **kwargs):
        """Initialize Neo4j configuration with environment variable support."""
        # Set defaults from environment variables if not provided in kwargs
        defaults = {
            'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            'user': os.getenv('NEO4J_USER', 'neo4j'),
            'password': os.getenv('NEO4J_PASSWORD', 'testpassword'),
            'database': os.getenv('NEO4J_DATABASE', 'neo4j'),
        }

        # Merge defaults with kwargs (kwargs take precedence)
        merged_kwargs = {**defaults, **kwargs}
        super().__init__(**merged_kwargs)


def get_neo4j_config() -> Neo4jConfig:
    """Get Neo4j configuration from environment variables.

    Returns:
        Neo4jConfig: Configuration object with Neo4j connection settings.

    Example:
        >>> config = get_neo4j_config()
        >>> print(config.uri)
        bolt://localhost:7687
    """
    return Neo4jConfig()


class OpenAIConfig(BaseSettings):
    """OpenAI API configuration for embeddings and LLM operations."""

    api_key: Optional[str] = None
    organization: Optional[str] = None
    model: str = 'text-embedding-3-small'  # Default embedding model
    llm_model: str = 'gpt-5-nano'  # Default LLM model for extraction (reasoning model)
    embedding_dimension: int = 1536  # Dimension for text-embedding-3-small

    model_config = SettingsConfigDict(
        env_prefix='OPENAI_',
        case_sensitive=False,
        extra='ignore',
        env_file='.env',  # Load from .env file if present
        env_file_encoding='utf-8',
    )

    def __init__(self, **kwargs):
        """Initialize OpenAI configuration with environment variable support."""
        defaults = {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'organization': os.getenv('OPENAI_ORGANIZATION'),
            'model': os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small'),
            # Support gpt-5-nano, gpt-5o-mini, or fallback to gpt-4o-mini
            'llm_model': os.getenv('OPENAI_LLM_MODEL', os.getenv('OPENAI_MODEL', 'gpt-5-nano')),
            'embedding_dimension': int(os.getenv('OPENAI_EMBEDDING_DIMENSION', '1536')),
        }
        merged_kwargs = {**defaults, **kwargs}
        super().__init__(**merged_kwargs)


def get_openai_config() -> OpenAIConfig:
    """Get OpenAI configuration from environment variables.

    Returns:
        OpenAIConfig: Configuration object with OpenAI API settings.

    Example:
        >>> config = get_openai_config()
        >>> print(config.model)
        text-embedding-3-small
    """
    return OpenAIConfig()


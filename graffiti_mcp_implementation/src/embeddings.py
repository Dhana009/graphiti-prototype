"""Embedding generation and management for Graffiti Graph.

This module provides functions for generating and storing embeddings
for entities to enable semantic search.
"""

import logging
from typing import List, Optional
import numpy as np
from openai import OpenAI

from .config import get_openai_config

logger = logging.getLogger(__name__)


def generate_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """Generate embedding for text using OpenAI API.

    Args:
        text: Text to generate embedding for (required)
        model: Optional OpenAI embedding model (defaults to config model)

    Returns:
        List[float]: Embedding vector (list of floats)

    Raises:
        RuntimeError: If OpenAI API key is not configured
        ValueError: If text is empty
        Exception: If OpenAI API call fails

    Example:
        >>> embedding = generate_embedding("Authentication module for user login")
        >>> print(len(embedding))
        1536
    """
    if not text or not text.strip():
        raise ValueError('text must be a non-empty string')

    openai_config = get_openai_config()
    if not openai_config.api_key:
        raise RuntimeError('OpenAI API key not configured. Set OPENAI_API_KEY environment variable.')

    model = model or openai_config.model

    try:
        client = OpenAI(api_key=openai_config.api_key)
        response = client.embeddings.create(
            model=model,
            input=text.strip(),
        )
        embedding = response.data[0].embedding
        logger.debug(f"Generated embedding for text (length: {len(text)}, model: {model})")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise


def generate_entity_embedding(name: str, summary: Optional[str] = None) -> List[float]:
    """Generate embedding for an entity based on its name and summary.

    Combines entity name and summary into a single text for embedding generation.
    This ensures semantic search can match entities based on both their name
    and description.

    Args:
        name: Entity name (required)
        summary: Optional entity summary/description

    Returns:
        List[float]: Embedding vector for the entity

    Raises:
        ValueError: If name is empty
        RuntimeError: If OpenAI API key is not configured

    Example:
        >>> embedding = generate_entity_embedding(
        ...     name="Authentication Module",
        ...     summary="Handles user authentication and login"
        ... )
        >>> print(len(embedding))
        1536
    """
    if not name or not name.strip():
        raise ValueError('name must be a non-empty string')

    # Combine name and summary for embedding
    text_parts = [name.strip()]
    if summary and summary.strip():
        text_parts.append(summary.strip())

    combined_text = ' '.join(text_parts)
    return generate_embedding(combined_text)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two embedding vectors.

    Args:
        vec1: First embedding vector
        vec2: Second embedding vector

    Returns:
        float: Cosine similarity score between 0.0 and 1.0

    Raises:
        ValueError: If vectors have different lengths or are empty

    Example:
        >>> vec1 = [0.1, 0.2, 0.3]
        >>> vec2 = [0.2, 0.3, 0.4]
        >>> similarity = cosine_similarity(vec1, vec2)
        >>> print(f"{similarity:.3f}")
        0.992
    """
    if not vec1 or not vec2:
        raise ValueError('Vectors cannot be empty')

    if len(vec1) != len(vec2):
        raise ValueError(f'Vectors must have same length, got {len(vec1)} and {len(vec2)}')

    vec1_array = np.array(vec1)
    vec2_array = np.array(vec2)

    dot_product = np.dot(vec1_array, vec2_array)
    norm1 = np.linalg.norm(vec1_array)
    norm2 = np.linalg.norm(vec2_array)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    similarity = dot_product / (norm1 * norm2)
    # Ensure result is between 0.0 and 1.0 (cosine similarity range)
    return float(max(0.0, min(1.0, similarity)))


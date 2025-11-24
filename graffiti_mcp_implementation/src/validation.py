"""Input validation for Graffiti Graph entities and relationships.

This module provides validation functions for entity and relationship
data before database operations.
"""

from typing import Dict, Any, Optional


# Validation limits based on implementation decisions
MAX_PROPERTIES = 50
MAX_KEY_LENGTH = 255
MAX_VALUE_LENGTH = 10000


def validate_entity_id(entity_id: Optional[str]) -> str:
    """Validate entity_id.

    Args:
        entity_id: The entity ID to validate

    Returns:
        str: The validated and trimmed entity_id

    Raises:
        ValueError: If entity_id is None or empty
        TypeError: If entity_id is not a string

    Example:
        >>> validate_entity_id('user:john_doe')
        'user:john_doe'
        >>> validate_entity_id('  module:auth  ')
        'module:auth'
    """
    if entity_id is None:
        raise ValueError('entity_id is required')
    if not isinstance(entity_id, str):
        raise TypeError(f'entity_id must be a string, got {type(entity_id)}')
    if not entity_id.strip():
        raise ValueError('entity_id cannot be empty')
    return entity_id.strip()


def validate_entity_type(entity_type: Optional[str]) -> str:
    """Validate entity_type.

    Args:
        entity_type: The entity type to validate

    Returns:
        str: The validated and trimmed entity_type

    Raises:
        ValueError: If entity_type is None or empty
        TypeError: If entity_type is not a string

    Example:
        >>> validate_entity_type('User')
        'User'
        >>> validate_entity_type('  Module  ')
        'Module'
    """
    if entity_type is None:
        raise ValueError('entity_type is required')
    if not isinstance(entity_type, str):
        raise TypeError(f'entity_type must be a string, got {type(entity_type)}')
    if not entity_type.strip():
        raise ValueError('entity_type cannot be empty')
    return entity_type.strip()


def validate_name(name: Optional[str]) -> str:
    """Validate name.

    Args:
        name: The name to validate

    Returns:
        str: The validated and trimmed name

    Raises:
        ValueError: If name is None or empty
        TypeError: If name is not a string

    Example:
        >>> validate_name('John Doe')
        'John Doe'
        >>> validate_name('  Test Entity  ')
        'Test Entity'
    """
    if name is None:
        raise ValueError('name is required')
    if not isinstance(name, str):
        raise TypeError(f'name must be a string, got {type(name)}')
    if not name.strip():
        raise ValueError('name cannot be empty')
    return name.strip()


def validate_properties(properties: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate properties dictionary.

    Properties must be simple key-value pairs where:
    - Keys are strings (max 255 characters)
    - Values are string, number, boolean, or null
    - Maximum 50 properties per entity/relationship

    Args:
        properties: The properties dictionary to validate

    Returns:
        Dict[str, Any]: The validated properties dictionary

    Raises:
        TypeError: If properties is not a dict or contains invalid types
        ValueError: If properties exceed limits or contain invalid values

    Example:
        >>> validate_properties({'email': 'test@example.com', 'age': 30})
        {'email': 'test@example.com', 'age': 30}
        >>> validate_properties(None)
        {}
    """
    if properties is None:
        return {}

    if not isinstance(properties, dict):
        raise TypeError('properties must be a dictionary')

    if len(properties) > MAX_PROPERTIES:
        raise ValueError(
            f'Maximum {MAX_PROPERTIES} properties allowed, got {len(properties)}'
        )

    validated = {}
    for key, value in properties.items():
        # Validate key
        if not isinstance(key, str):
            raise TypeError(f'Property key must be string, got {type(key)}')
        if len(key) > MAX_KEY_LENGTH:
            raise ValueError(
                f'Property key too long: {len(key)} > {MAX_KEY_LENGTH}'
            )
        if not key.strip():
            raise ValueError('Property key cannot be empty')

        # Validate value
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise TypeError(
                f'Property value must be string|number|boolean|null, '
                f'got {type(value)} for key \'{key}\''
            )

        if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
            raise ValueError(
                f'Property value too long for key \'{key}\': '
                f'{len(value)} > {MAX_VALUE_LENGTH}'
            )

        validated[key.strip()] = value

    return validated


def validate_group_id(group_id: Optional[str]) -> str:
    """Validate and normalize group_id.

    Args:
        group_id: The group ID to validate

    Returns:
        str: The validated and normalized group_id (defaults to 'default')

    Raises:
        ValueError: If group_id is reserved or invalid

    Example:
        >>> validate_group_id('my_group')
        'my_group'
        >>> validate_group_id(None)
        'default'
        >>> validate_group_id('  TEST_GROUP  ')
        'test_group'
    """
    # Reserved group IDs (case-insensitive)
    RESERVED_GROUP_IDS = {
        'default',
        'global',
        'system',
        'admin',
        '_system_',
        '_internal_',
        '_admin_',
    }

    if group_id is None:
        return 'default'

    if not isinstance(group_id, str):
        raise TypeError(f'group_id must be a string, got {type(group_id)}')

    normalized = group_id.lower().strip()

    # Check for reserved names
    if normalized in RESERVED_GROUP_IDS:
        raise ValueError(f"Group ID '{group_id}' is reserved")

    # Check for reserved prefixes
    if normalized.startswith('_system_') or normalized.startswith('_internal_') or normalized.startswith('_admin_'):
        raise ValueError(f"Group ID '{group_id}' uses reserved prefix")

    if not normalized:
        return 'default'

    return normalized


def validate_relationship_type(relationship_type: Optional[str]) -> str:
    """Validate relationship_type.

    Args:
        relationship_type: The relationship type to validate

    Returns:
        str: The validated and trimmed relationship_type

    Raises:
        ValueError: If relationship_type is None or empty
        TypeError: If relationship_type is not a string

    Example:
        >>> validate_relationship_type('USES')
        'USES'
        >>> validate_relationship_type('  DEPENDS_ON  ')
        'DEPENDS_ON'
    """
    if relationship_type is None:
        raise ValueError('relationship_type is required')
    if not isinstance(relationship_type, str):
        raise TypeError(f'relationship_type must be a string, got {type(relationship_type)}')
    if not relationship_type.strip():
        raise ValueError('relationship_type cannot be empty')
    return relationship_type.strip()


def validate_relationship_input(
    source_entity_id: Optional[str],
    target_entity_id: Optional[str],
    relationship_type: Optional[str],
    properties: Optional[Dict[str, Any]] = None,
) -> tuple[str, str, str, Optional[Dict[str, Any]]]:
    """Validate all relationship input fields.

    Args:
        source_entity_id: Source entity ID (required)
        target_entity_id: Target entity ID (required)
        relationship_type: Relationship type (required)
        properties: Optional relationship properties

    Returns:
        tuple: (validated_source_id, validated_target_id, validated_type, validated_properties)

    Raises:
        ValueError: If any required field is invalid
        TypeError: If any field has wrong type

    Example:
        >>> validate_relationship_input('user:1', 'module:1', 'USES', {'since': '2024-01-01'})
        ('user:1', 'module:1', 'USES', {'since': '2024-01-01'})
    """
    validated_source_id = validate_entity_id(source_entity_id)
    validated_target_id = validate_entity_id(target_entity_id)
    validated_type = validate_relationship_type(relationship_type)
    validated_properties = validate_properties(properties) if properties is not None else None

    return (validated_source_id, validated_target_id, validated_type, validated_properties)


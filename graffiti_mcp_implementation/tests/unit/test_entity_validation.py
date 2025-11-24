"""Unit tests for entity validation.

These tests verify input validation for entity creation without
requiring a database connection.
"""

import pytest
from src.validation import (
    validate_entity_id,
    validate_entity_type,
    validate_name,
    validate_properties,
    validate_group_id,
)


def test_validate_entity_id_valid():
    """Validate entity_id (placeholder - will be implemented)."""
    if entity_id is None:
        raise ValueError("entity_id is required")
    if not isinstance(entity_id, str):
        raise TypeError(f"entity_id must be a string, got {type(entity_id)}")
    if not entity_id.strip():
        raise ValueError("entity_id cannot be empty")
    return entity_id.strip()




def test_validate_entity_id_valid():
    """Test validating valid entity_id."""
    assert validate_entity_id('user:john_doe') == 'user:john_doe'
    assert validate_entity_id('  module:auth  ') == 'module:auth'


def test_validate_entity_id_none():
    """Test that None entity_id raises ValueError."""
    with pytest.raises(ValueError, match='entity_id is required'):
        validate_entity_id(None)


def test_validate_entity_id_empty():
    """Test that empty entity_id raises ValueError."""
    with pytest.raises(ValueError, match='entity_id cannot be empty'):
        validate_entity_id('')
    with pytest.raises(ValueError, match='entity_id cannot be empty'):
        validate_entity_id('   ')


def test_validate_entity_id_wrong_type():
    """Test that non-string entity_id raises TypeError."""
    with pytest.raises(TypeError, match='entity_id must be a string'):
        validate_entity_id(123)
    with pytest.raises(TypeError, match='entity_id must be a string'):
        validate_entity_id(['user:john'])


def test_validate_entity_type_valid():
    """Test validating valid entity_type."""
    assert validate_entity_type('User') == 'User'
    assert validate_entity_type('  Module  ') == 'Module'


def test_validate_entity_type_none():
    """Test that None entity_type raises ValueError."""
    with pytest.raises(ValueError, match='entity_type is required'):
        validate_entity_type(None)


def test_validate_name_valid():
    """Test validating valid name."""
    assert validate_name('John Doe') == 'John Doe'
    assert validate_name('  Test Entity  ') == 'Test Entity'


def test_validate_name_none():
    """Test that None name raises ValueError."""
    with pytest.raises(ValueError, match='name is required'):
        validate_name(None)


def test_validate_properties_valid():
    """Test validating valid properties."""
    props = {
        'email': 'test@example.com',
        'age': 30,
        'active': True,
        'score': 95.5,
        'metadata': None,
    }
    result = validate_properties(props)
    assert result == props


def test_validate_properties_none():
    """Test that None properties returns empty dict."""
    assert validate_properties(None) == {}


def test_validate_properties_empty():
    """Test that empty properties dict is valid."""
    assert validate_properties({}) == {}


def test_validate_properties_not_dict():
    """Test that non-dict properties raises TypeError."""
    with pytest.raises(TypeError, match='properties must be a dictionary'):
        validate_properties('not a dict')
    with pytest.raises(TypeError, match='properties must be a dictionary'):
        validate_properties(['list', 'not', 'dict'])


def test_validate_properties_too_many():
    """Test that more than 50 properties raises ValueError."""
    props = {f'key{i}': f'value{i}' for i in range(51)}
    with pytest.raises(ValueError, match='Maximum 50 properties allowed'):
        validate_properties(props)


def test_validate_properties_invalid_value_type():
    """Test that invalid property value types raise TypeError."""
    with pytest.raises(TypeError, match='Property value must be string|number|boolean|null'):
        validate_properties({'nested': {'object': 'not allowed'}})

    with pytest.raises(TypeError, match='Property value must be string|number|boolean|null'):
        validate_properties({'array': [1, 2, 3]})

    with pytest.raises(TypeError, match='Property value must be string|number|boolean|null'):
        validate_properties({'date': object()})


def test_validate_properties_invalid_key_type():
    """Test that non-string property keys raise TypeError."""
    with pytest.raises(TypeError, match='Property key must be string'):
        validate_properties({123: 'value'})

    with pytest.raises(TypeError, match='Property key must be string'):
        validate_properties({('tuple', 'key'): 'value'})


def test_validate_properties_key_too_long():
    """Test that property keys longer than 255 characters raise ValueError."""
    long_key = 'a' * 256
    with pytest.raises(ValueError, match='Property key too long'):
        validate_properties({long_key: 'value'})


def test_validate_properties_value_too_long():
    """Test that string property values longer than 10000 characters raise ValueError."""
    long_value = 'a' * 10001
    with pytest.raises(ValueError, match='Property value too long'):
        validate_properties({'key': long_value})


def test_validate_properties_empty_key():
    """Test that empty property keys raise ValueError."""
    with pytest.raises(ValueError, match='Property key cannot be empty'):
        validate_properties({'': 'value'})
    with pytest.raises(ValueError, match='Property key cannot be empty'):
        validate_properties({'   ': 'value'})


def test_validate_group_id_valid():
    """Test validating valid group_id."""
    assert validate_group_id('my_group') == 'my_group'
    assert validate_group_id('  TEST_GROUP  ') == 'test_group'
    assert validate_group_id('group123') == 'group123'


def test_validate_group_id_none():
    """Test that None group_id returns 'default'."""
    assert validate_group_id(None) == 'default'


def test_validate_group_id_empty():
    """Test that empty group_id returns 'default'."""
    assert validate_group_id('') == 'default'
    assert validate_group_id('   ') == 'default'


def test_validate_group_id_reserved():
    """Test that reserved group_ids raise ValueError."""
    reserved = ['default', 'global', 'system', 'admin']
    for reserved_id in reserved:
        with pytest.raises(ValueError, match='is reserved'):
            validate_group_id(reserved_id)
        # Case-insensitive
        with pytest.raises(ValueError, match='is reserved'):
            validate_group_id(reserved_id.upper())


def test_validate_group_id_reserved_prefix():
    """Test that reserved prefixes raise ValueError."""
    reserved_prefixes = ['_system_', '_internal_', '_admin_']
    for prefix in reserved_prefixes:
        with pytest.raises(ValueError, match='uses reserved prefix'):
            validate_group_id(f'{prefix}something')
        # Case-insensitive
        with pytest.raises(ValueError, match='uses reserved prefix'):
            validate_group_id(f'{prefix.upper()}something')


def test_validate_group_id_wrong_type():
    """Test that non-string group_id raises TypeError."""
    with pytest.raises(TypeError, match='group_id must be a string'):
        validate_group_id(123)
    with pytest.raises(TypeError, match='group_id must be a string'):
        validate_group_id(['group'])


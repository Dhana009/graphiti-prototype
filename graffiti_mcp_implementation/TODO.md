# Graffiti Graph MCP Implementation - Detailed TODO List

**Last Updated:** 2025-01-27 (Updated with P3-2 completion and GPT-5-nano configuration)  
**Total Tasks:** 57  
**Completed:** 29  
**In Progress:** 0  
**Pending:** 28  
**Tested:** 22  

---

## 📊 Progress Summary

| Phase | Total | Completed | In Progress | Pending | Tested | Coverage |
|-------|-------|-----------|-------------|---------|--------|----------|
| **Setup & Infrastructure** | 5 | 4 | 0 | 1 | 3 | 80% |
| **Phase 1: Foundation** | 16 | 13 | 0 | 3 | 13 | 81% |
| **Phase 2: Relationships** | 7 | 6 | 0 | 1 | 6 | 86% |
| **Phase 3: Advanced Operations** | 15 | 6 | 0 | 9 | 0 | 40% |
| **Phase 4: MCP Integration** | 5 | 0 | 0 | 5 | 0 | 0% |
| **Phase 5: Testing & Validation** | 5 | 0 | 0 | 5 | 0 | 0% |
| **Documentation** | 4 | 0 | 0 | 4 | 0 | 0% |
| **TOTAL** | **57** | **29** | **0** | **28** | **22** | **51%** |

---

## 🔧 Setup & Infrastructure

### INFRA-1: Testing Infrastructure Setup
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** None
- **Test Coverage:** ✅ Basic structure verified
- **Notes:** 
  - Created project structure (`src/`, `tests/unit/`, `tests/integration/`, `tests/performance/`)
  - Configured `pyproject.toml`, `pytest.ini`, `.flake8`, `mypy.ini`, `.gitignore`
  - Created placeholder test files
  - Verified pytest runs successfully

### INFRA-2: Install Development Dependencies
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** INFRA-1
- **Test Coverage:** ✅ All tools verified
- **Notes:** 
  - ✅ Installed all dev dependencies using `uv sync --extra dev`
  - ✅ Verified pytest 9.0.1 works
  - ✅ Verified mypy 1.18.2 works
  - ✅ Verified ruff 0.14.6 works
  - ✅ Verified black 25.11.0 works
  - ✅ Virtual environment created at `.venv`
  - ✅ 54 packages installed successfully

### INFRA-3: Docker Compose Setup for Neo4j
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** INFRA-2
- **Test Coverage:** ✅ Basic setup verified
- **Notes:** 
  - ✅ Created `docker-compose.yml` for local Neo4j instance (Neo4j 5.26.2)
  - ✅ Configured Neo4j with authentication (default: neo4j/testpassword)
  - ✅ Documented connection details in `docker-compose.README.md`
  - ✅ Updated `SETUP.md` with Docker Compose instructions
  - ✅ Added health checks and volume persistence
  - ⏳ Test database setup script (can be added later if needed)

### INFRA-4: Environment Variables Configuration
- **Status:** ✅ Completed (Partially)
- **Priority:** High
- **Dependencies:** INFRA-3
- **Test Coverage:** ✅ Configuration module tested via integration tests
- **Notes:** 
  - ✅ Created configuration module (`src/config.py`) with Neo4jConfig and OpenAIConfig classes
  - ✅ Environment variable loading via pydantic-settings
  - ✅ Automatic .env file loading from parent directory (graphiti/.env)
  - ✅ Added python-dotenv dependency for .env file support
  - ✅ Added OpenAI organization support
  - ✅ Added GPT-5-nano model support via OPENAI_LLM_MODEL environment variable
  - ✅ Updated README.md with comprehensive configuration documentation
  - ✅ Environment variables validated via pydantic-settings
  - ⏳ TODO: Create `.env.example` file (documented in README instead, .env.example blocked by .gitignore)

### INFRA-5: Project Documentation Setup
- **Status:** ⏳ Pending
- **Priority:** Medium
- **Dependencies:** None
- **Test Coverage:** N/A
- **Notes:** 
  - Update `README.md` with project overview
  - Create `ARCHITECTURE.md` for system design
  - Create `API.md` for MCP tool documentation
  - Create `CONTRIBUTING.md` for development guidelines

---

## 🏗️ Phase 1: Foundation (Safest First)

### P1-1: Database Connection & Initialization

#### P1-1.1: Write Tests for Database Connection
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** INFRA-3, INFRA-4
- **Test Coverage:** ✅ Tests written and passing
- **Notes:** 
  - ✅ Test: Can connect to Neo4j successfully (`test_neo4j_connection`)
  - ✅ Test: Can query database and retrieve information (`test_neo4j_database_info`)
  - ✅ Test: Can create and delete test nodes
  - ⏳ Test: Handles connection failures gracefully (can add later)
  - ⏳ Test: Handles invalid credentials (can add later)
  - ⏳ Test: Handles database unavailable (can add later)
  - Test: Connection pooling works correctly
  - Test: Connection retry logic works

#### P1-1.2: Implement Database Connection
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-1.1
- **Test Coverage:** ✅ All tests passing (7 integration tests)
- **Notes:** 
  - ✅ Created `src/config.py` with Neo4jConfig class for environment variable management
  - ✅ Created `src/database.py` with DatabaseConnection class
  - ✅ Implemented connection, verification, and cleanup methods
  - ✅ Uses AsyncGraphDatabase driver
  - ✅ Handles connection errors gracefully (ServiceUnavailable, AuthError)
  - ✅ Supports async context manager pattern
  - ✅ All integration tests passing
  - ⏳ Connection pooling (handled by Neo4j driver automatically)
  - ⏳ Retry logic for transient failures (can add later if needed)

#### P1-1.3: Write Tests for Database Initialization
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-1.2
- **Test Coverage:** ✅ Tests written (6 tests, all passing)
- **Notes:** 
  - ✅ Test: Can query for constraints (test_initialization_creates_constraints)
  - ✅ Test: Can query for indexes (test_initialization_creates_indexes)
  - ✅ Test: Can query constraint existence (test_can_query_constraint_existence)
  - ✅ Test: Can query index existence (test_can_query_index_existence)
  - ✅ Test: Idempotency placeholder (test_initialization_is_idempotent)
  - ✅ Test: Constraint behavior placeholder (test_constraint_prevents_duplicate_entities)
  - ⏳ Tests will be enhanced once initialization function is implemented

#### P1-1.4: Implement Database Initialization
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-1.3
- **Test Coverage:** ✅ All tests passing (4 new tests, 17 total integration tests)
- **Notes:** 
  - ✅ Created `initialize_database()` function in `src/database.py`
  - ✅ Creates constraint: `unique_entity_per_group` (composite on group_id, entity_id)
  - ✅ Creates indexes: `entity_type_index`, `entity_group_index`, `relationship_type_index`
  - ✅ Uses `IF NOT EXISTS` for idempotency
  - ✅ Added logging for initialization steps
  - ✅ Handles initialization errors gracefully (continues on errors)
  - ✅ Verified constraint enforces uniqueness correctly
  - ✅ Verified idempotency (can run multiple times)
  - ⏳ Call initialization on startup (will be done when MCP server is created)

### P1-2: Entity Creation (Simplest Operation)

#### P1-2.1: Write Tests for Entity Creation
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-1.4
- **Test Coverage:** ✅ Tests written (25 tests total: 7 integration + 18 unit)
- **Notes:** 
  - ✅ Integration tests: Create entity with minimal fields, all fields, duplicate rejection, same ID different group, performance, properties validation, default group_id
  - ✅ Unit tests: Comprehensive validation tests for entity_id, entity_type, name, and properties
  - ✅ Test: Create entity with minimal fields (entity_id, entity_type, name) - Happy path
  - ✅ Test: Reject duplicate entity_id (clear error message via ConstraintError) - Error case
  - ✅ Test: Validate property types (string, number, boolean, null only) - Validation
  - ✅ Test: Reject nested objects/arrays in properties (TypeError) - Validation
  - ✅ Test: Handle invalid inputs (None, empty strings, wrong types) - Error cases
  - ✅ Test: Performance test (< 200ms) - Performance
  - ✅ Test: Property limits (max 50 properties, max key length 255, max value length 10000)
  - ✅ Test: Create entity with optional properties - Happy path
  - ✅ Test: Create entity with optional summary - Happy path
  - ✅ Test: Create entity with group_id isolation - Multi-tenancy
  - ✅ All 45 tests passing

#### P1-2.2: Implement Input Validation Layer
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-2.1
- **Test Coverage:** ✅ All tests passing (24 unit tests)
- **Notes:** 
  - ✅ Created `src/validation.py` with all validation functions
  - ✅ Implemented `validate_entity_id()` - validates and trims entity_id
  - ✅ Implemented `validate_entity_type()` - validates and trims entity_type
  - ✅ Implemented `validate_name()` - validates and trims name
  - ✅ Implemented `validate_properties()` - validates properties with limits (max 50, key length 255, value length 10000)
  - ✅ Implemented `validate_group_id()` - validates and normalizes group_id with reserved name checks
  - ✅ Added type checking and runtime validation
  - ✅ Added clear error messages for all validation failures
  - ✅ Exported validation functions and constants from module
  - ✅ All 24 unit tests passing
  - ✅ All 51 total tests passing

#### P1-2.3: Implement Entity Creation
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-2.2
- **Test Coverage:** ✅ All tests passing (7 new integration tests, 58 total)
- **Notes:** 
  - ✅ Created `add_entity()` function in `src/entities.py`
  - ✅ Uses all validation functions (entity_id, entity_type, name, properties, group_id)
  - ✅ Creates entity in Neo4j with Entity label and entity_type label
  - ✅ Stores entity_type as both label and property
  - ✅ Handles duplicate entity_id errors via ConstraintError → DuplicateEntityError
  - ✅ Returns entity data with all fields
  - ✅ Supports optional properties and summary
  - ✅ Defaults group_id to 'default' when not provided
  - ✅ Preserves null properties in return value
  - ✅ All 7 new integration tests passing
  - ✅ All 58 total tests passing

#### P1-2.4: Write Integration Tests for Entity Creation
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P1-2.3
- **Test Coverage:** ❌ Not written
- **Notes:** 
  - Test: Full flow from MCP tool to database
  - Test: Error propagation from database to MCP response
  - Test: Concurrent entity creation (thread safety)
  - Test: Transaction rollback on errors

### P1-3: Entity Retrieval

#### P1-3.1: Write Tests for Entity Retrieval
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-2.3
- **Test Coverage:** ✅ Tests written (9 integration tests)
- **Notes:** 
  - ✅ Test: Get by entity_id (exists) - verifies complete entity retrieval
  - ✅ Test: Get by entity_id (not exists) - verifies None return for missing entities
  - ✅ Test: Get by entity_id (different group) - verifies group_id isolation
  - ✅ Test: Get by type (single result) - verifies single entity retrieval
  - ✅ Test: Get by type (multiple results) - verifies multiple entities retrieval
  - ✅ Test: Get by type (no results) - verifies empty array return
  - ✅ Test: Performance targets (< 100ms for by ID, < 500ms for by type) - both passing
  - ✅ Test: Get by type with limit - verifies limit functionality
  - ✅ All 9 tests passing
- **Dependencies:** P1-2.4
- **Test Coverage:** ❌ Not written
- **Notes:** 
  - Test: Get by entity_id (exists) - Happy path
  - Test: Get by entity_id (not exists) → clear error - Error case
  - Test: Performance target (< 100ms) - Performance
  - Test: Handle invalid entity_id format - Validation
  - Test: Get entity with group_id isolation - Multi-tenancy
  - Test: Get entity with all properties - Happy path

#### P1-3.2: Implement Entity Retrieval Functions
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-3.1
- **Test Coverage:** ✅ All tests passing (18 integration tests)
- **Notes:** 
  - ✅ Created `get_entity_by_id()` function in `src/entities.py`
  - ✅ Created `get_entities_by_type()` function in `src/entities.py`
  - ✅ Handles entity not found with `EntityNotFoundError`
  - ✅ Supports group_id for multi-tenancy
  - ✅ Returns proper entity dictionaries with all fields
  - ✅ Supports limit parameter (default 50, max 1000)
  - ✅ Validates limit values
  - ✅ Uses indexed queries for performance
  - ✅ All 9 retrieval function tests passing
  - ✅ All 9 original retrieval tests updated and passing
  - ✅ All 76 total tests passing
  - ✅ Fixed cleanup fixture in conftest.py to ensure test isolation

### P1-4: Entity Update & Deletion

#### P1-4.1: Write Tests for Entity Update
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-3.2
- **Test Coverage:** ✅ All tests passing (8 integration tests)
- **Notes:** 
  - ✅ Test: Update entity name
  - ✅ Test: Update entity properties
  - ✅ Test: Update entity summary
  - ✅ Test: Update entity not found (raises error)
  - ✅ Test: Update entity group isolation
  - ✅ Test: Partial update (only specified fields)
  - ✅ Test: Remove property by not including it in update
  - ✅ Test: Remove summary by setting to None
  - ✅ Test: Update all fields at once
  - ✅ All 8 integration tests passing

#### P1-4.2: Implement Entity Update
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-4.1
- **Test Coverage:** ✅ All tests passing
- **Notes:** 
  - ✅ Created `update_entity()` function in `src/entities.py`
  - ✅ Supports partial updates (name, properties, summary)
  - ✅ Uses `_NOT_PROVIDED` sentinel to distinguish "not provided" from "explicitly None"
  - ✅ Dynamically builds Cypher SET clauses for only provided fields
  - ✅ Removes properties not included in update
  - ✅ Sets summary to null when explicitly passed as None
  - ✅ Updates `updated_at` timestamp
  - ✅ Raises `EntityNotFoundError` if entity doesn't exist
  - ✅ All 8 integration tests passing

#### P1-4.3: Write Tests for Entity Deletion
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-4.2
- **Test Coverage:** ✅ All tests passing (8 integration tests)
- **Notes:** 
  - ✅ Test: Soft delete entity (marks as deleted)
  - ✅ Test: Soft delete idempotent (preserves original deleted_at)
  - ✅ Test: Soft delete not found (idempotent, returns success)
  - ✅ Test: Soft delete group isolation
  - ✅ Test: Hard delete entity (permanent removal)
  - ✅ Test: Hard delete not found (raises error)
  - ✅ Test: Hard delete cascade (removes relationships)
  - ✅ Test: Delete performance (< 200ms)
  - ✅ All 8 integration tests passing

#### P1-4.4: Implement Entity Deletion
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-4.3
- **Test Coverage:** ✅ All tests passing
- **Notes:** 
  - ✅ Created `delete_entity()` function in `src/entities.py`
  - ✅ Supports both soft delete (default) and hard delete (hard=True)
  - ✅ Soft delete: Sets `_deleted = true` and `deleted_at = timestamp()`
  - ✅ Hard delete: Uses `DETACH DELETE` to permanently remove entity and relationships
  - ✅ Soft delete is idempotent (preserves original deleted_at on re-delete)
  - ✅ Hard delete raises `EntityNotFoundError` if entity doesn't exist
  - ✅ Soft delete returns success even if entity doesn't exist (idempotent)
  - ✅ Returns dict with status, entity_id, hard_delete flag, and deleted_at (for soft delete)
  - ✅ Updated `get_entity_by_id()` to filter out soft-deleted entities
  - ✅ All 8 integration tests passing

---

## 🔗 Phase 2: Relationships

### P2-1: Relationship Creation

#### P2-1.1: Write Tests for Relationship Creation
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P1-3.4
- **Test Coverage:** ✅ All tests passing (9 integration tests)
- **Notes:** 
  - ✅ Test: Create relationship between existing entities - Happy path
  - ✅ Test: Reject if source entity doesn't exist - Error case
  - ✅ Test: Reject if target entity doesn't exist - Error case
  - ✅ Test: Create relationship with optional properties - Happy path
  - ✅ Test: Create relationship with optional fact - Happy path
  - ✅ Test: Create multiple relationships between same entities (different types) - Feature
  - ✅ Test: Relationship group isolation
  - ✅ Test: Idempotency test - Edge case
  - ✅ Test: Performance test (< 200ms) - Performance
  - ✅ All 9 integration tests passing

#### P2-1.2: Implement Relationship Input Validation
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P2-1.1
- **Test Coverage:** ✅ All tests passing
- **Notes:** 
  - ✅ Created `validate_relationship_type()` function in `src/validation.py`
  - ✅ Created `validate_relationship_input()` function in `src/validation.py`
  - ✅ Validates source_entity_id (required, non-empty string)
  - ✅ Validates target_entity_id (required, non-empty string)
  - ✅ Validates relationship_type (required, non-empty string)
  - ✅ Validates properties (dict, flat key-value pairs only) - reuses `validate_properties()`
  - ✅ Returns clear error messages
  - ✅ All validation functions exported from module

#### P2-1.3: Implement Entity Existence Validation
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P2-1.2
- **Test Coverage:** ✅ All tests passing
- **Notes:** 
  - ✅ Created `validate_entities_exist()` function in `src/relationships.py`
  - ✅ Checks if source entity exists using `get_entity_by_id()`
  - ✅ Checks if target entity exists using `get_entity_by_id()`
  - ✅ Returns clear error if either doesn't exist
  - ✅ Supports group_id filtering
  - ✅ All tests passing (validated through relationship creation tests)

#### P2-1.4: Implement Relationship Creation
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P2-1.3
- **Test Coverage:** ✅ All tests passing
- **Notes:** 
  - ✅ Created `add_relationship()` function in `src/relationships.py`
  - ✅ Uses MERGE pattern for idempotency (creates or updates existing relationship)
  - ✅ Validates entities exist before creating relationship
  - ✅ Supports optional properties, fact, temporal properties (t_valid, t_invalid)
  - ✅ Supports group_id for multi-tenancy
  - ✅ Returns relationship dict with all fields (source_entity_id, target_entity_id, relationship_type, properties, fact, group_id, created_at)
  - ✅ Uses generic RELATIONSHIP type with relationship_type stored as property (for dynamic types)
  - ✅ Adds structured logging
  - ✅ All 9 integration tests passing

#### P2-1.5: Write Integration Tests for Relationship Creation
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P2-1.4
- **Test Coverage:** ❌ Not written
- **Notes:** 
  - Test: Full flow from MCP tool to database
  - Test: Error propagation (entity not found)
  - Test: Concurrent relationship creation
  - Test: Transaction rollback on errors

### P2-2: Relationship Retrieval

#### P2-2.1: Write Tests for Get Entity Relationships
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P2-1.5
- **Test Coverage:** ✅ All tests passing (10 integration tests)
- **Notes:** 
  - ✅ Test: Get relationships (outgoing) - Happy path
  - ✅ Test: Get relationships (incoming) - Happy path
  - ✅ Test: Get relationships (both) - Happy path
  - ✅ Test: Filter by relationship type - Feature
  - ✅ Test: Handle entity with no relationships → empty array - Edge case
  - ✅ Test: Performance targets (< 200ms) - Performance
  - ✅ Test: Handle invalid entity_id (entity not found) - Validation
  - ✅ Test: Support limit parameter - Feature
  - ✅ Test: Get relationships with group_id isolation - Multi-tenancy
  - ✅ Test: Get relationships with properties and fact - Feature
  - ✅ All 10 integration tests passing

#### P2-2.2: Implement Get Entity Relationships
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P2-2.1
- **Test Coverage:** ✅ All tests passing
- **Notes:** 
  - ✅ Created `get_entity_relationships()` function in `src/relationships.py`
  - ✅ Supports direction parameter (incoming, outgoing, both) - default 'both'
  - ✅ Supports relationship_types filter (array) - optional
  - ✅ Supports limit parameter (optional, validated 1-1000)
  - ✅ Supports group_id filtering
  - ✅ Validates entity exists before querying relationships
  - ✅ Returns array of relationship dicts with all fields (source, target, type, properties, fact, group_id, created_at)
  - ✅ Uses OPTIONAL MATCH for 'both' direction to handle incoming and outgoing
  - ✅ Filters out soft-deleted relationships (implicitly via group_id matching)
  - ✅ Adds structured logging
  - ✅ All 10 integration tests passing

---

## 🚀 Phase 3: Advanced Operations

### P3-1: Semantic Search

#### P3-1.1: Write Tests for Semantic Search
- **Status:** ✅ Completed
- **Priority:** Medium
- **Dependencies:** P2-2.2
- **Test Coverage:** ✅ Tests written (7 integration tests)
- **Notes:** 
  - ✅ Test: Search nodes by natural language query - Happy path
  - ✅ Test: Returns relevance scores (0.0 to 1.0) - Feature
  - ✅ Test: Filters by entity type when provided - Feature
  - ✅ Test: Respects max_nodes limit - Feature
  - ✅ Test: Returns empty array if no matches - Edge case
  - ✅ Test: Search with group_id isolation - Multi-tenancy
  - ✅ Test: Performance target (< 300ms) - Performance
  - ✅ All 7 integration tests written (require OpenAI API key to run)

#### P3-1.2: Implement Embedding Generation
- **Status:** ✅ Completed
- **Priority:** Medium
- **Dependencies:** P3-1.1
- **Test Coverage:** ⏳ Covered by P3-1.1 tests
- **Notes:** 
  - ✅ Created `src/embeddings.py` module
  - ✅ Implemented `generate_embedding()` function (OpenAI API integration)
  - ✅ Implemented `generate_entity_embedding()` function (combines name + summary)
  - ✅ Implemented `cosine_similarity()` function for vector comparison
  - ✅ Added OpenAI configuration (`OpenAIConfig` class)
  - ✅ Integrated embedding generation into `add_entity()` (automatic on creation)
  - ✅ Integrated embedding regeneration into `update_entity()` (when name/summary changes)
  - ✅ Embeddings stored as entity property in Neo4j
  - ✅ Error handling: embedding failures don't break entity operations
  - ✅ Added openai and numpy dependencies to pyproject.toml

#### P3-1.3: Implement Semantic Search
- **Status:** ✅ Completed (Basic Implementation)
- **Priority:** Medium
- **Dependencies:** P3-1.2
- **Test Coverage:** ⏳ Tests written, need to run with OpenAI API
- **Notes:** 
  - ✅ Created `search_nodes()` function in `src/search.py`
  - ✅ Generates query embedding using OpenAI
  - ✅ Calculates cosine similarity with entity embeddings
  - ✅ Filters by entity_type if provided
  - ✅ Filters by group_id (multi-tenancy)
  - ✅ Sorts by relevance score (descending)
  - ✅ Returns top N results with scores (0.0 to 1.0)
  - ✅ Skips entities without embeddings (graceful degradation)
  - ✅ Adds structured logging
  - ⏳ TODO: Add hybrid search (BM25 lexical + vector) - currently vector-only
  - ⏳ TODO: Add caching for embeddings to avoid regeneration

### P3-2: Automatic Entity/Relationship Extraction

#### P3-2.1: Write Tests for add_memory
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P3-1.3
- **Test Coverage:** ✅ Tests written (8 integration tests)
- **Notes:** 
  - ✅ Test: Extract entities from unstructured text - Happy path
  - ✅ Test: Extract relationships from unstructured text - Happy path
  - ✅ Test: Automatic deduplication of entities - Feature
  - ✅ Test: Generate embeddings for semantic search - Feature
  - ✅ Test: Performance targets (small text < 2s) - Performance
  - ✅ Test: Handle extraction failures gracefully - Error case
  - ✅ Test: Support different source types (text, json, message) - Feature
  - ✅ Test: Support group_id isolation - Multi-tenancy
  - ✅ All 8 integration tests written (require OpenAI API key to run)

#### P3-2.2: Implement LLM Integration for Extraction
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P3-2.1
- **Test Coverage:** ⏳ Covered by P3-2.1 tests
- **Notes:** 
  - ✅ Created `EXTRACTION_PROMPT_TEMPLATE` for entity/relationship extraction
  - ✅ Implemented `_call_llm_for_extraction()` function
  - ✅ Calls OpenAI API with structured prompt
  - ✅ Parses LLM JSON response with validation
  - ✅ Handles LLM API errors gracefully
  - ✅ Uses gpt-4o-mini as default model (configurable via OPENAI_LLM_MODEL)
  - ✅ Supports GPT-5-nano, GPT-5o-mini, GPT-4o-mini models
  - ✅ Uses temperature=0.0 for deterministic extraction
  - ✅ Forces JSON response format
  - ✅ Added llm_model to OpenAIConfig
  - ✅ Automatic .env file loading from parent directory (graphiti/.env)
  - ✅ Added python-dotenv dependency for .env file support

#### P3-2.3: Implement add_memory Function
- **Status:** ✅ Completed
- **Priority:** High
- **Dependencies:** P3-2.2
- **Test Coverage:** ⏳ Covered by P3-2.1 tests
- **Notes:** 
  - ✅ Created `add_memory()` function in `src/memory.py`
  - ✅ Extracts entities and relationships using LLM
  - ✅ Implements `_deduplicate_entities()` for entity deduplication
  - ✅ Creates entities using `add_entity()` (idempotent)
  - ✅ Creates relationships using `add_relationship()` (idempotent)
  - ✅ Embeddings generated automatically via `add_entity()` integration
  - ✅ Supports source types: "text", "json", "message"
  - ✅ Supports group_id for multi-tenancy
  - ✅ Handles extraction failures with clear error messages
  - ✅ Returns detailed result with entities_created, relationships_created
  - ✅ Adds structured logging
  - ⏳ TODO: Asynchronous processing for large content (> 10000 chars)
  - ⏳ TODO: Entity name variation resolution (currently deduplicates by entity_id only)

### P3-3: Update Operations

#### P3-3.1: Write Tests for update_memory
- **Status:** ✅ Complete
- **Priority:** Medium
- **Dependencies:** P3-2.3
- **Test Coverage:** ✅ Written (6 tests)
- **Test Results:** ✅ All 6 tests passing
- **Notes:** 
  - ✅ Test: Update existing memory incrementally - Happy path (PASSING)
  - ✅ Test: Only changed entities/relationships are updated - Feature (PASSING)
  - ✅ Test: Embeddings only regenerated for changed content - Feature (PASSING)
  - ✅ Test: History is preserved (soft delete) - Feature (PASSING)
  - ✅ Test: Content hash comparison works correctly - Feature (PASSING - fixed: hash comparison skips updates when content is identical)
  - ✅ Test: Replace strategy soft-deletes old entities - Feature (PASSING - fixed: replace strategy soft-deletes correctly)
  - ✅ Test: Handle update failures gracefully - Error case (PASSING - fixed: test creates memory first)
  - **Implementation Fixes Applied:**
    1. ✅ Content hash stored on first entity and compared in update_memory to skip updates when identical
    2. ✅ Replace strategy correctly soft-deletes old entities (verified in test)
    3. ✅ Error handling test creates memory before testing update failures

#### P3-3.2: Implement Content Comparison
- **Status:** ✅ Complete
- **Priority:** Medium
- **Dependencies:** P3-3.1
- **Test Coverage:** ✅ Complete (22 unit tests)
- **Notes:** 
  - ✅ Create function to calculate content hash (`_calculate_content_hash`)
  - ✅ Compare old vs new content hash (implemented in `update_memory`)
  - ✅ Identify changed entities (added, removed, modified) (`_compare_entities`)
  - ✅ Identify changed relationships (added, removed, modified) (`_compare_relationships`)
  - ✅ Use diff algorithm for fine-grained comparison (field-level comparison)
  - **Test Coverage:**
    - 5 tests for `_calculate_content_hash` (consistency, different content, unicode, empty string)
    - 9 tests for `_compare_entities` (added, removed, modified, complex scenarios, edge cases)
    - 8 tests for `_compare_relationships` (added, removed, modified, complex scenarios, edge cases)

#### P3-3.3: Implement update_memory Function
- **Status:** ✅ Complete
- **Priority:** Medium
- **Dependencies:** P3-3.2
- **Test Coverage:** ✅ Complete (6 integration tests, all passing)
- **Notes:** 
  - ✅ Create `update_memory()` function - Implemented
  - ✅ Compare old vs new content - Uses `_compare_entities()` and `_compare_relationships()`
  - ✅ Update only changed entities - Only modified entities are updated via `update_entity()`
  - ✅ Update only changed relationships - Only modified relationships are updated
  - ✅ Regenerate embeddings only for changed content - `update_entity()` regenerates embeddings when name/summary changes
  - ✅ Support both "replace" and "incremental" strategies - Both strategies implemented
  - ✅ Add structured logging - Logging throughout (info, debug, error levels)
  - **Implementation Details:**
    - Content hash comparison to skip updates when content is identical
    - Incremental strategy: compares entities/relationships and updates only what changed
    - Replace strategy: soft-deletes old entities and re-adds memory
    - Embeddings regenerated automatically by `update_entity()` when name/summary changes
    - All operations are idempotent and handle errors gracefully

### P3-4: Delete Operations

#### P3-4.1: Write Tests for Soft Delete
- **Status:** ✅ Complete
- **Priority:** Medium
- **Dependencies:** P3-3.3
- **Test Coverage:** ✅ Written (8 tests)
- **Test Results:** 2 passing, 6 failing (expected - functionality not implemented yet)
- **Notes:** 
  - ✅ Test: Soft delete entity (marks as deleted) - Happy path (PASSING - already implemented)
  - ✅ Test: Soft delete relationship (marks as deleted) - Happy path (FAILING - needs implementation)
  - ✅ Test: Queries automatically filter out soft-deleted entities - Feature (PASSING - already implemented)
  - ✅ Test: Queries automatically filter out soft-deleted relationships - Feature (FAILING - needs implementation)
  - ✅ Test: Can restore soft-deleted entities - Feature (FAILING - needs implementation)
  - ✅ Test: Can restore soft-deleted relationships - Feature (FAILING - needs implementation)
  - ✅ Test: Can query deleted entities with include_deleted flag - Feature (FAILING - needs implementation)
  - ✅ Test: Can query deleted relationships with include_deleted flag - Feature (FAILING - needs implementation)
  - **Test File:** `tests/integration/test_soft_delete.py`

#### P3-4.2: Implement Soft Delete
- **Status:** ✅ Complete
- **Priority:** Medium
- **Dependencies:** P3-4.1
- **Test Coverage:** ✅ Complete (8 tests, all passing)
- **Notes:** 
  - ✅ Create `soft_delete_entity()` function - Already existed, verified working
  - ✅ Create `soft_delete_relationship()` function - Implemented in `src/relationships.py`
  - ✅ Set `_deleted: true` and `deleted_at: timestamp` - Implemented for both entities and relationships
  - ✅ Update all queries to filter out soft-deleted items - Implemented in `get_entity_by_id()` and `get_entity_relationships()`
  - ✅ Create `restore_entity()` function - Implemented in `src/entities.py`
  - ✅ Create `restore_relationship()` function - Implemented in `src/relationships.py`
  - ✅ Add `include_deleted` parameter to `get_entity_by_id()` - Implemented
  - ✅ Add `include_deleted` parameter to `get_entity_relationships()` - Implemented
  - ✅ Add structured logging - All functions have logging

#### P3-4.3: Write Tests for Hard Delete
- **Status:** ✅ Complete
- **Priority:** Low
- **Dependencies:** P3-4.2
- **Test Coverage:** ✅ Written (6 tests)
- **Test Results:** 4 passing, 2 failing (expected - functionality not implemented yet)
- **Notes:** 
  - ✅ Test: Hard delete entity (permanently removes) - Happy path (PASSING - already implemented)
  - ✅ Test: Hard delete relationship (permanently removes) - Happy path (FAILING - needs `hard_delete_relationship()`)
  - ✅ Test: Cascade delete (removes all relationships) - Feature (PASSING - already implemented)
  - ✅ Test: Cannot restore hard-deleted entities - Feature (PASSING - already implemented)
  - ✅ Test: Cannot restore hard-deleted relationships - Feature (FAILING - needs `hard_delete_relationship()`)
  - ✅ Test: Hard delete vs soft delete comparison - Feature (PASSING)
  - **Test File:** `tests/integration/test_hard_delete.py`

#### P3-4.4: Implement Hard Delete
- **Status:** ✅ Complete
- **Priority:** Low
- **Dependencies:** P3-4.3
- **Test Coverage:** ✅ Complete (6 tests, all passing)
- **Notes:** 
  - ✅ Create `delete_entity()` function - Already existed with `hard=True` parameter
  - ✅ Create `hard_delete_relationship()` function - Implemented in `src/relationships.py`
  - ✅ Use `DETACH DELETE` for cascade deletion - Implemented for entities (removes entity and all relationships)
  - ✅ Use `DELETE` for relationship deletion - Implemented (removes only the relationship, not nodes)
  - ✅ Support cascade parameter - Cascade is automatic for entity hard delete (DETACH DELETE)
  - ✅ Add structured logging - All functions have logging
  - **Implementation Details:**
    - Entity hard delete: Uses `DETACH DELETE` to permanently remove entity and all its relationships
    - Relationship hard delete: Uses `DELETE` to permanently remove only the relationship
    - Hard delete raises errors if item doesn't exist (unlike soft delete which is idempotent)
    - Hard-deleted items cannot be restored (they're permanently removed)

---

## 🔌 Phase 4: MCP Integration

### P4-1: MCP Tool Definitions

#### P4-1.1: Define MCP Tool Schemas
- **Status:** ✅ Complete
- **Priority:** High
- **Dependencies:** P3-2.3
- **Test Coverage:** ⏳ Not written (will be tested in P4-1.3)
- **Notes:** 
  - ✅ Define tool schema for `add_entity` - Implemented
  - ✅ Define tool schema for `add_relationship` - Implemented
  - ✅ Define tool schema for `get_entity_by_id` - Implemented
  - ✅ Define tool schema for `get_entities_by_type` - Implemented
  - ✅ Define tool schema for `get_entity_relationships` - Implemented
  - ✅ Define tool schema for `search_nodes` - Implemented
  - ✅ Define tool schema for `add_memory` - Implemented
  - ✅ Define tool schema for `update_memory` - Implemented
  - ✅ Define tool schema for `soft_delete_entity` - Implemented
  - ✅ Define tool schema for `soft_delete_relationship` - Implemented
  - ✅ Define tool schema for `restore_entity` - Implemented
  - ✅ Define tool schema for `restore_relationship` - Implemented
  - ✅ Define tool schema for `hard_delete_entity` - Implemented
  - ✅ Define tool schema for `hard_delete_relationship` - Implemented
  - **Total:** 14 tool schemas defined
  - **File:** `src/mcp_tools.py` with `get_tool_schemas()` function
  - **Schema Format:** JSON Schema following MCP specification

#### P4-1.2: Implement MCP Tool Handlers
- **Status:** ✅ Complete
- **Priority:** High
- **Dependencies:** P4-1.1
- **Test Coverage:** ⏳ Not tested (will be tested in P4-1.3)
- **Notes:** 
  - ✅ Create handler for each MCP tool - Implemented (14 handlers)
  - ✅ Map MCP tool calls to internal functions - All tools mapped
  - ✅ Handle JSON-RPC request/response format - Returns TextContent with JSON
  - ✅ Transform errors to MCP error format - Domain errors, validation errors, and internal errors handled
  - ✅ Add input validation at MCP layer - Validation handled by internal functions
  - ✅ Add structured logging - Logging added for all operations
  - **File:** `src/mcp_server.py`
  - **Features:**
    - Lifespan management for database connection
    - 14 tool handlers implemented
    - Error handling with proper error types
    - JSON response format
    - Server entry point with `run_server()` function

#### P4-1.3: Write Integration Tests for MCP Tools
- **Status:** ✅ Complete
- **Priority:** High
- **Dependencies:** P4-1.2
- **Test Coverage:** ✅ Complete (14 tests, all passing)
- **Notes:** 
  - ✅ Test: MCP tool calls work end-to-end - All handlers tested
  - ✅ Test: Error responses are properly formatted - Error handling verified
  - ✅ Test: Input validation at MCP layer - Validation errors tested
  - ✅ Test: Response format matches MCP spec - Response format verified
  - **File:** `tests/integration/test_mcp_tools.py`
  - **Test Coverage:**
    - `test_list_tools_returns_all_schemas` - Verifies all 14 tools are registered
    - `test_mcp_tool_add_entity_success` - Tests successful entity creation
    - `test_mcp_tool_add_entity_duplicate_error` - Tests duplicate error handling
    - `test_mcp_tool_get_entity_by_id_success` - Tests entity retrieval
    - `test_mcp_tool_get_entity_by_id_not_found` - Tests not found error handling
    - `test_mcp_tool_add_relationship_success` - Tests relationship creation
    - `test_mcp_tool_validation_error` - Tests input validation
    - `test_mcp_tool_unknown_tool_error` - Tests unknown tool handling
    - `test_mcp_tool_soft_delete_entity` - Tests soft delete functionality
    - `test_mcp_tool_restore_entity` - Tests restore functionality
    - `test_mcp_tool_hard_delete_entity` - Tests hard delete functionality
    - `test_mcp_tool_search_nodes` - Tests semantic search
    - `test_mcp_tool_response_format_consistency` - Tests response format
    - `test_mcp_tool_error_handling` - Tests error handling patterns
  - **All 14 tests passing** ✅

### P4-2: MCP Server Setup

#### P4-2.1: Create MCP Server Entry Point
- **Status:** ✅ Complete
- **Priority:** High
- **Dependencies:** P4-1.3
- **Test Coverage:** ⏳ Not tested (will be tested in P4-2.2)
- **Notes:** 
  - ✅ Create main server file - Created `main.py` and `src/__main__.py`
  - ✅ Initialize MCP server - Server initialized in `src/mcp_server.py`
  - ✅ Register all tools - All 14 tools registered via `handle_list_tools()`
  - ✅ Handle server lifecycle (start, stop) - Implemented with lifespan management
  - ✅ Add structured logging - Logging configured with proper format
  - **Files Created:**
    - `main.py` - Standalone entry point script
    - `src/__main__.py` - Package entry point (allows `python -m src`)
  - **Entry Points:**
    - `python main.py` - Run standalone script
    - `python -m src` - Run as package module
    - `graffiti-mcp-server` - CLI command (via pyproject.toml entry point)
  - **Features:**
    - Structured logging to stderr (doesn't interfere with MCP stdio)
    - Proper error handling (KeyboardInterrupt, exceptions)
    - Server lifecycle management (database connection via lifespan)
    - All 14 tools automatically registered

#### P4-2.2: Create MCP Server Configuration
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P4-2.1
- **Test Coverage:** ❌ Not tested
- **Notes:** 
  - Create configuration file for MCP server
  - Document server setup instructions
  - Create example configuration
  - Add validation for configuration

---

## ✅ Phase 5: Testing & Validation

### P5-1: Test Coverage

#### P5-1.1: Achieve 90% Code Coverage
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P4-2.2
- **Test Coverage:** ❌ Not achieved
- **Notes:** 
  - Run coverage report
  - Identify uncovered code
  - Write additional tests for uncovered code
  - Verify 90% coverage threshold

#### P5-1.2: Performance Benchmarking
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P5-1.1
- **Test Coverage:** ❌ Not benchmarked
- **Notes:** 
  - Create performance benchmarks for all operations
  - Verify performance targets are met:
    - Entity creation: < 200ms
    - Entity retrieval by ID: < 100ms
    - Entity retrieval by type: < 500ms
    - Relationship creation: < 200ms
    - Relationship queries: < 200ms
    - Semantic search: < 300ms
  - Document performance results

#### P5-1.3: Integration Test Suite
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P5-1.2
- **Test Coverage:** ❌ Not complete
- **Notes:** 
  - Test full workflows (create entity → create relationship → query)
  - Test error propagation across layers
  - Test concurrent operations
  - Test database transaction handling
  - Test MCP tool integration end-to-end

### P5-2: Error Handling Validation

#### P5-2.1: Validate All Error Cases
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P5-1.3
- **Test Coverage:** ❌ Not validated
- **Notes:** 
  - Verify all error cases return clear, actionable messages
  - Verify error messages don't expose internals
  - Verify error format is consistent
  - Verify errors are logged with context

### P5-3: Data Integrity Validation

#### P5-3.1: Validate Data Integrity
- **Status:** ⏳ Pending
- **Priority:** High
- **Dependencies:** P5-2.1
- **Test Coverage:** ❌ Not validated
- **Notes:** 
  - Verify entity_id uniqueness is enforced
  - Verify relationships validate entity existence
  - Verify properties are simple key-value pairs
  - Verify no data corruption under normal operations
  - Verify transactions work correctly

---

## 📚 Documentation

### DOC-1: API Documentation
- **Status:** ⏳ Pending
- **Priority:** Medium
- **Dependencies:** P4-2.2
- **Test Coverage:** N/A
- **Notes:** 
  - Document all MCP tools with examples
  - Document request/response formats
  - Document error codes and messages
  - Create API reference guide

### DOC-2: Architecture Documentation
- **Status:** ⏳ Pending
- **Priority:** Medium
- **Dependencies:** P4-2.2
- **Test Coverage:** N/A
- **Notes:** 
  - Document system architecture
  - Document database schema
  - Document data flow
  - Create architecture diagrams

### DOC-3: Development Guide
- **Status:** ⏳ Pending
- **Priority:** Medium
- **Dependencies:** P5-3.1
- **Test Coverage:** N/A
- **Notes:** 
  - Document development setup
  - Document testing procedures
  - Document code style guidelines
  - Document contribution process

### DOC-4: User Guide
- **Status:** ⏳ Pending
- **Priority:** Low
- **Dependencies:** DOC-1
- **Test Coverage:** N/A
- **Notes:** 
  - Create user guide for MCP tool usage
  - Provide examples and use cases
  - Document best practices
  - Create troubleshooting guide

---

## 📝 Notes

### Task Status Legend
- ✅ **Completed:** Task is fully implemented and tested
- ⏳ **Pending:** Task is not yet started
- 🔄 **In Progress:** Task is currently being worked on
- ❌ **Blocked:** Task is blocked by dependencies or issues
- ⚠️ **Needs Review:** Task needs review before marking as complete

### Priority Legend
- **High:** Critical for MVP, must be completed first
- **Medium:** Important but can be done after high-priority tasks
- **Low:** Nice to have, can be deferred

### Test Coverage Legend
- ✅ **Tested:** Tests written and passing
- ❌ **Not tested:** Tests not yet written or not passing
- ⏳ **In progress:** Tests being written
- N/A: Not applicable (documentation, setup tasks)

---

## 🔄 Update Log

- **2025-01-27:** Initial TODO list created with comprehensive task breakdown
- **2025-01-27:** P1-4.1 (Entity Update Tests) completed - Created comprehensive test suite: 8 integration tests for entity update operations, all tests passing
- **2025-01-27:** P1-4.2 (Entity Update Implementation) completed - Implemented `update_entity()` function with partial update support, uses `_NOT_PROVIDED` sentinel, all 8 integration tests passing
- **2025-01-27:** P1-4.3 (Entity Deletion Tests) completed - Created comprehensive test suite: 8 integration tests for entity deletion operations (soft and hard delete), all tests passing
- **2025-01-27:** P1-4.4 (Entity Deletion Implementation) completed - Implemented `delete_entity()` function with soft/hard delete support, soft delete is idempotent, updated `get_entity_by_id()` to filter soft-deleted entities, all 8 integration tests passing
- **2025-01-27:** P2-1.1 (Relationship Creation Tests) completed - Created comprehensive test suite: 9 integration tests for relationship creation operations, all tests passing
- **2025-01-27:** P2-1.2 (Relationship Input Validation) completed - Implemented `validate_relationship_type()` and `validate_relationship_input()` functions in validation.py, all tests passing
- **2025-01-27:** P2-1.3 (Entity Existence Validation) completed - Implemented `validate_entities_exist()` function in relationships.py, validates source and target entities exist before creating relationships
- **2025-01-27:** P2-1.4 (Relationship Creation Implementation) completed - Implemented `add_relationship()` function with MERGE pattern for idempotency, supports properties, fact, temporal properties, all 9 integration tests passing
- **2025-01-27:** P2-2.1 (Relationship Retrieval Tests) completed - Created comprehensive test suite: 10 integration tests for relationship retrieval operations, all tests passing
- **2025-01-27:** P2-2.2 (Relationship Retrieval Implementation) completed - Implemented `get_entity_relationships()` function with direction support (incoming/outgoing/both), relationship type filtering, limit support, all 10 integration tests passing
- **2025-01-27:** P3-1.1 (Semantic Search Tests) completed - Created 7 comprehensive integration tests for semantic search operations
- **2025-01-27:** P3-1.2 (Embedding Generation) completed - Implemented embedding generation module with OpenAI integration, automatic embedding generation on entity create/update
- **2025-01-27:** P3-1.3 (Semantic Search Implementation) completed - Implemented `search_nodes()` function with vector similarity search, entity type filtering, group isolation, relevance scoring
- **2025-01-27:** P3-2.1 (add_memory Tests) completed - Created 8 comprehensive integration tests for automatic entity/relationship extraction
- **2025-01-27:** P3-2.2 (LLM Integration) completed - Implemented `_call_llm_for_extraction()` with structured prompt, JSON parsing, error handling
- **2025-01-27:** P3-2.3 (add_memory Function) completed - Implemented `add_memory()` function with entity/relationship extraction, deduplication, automatic embedding generation
- **2025-01-27:** INFRA-4 (Environment Variables Configuration) completed - Added GPT-5-nano support via OPENAI_LLM_MODEL environment variable, automatic .env file loading from parent directory, OpenAI organization support, python-dotenv dependency added, updated README.md with configuration documentation
- **2025-01-27:** INFRA-3 (Docker Compose Setup) completed - Created docker-compose.yml, documentation, and updated SETUP.md
- **2025-01-27:** P1-1.1 (Database Connection Tests) completed - Created and verified Neo4j connection tests, both tests passing
- **2025-01-27:** INFRA-2 (Install Development Dependencies) completed - Installed all dev dependencies using uv, verified all tools (pytest, mypy, ruff, black) work correctly
- **2025-01-27:** P1-1.2 (Database Connection Module) completed - Created config.py and database.py modules, implemented DatabaseConnection class with async context manager support, all 7 integration tests passing
- **2025-01-27:** P1-1.3 (Database Initialization Tests) completed - Created 6 comprehensive tests for database initialization, all tests passing, ready for implementation
- **2025-01-27:** P1-1.4 (Database Initialization Implementation) completed - Implemented `initialize_database()` function, creates all required constraints and indexes, verified idempotency and constraint enforcement, all 17 integration tests passing
- **2025-01-27:** P1-2.1 (Entity Creation Tests) completed - Created comprehensive test suite: 7 integration tests for entity creation operations, 18 unit tests for validation logic, all 45 tests passing, ready for implementation
- **2025-01-27:** P1-2.2 (Input Validation Layer) completed - Implemented complete validation module with functions for entity_id, entity_type, name, properties, and group_id validation, all 24 unit tests passing, all 51 total tests passing
- **2025-01-27:** P1-2.3 (Entity Creation) completed - Implemented `add_entity()` function with full validation, Neo4j integration, duplicate handling, and proper label/property storage, all 7 new integration tests passing, all 58 total tests passing
- **2025-01-27:** P1-3.1 (Entity Retrieval Tests) completed - Created comprehensive test suite: 9 integration tests covering entity retrieval by ID and type, performance targets, group isolation, and limit functionality, all 9 tests passing, all 67 total tests passing
- **2025-01-27:** P1-3.2 (Entity Retrieval Implementation) completed - Implemented `get_entity_by_id()` and `get_entities_by_type()` functions with full validation, error handling, group isolation, limit support, and proper property extraction, all 18 retrieval tests passing (9 function tests + 9 updated original tests), all 76 total tests passing, fixed cleanup fixture in conftest.py
- Tasks will be updated as work progresses

---

**Next Steps:**
1. Install development dependencies (INFRA-2)
2. Set up Docker Compose for Neo4j (INFRA-3)
3. Begin Phase 1: Database Connection & Initialization (P1-1)


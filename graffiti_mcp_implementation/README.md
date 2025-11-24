# Graffiti Graph MCP Implementation

**Test-Driven Development Approach**

This folder contains the implementation of the Graffiti Graph MCP server following a strict test-driven development (TDD) methodology.

## 📋 Implementation Strategy

See [GRAFFITI_IMPLEMENTATION_STRATEGY.md](../../../docs/GRAFFITI_IMPLEMENTATION_STRATEGY.md) for the complete strategic approach.

## 🎯 Core Principles

1. **Test-Driven Development (TDD)**
   - Write tests BEFORE implementation
   - Test edge cases and error paths FIRST
   - Validate each step before moving forward

2. **Incremental Implementation**
   - One operation at a time
   - Test in isolation before integration
   - Small, reviewable commits

3. **Defensive Validation**
   - Input validation at every boundary
   - Type checking (Python type hints + runtime checks)
   - Database constraint validation

4. **Regression Prevention**
   - Test suite runs on every change
   - Integration tests for each operation
   - Performance benchmarks

## 📁 Project Structure

```
graffiti_mcp_implementation/
├── src/                    # Source code (implementation)
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Performance benchmarks
├── pyproject.toml         # Project configuration
├── pytest.ini            # Pytest configuration
├── mypy.ini              # Type checking configuration
└── README.md             # This file
```

## 🧪 Testing Infrastructure

### Tools
- **pytest** - Testing framework
- **mypy** - Type checking
- **ruff** - Linting and formatting
- **black** - Code formatting
- **coverage** - Test coverage tracking
- **pytest-benchmark** - Performance testing

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run performance benchmarks
pytest -m performance

# Run with coverage
pytest --cov=src --cov-report=html

# Run type checking
mypy src

# Run linting
ruff check src tests

# Format code
black src tests
ruff format src tests
```

## 📊 Test Coverage Requirements

- **Minimum 90% code coverage**
- Every function must have:
  - ✅ Happy path test
  - ✅ Error path test
  - ✅ Edge case test
  - ✅ Performance test

## 🚀 Implementation Phases

### Phase 1: Foundation
1. Database Connection & Initialization
2. Entity Creation (Simplest Operation)
3. Entity Retrieval

### Phase 2: Relationships
4. Relationship Creation
5. Relationship Retrieval

### Phase 3: Advanced Operations
6. Semantic Search
7. MCP Tool Integration
8. Error Handling & Logging

## ✅ Success Criteria

Before moving to next phase:
- ✅ All tests pass
- ✅ Code coverage > 90%
- ✅ No linting errors
- ✅ Type checking passes
- ✅ Performance targets met
- ✅ Error handling complete
- ✅ Documentation updated

## ⚙️ Configuration

### Environment Variables

The implementation uses environment variables for configuration. You can set them in a `.env` file in the `graphiti` directory (parent directory) or as system environment variables.

**Required:**
- `OPENAI_API_KEY` - OpenAI API key for embeddings and LLM operations

**Optional:**
- `OPENAI_LLM_MODEL` - LLM model for entity/relationship extraction (default: `gpt-5-nano`)
  - Supported models: `gpt-5-nano` (default, reasoning model), `gpt-5o-mini`, `gpt-4o-mini` (fallback)
  - Note: `gpt-5-nano` is a reasoning model and doesn't support temperature parameter
  - Example: `OPENAI_LLM_MODEL=gpt-5-nano`
- `OPENAI_ORGANIZATION` - OpenAI organization ID (if using organization account)
- `OPENAI_EMBEDDING_MODEL` - Embedding model (default: `text-embedding-3-small`)
- `OPENAI_EMBEDDING_DIMENSION` - Embedding dimension (default: `1536`)
- `NEO4J_URI` - Neo4j connection URI (default: `bolt://localhost:7687`)
- `NEO4J_USER` - Neo4j username (default: `neo4j`)
- `NEO4J_PASSWORD` - Neo4j password (default: `testpassword`)
- `NEO4J_DATABASE` - Neo4j database name (default: `neo4j`)

**Example `.env` file:**
```bash
# Required
OPENAI_API_KEY=sk-proj-...

# Optional - Use GPT-5-nano for extraction
OPENAI_LLM_MODEL=gpt-5-nano

# Optional - Neo4j configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

**Note:** The `.env` file should be placed in the `graphiti` directory (parent directory), and the configuration will automatically load from there.

## 📝 Notes

- Follow TDD: Write tests first, then implement
- One operation at a time
- Validate before moving forward
- Never skip tests


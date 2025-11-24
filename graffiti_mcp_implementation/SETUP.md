# Setup Guide

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (for Neo4j testing)
- pip or uv package manager

## Installation

### 1. Create Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Or using uv (recommended)
uv pip install -e ".[dev]"
```

### 3. Start Neo4j with Docker Compose

**Option 1: Manual (Command Line)**
```bash
# Start Neo4j container
docker-compose up -d

# Verify Neo4j is running and healthy
docker-compose ps

# Check logs (optional)
docker-compose logs neo4j
```

**Option 2: Automated (Docker MCP)**
The AI assistant can manage Docker containers directly using Docker MCP tools. This enables:
- Automated container lifecycle management
- Programmatic health checks
- Integrated testing workflows

**Note:** See `docker-compose.README.md` for detailed Docker Compose instructions and Docker MCP integration.

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Neo4j Configuration (matches docker-compose.yml defaults)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=testpassword

# OpenAI API Configuration (for LLM-based extraction)
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
GRAPHITI_GROUP_ID=main

# Test Configuration
TEST_GROUP_ID=test_group
```

**Note:** The default password in Docker Compose is `testpassword`. Change it in both `docker-compose.yml` and `.env` if needed.

### 5. Verify Setup

Run the placeholder tests to verify everything is working:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run type checking
mypy src

# Run linting
ruff check src tests

# Format code
black src tests
ruff format src tests
```

## Development Workflow

### 1. Write Tests First (TDD)

```bash
# Create a new test file
touch tests/unit/test_entity_creation.py

# Write test cases
# Run tests (they should fail initially)
pytest tests/unit/test_entity_creation.py -v
```

### 2. Implement Code

```bash
# Create implementation file
touch src/entity.py

# Implement to make tests pass
# Run tests continuously
pytest tests/unit/test_entity_creation.py -v --cov=src
```

### 3. Check Quality

```bash
# Type checking
mypy src

# Linting
ruff check src tests

# Format code
black src tests
ruff format src tests

# Coverage
pytest --cov=src --cov-report=html
```

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Performance benchmarks
pytest -m performance

# Specific test file
pytest tests/unit/test_entity_creation.py

# Specific test function
pytest tests/unit/test_entity_creation.py::test_create_entity_happy_path

# With verbose output
pytest -v

# With coverage report
pytest --cov=src --cov-report=html
```

## Code Quality Checks

```bash
# Type checking
mypy src

# Linting
ruff check src tests

# Format code
black src tests
ruff format src tests

# All checks at once
mypy src && ruff check src tests && black --check src tests
```

## Docker Compose Commands

```bash
# Start Neo4j
docker-compose up -d

# Stop Neo4j (keeps data)
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop and remove containers + volumes (deletes all data)
docker-compose down -v

# View logs
docker-compose logs neo4j

# Check status
docker-compose ps

# Reset database (clear all data)
docker-compose exec neo4j cypher-shell -u neo4j -p testpassword "MATCH (n) DETACH DELETE n"
```

For more details, see `docker-compose.README.md`.

## Troubleshooting

### Neo4j Connection Issues

1. **Verify Neo4j is running:**
   ```bash
   # Check Docker container status
   docker-compose ps
   
   # Should show "healthy" status
   # If not, check logs:
   docker-compose logs neo4j
   ```

2. **Check if ports are available:**
   ```bash
   # Windows
   netstat -ano | findstr :7687
   
   # Linux/Mac
   lsof -i :7687
   ```

3. **Check connection credentials in `.env` file** (must match `docker-compose.yml`)

4. **Test connection manually:**
   ```bash
   # Access Neo4j Browser
   # Open http://localhost:7474
   # Login: neo4j / testpassword
   ```

5. **Reset everything (fresh start):**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Test Failures

1. Check test output for specific error messages
2. Verify environment variables are set correctly
3. Ensure Neo4j database is accessible
4. Check test data isolation (group_id)

### Import Errors

1. Ensure virtual environment is activated
2. Verify dependencies are installed: `pip list`
3. Check Python path: `python -c "import sys; print(sys.path)"`


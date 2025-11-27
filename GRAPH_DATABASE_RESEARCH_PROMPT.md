# Graph Database Research Prompt - Comprehensive Analysis

## Research Objectives

We need to understand the following aspects of graph databases (specifically Neo4j and Graphiti implementation):

### 1. Data Storage Fundamentals
- How is data stored in graph databases (nodes, relationships, properties)?
- What are the internal structures and how do they differ from relational databases?
- How are UUIDs/hash numbers used for nodes and relationships?
- What is the difference between relationship types and relationship properties?

### 2. Relationship Types and Implementation
- How do different relationship types work (MENTIONS, RELATES_TO, HAS_MEMBER)?
- Why might relationships not appear together when querying?
- How to query multiple relationship types simultaneously?
- Best practices for relationship type design in Neo4j

### 3. Node and Relationship Operations
- How to add new nodes to an existing graph?
- How to add new relationships between existing nodes?
- How to reuse existing relationships?
- How to update relationships without creating duplicates?

### 4. Backup and Restore Operations
- What are the backup strategies for Neo4j graph databases?
- How to backup before making changes?
- How to restore from backup?
- Production backup best practices

### 5. Production Best Practices
- What are critical considerations for production graph databases?
- Performance optimization strategies
- Data integrity and consistency
- Monitoring and maintenance

## Specific Issues to Investigate

### Issue 1: Hash Numbers and Relationships
- When clicking on hash numbers/relationships, not all relationships appear
- MENTIONS relationships work sometimes
- RELATES_TO relationships work sometimes
- They don't work together

### Issue 2: Relationship Querying
- How to query all relationship types for a node?
- Why might some relationships be missing from queries?
- How to ensure all relationships are retrieved?

## Current Implementation Context

From codebase analysis:
- Using Neo4j as the graph database
- Nodes have UUIDs (hash numbers)
- Relationships use generic `RELATIONSHIP` type with `relationship_type` property
- Different relationship types: MENTIONS, RELATES_TO, HAS_MEMBER
- Group-based multi-tenancy with `group_id`


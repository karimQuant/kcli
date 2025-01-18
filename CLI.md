# CLI Commands

## Document Management

### `kcli web <url>`
Crawls and adds web content to the knowledge base.

**Usage:**
```bash
kcli web https://example.com
```

**Features:**
- Respects robots.txt
- Converts HTML to markdown
- Extracts main content
- Stores metadata (source URL, timestamp)
- Generates embeddings for search

## Search

### `kcli search <query>`
Performs semantic search across the knowledge base.

**Usage:**
```bash
kcli search "how to implement authentication"
```

**Features:**
- Uses hnswlib for fast approximate nearest neighbor search
- Returns concatenated markdown of relevant documents
- Results ordered by relevance score
- Includes source metadata
- Highlights matching sections

**Output Format:**
```markdown
# Search Results for: "query"

## Document 1 (Score: 0.89)
Source: https://example.com/doc1
Added: 2023-08-10

[Content...]

---

## Document 2 (Score: 0.76)
Source: https://example.com/doc2
Added: 2023-08-09

[Content...]
```

## Utilities

### `kcli stats`
Displays knowledge base statistics.

**Usage:**
```bash
kcli stats
```

**Output:**
```
Knowledge Base Statistics
------------------------
Total Documents: 125
Storage Size: 45.2 MB
Embedding Size: 128.5 MB
Last Updated: 2023-08-10 15:30 UTC
Document Types:
  - Web Pages: 89
  - Local Files: 36
```

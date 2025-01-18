# Implementation Details

## Project Structure

```
kcli/
├── pyproject.toml         # Project configuration and dependencies
├── README.md             # Project documentation
├── CLI.md               # CLI usage documentation
├── kcli/                # Main package directory
│   ├── __init__.py      # Version and package initialization
│   ├── cli.py           # Click-based CLI implementation
│   ├── crawler.py       # Web crawling and HTML processing
│   ├── storage.py       # Vector database management
│   ├── embeddings.py    # LangChain embedding operations
│   └── utils/           # Utility modules
│       ├── __init__.py
│       └── markdown.py  # Markdown conversion utilities
└── tests/               # Test directory
    ├── __init__.py
    ├── test_cli.py
    ├── test_crawler.py
    ├── test_storage.py
    └── fixtures/        # Test data
```

## Core Components

### Crawler (`crawler.py`)
- **Purpose**: Fetches and processes web content
- **Key Functions**:
  - `process_url(url: str) -> Document`: Main entry point for URL processing
  - `fetch_content(url: str) -> str`: Handles HTTP requests with retry logic
  - `convert_to_markdown(html: str) -> str`: HTML to Markdown conversion
- **Dependencies**: 
  - requests: URL fetching
  - markdownify: HTML to Markdown conversion
  - beautifulsoup4: HTML parsing

### Storage (`storage.py`)
- **Purpose**: Manages metadata storage and hnswlib index operations
- **Key Functions**:
  - `store_document(doc: Document)`: Saves document metadata to SQLite and vector to hnswlib index
  - `search(query: str, limit: int) -> List[Document]`: Performs similarity search using hnswlib
  - `get_stats() -> Dict`: Database statistics
- **Dependencies**:
  - sqlite3: Metadata storage
  - hnswlib: Approximate nearest neighbor search for vector similarity
  - numpy: Vector operations

### Embeddings (`embeddings.py`)
- **Purpose**: Handles text-to-vector conversions
- **Key Functions**:
  - `create_embeddings(text: str) -> np.ndarray`: Generates embeddings
  - `batch_embed(texts: List[str]) -> List[np.ndarray]`: Batch processing
- **Dependencies**:
  - langchain: Embedding models
  - numpy: Vector operations

### CLI (`cli.py`)
- **Purpose**: Command-line interface implementation
- **Commands**:
  - `web`: URL crawling and storage
  - `search`: Knowledge base querying
  - `stats`: System statistics
- **Dependencies**:
  - click: CLI framework
  - rich: Terminal formatting

### Utilities (`utils/markdown.py`)
- **Purpose**: Markdown processing utilities
- **Key Functions**:
  - `clean_markdown(md: str) -> str`: Standardizes markdown format
  - `extract_metadata(md: str) -> Dict`: Parses document metadata
- **Dependencies**:
  - markdownify: HTML conversion

## Data Flow

1. **Document Ingestion**:
   ```python
   url -> crawler.process_url() -> Document
   -> embeddings.create_embeddings() -> Vector
   -> storage.store_document()
   ```

2. **Search Process**:
   ```python
   query -> embeddings.create_embeddings() -> Vector
   -> storage.search() -> List[Document] using hnswlib
   -> cli.format_results() -> Output
   ```

## Data Models

```python
@dataclass
class Document:
    content: str
    url: Optional[str]
    title: str
    created_at: datetime
    embedding: Optional[np.ndarray]
    metadata: Dict[str, Any]
```

## Configuration

- Database location: `~/.kcli/knowledge.db` (for metadata)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Vector dimensions: 384
- Chunk size: 512 tokens
- hnswlib index location: `~/.kcli/index.ann`

## Development Guidelines

1. Use type hints
2. Follow black code formatting
3. Validate with ruff
4. Write tests for all components
5. Document public APIs

# Testing
All tests are cli tests where we run each command ,
the tests can rely on local md file artifacts to check results are matching.
When the test run we always change the path of the db to a test_db ander .config/kcli folder.
the database should be created in the beginning of the test suite and removed at the end.

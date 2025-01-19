from datetime import datetime
from typing import Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

from kcli.embeddings import embeddings
from kcli.log import console
from kcli.storage import Document


async def process_url(url: str) -> Optional[Document]:
    """Processes a URL using crawl4ai, fetches content, converts to Markdown, and returns a Document."""
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
    )
    try:
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=url,
                config=run_config,
            )
            if not result or not result.markdown:
                console.log(f"Failed to crawl or extract content from {url}",)
                return None
            embedding = embeddings.create_embeddings(result.markdown)
            doc = Document(
                content=result.markdown,
                url=url,
                title=result.metadata.get('title',''),
                created_at=datetime.now(),
                embedding=embedding,
                meta={"source": "web"},
            )
            console.log(f" Retreived : {url}")
            return doc
    except Exception as e:
        console.log(f"Error processing URL {url}: {e}")
        return None


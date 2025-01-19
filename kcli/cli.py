"""CLI implementation for kcli."""

import click
from rich.table import Table

from kcli.log import console
from kcli.main import add_file, crawl_web_content, get_knowledge_base_stats, search_knowledge_base


@click.group()
@click.version_option()
def main():
    """KCLI - Local Knowledge Base CLI."""
    pass

@main.command()
@click.argument('url')
def web(url):
    """Crawl and add web content to knowledge base."""
    console.print(f"Crawling {url}...")
    crawl_web_content(url)

@main.command()
@click.argument('query')
def search(query):
    """Search the knowledge base."""
    console.print(f"Searching for: {query}")
    search_knowledge_base(query)

@main.command()
@click.argument('file_path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
def add(file_path):
    """Add a local file to the knowledge base."""
    console.log(f"Adding file: {file_path}")
    add_file(file_path)


@main.command()
def stats():
    """Display knowledge base statistics."""
    table = Table(title="Knowledge Base Statistics")
    table.add_column("Metric")
    table.add_column("Value")
    get_knowledge_base_stats()
    console.print(table)

if __name__ == '__main__':
    main()

"""Unit tests for HTMLExtractor."""

from src.crawler.extractors.html_extractor import HTMLExtractor


def test_html_extractor_elements() -> None:
    """Verifies complete structural extraction from HTML markup."""
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Portfolio Extractor Test</title>
        <meta name="description" content="Awesome web scraper test description">
    </head>
    <body>
        <h1>Welcome to Scraper</h1>
        <h2>Features Section</h2>
        <p>Paragraph 1 text content.</p>
        <p>Paragraph 2 text content.</p>
        <ul>
            <li>Feature A</li>
            <li>Feature B</li>
        </ul>
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        <img src="/static/logo.png" alt="Company Logo">
        <a href="/docs/guide">Documentation</a>
        <a href="https://github.com/project">GitHub Repo</a>
    </body>
    </html>
    """

    extractor = HTMLExtractor()
    dto = extractor.parse(sample_html, "https://example.com/home")

    assert dto.title == "Portfolio Extractor Test"
    assert dto.meta_description == "Awesome web scraper test description"
    assert dto.headings == {"h1": ["Welcome to Scraper"], "h2": ["Features Section"]}
    assert len(dto.paragraphs) == 2
    assert dto.paragraphs[0] == "Paragraph 1 text content."
    assert len(dto.lists) == 1
    assert dto.lists[0] == ["Feature A", "Feature B"]
    assert len(dto.tables) == 1
    assert dto.tables[0] == [["Header 1", "Header 2"], ["Cell 1", "Cell 2"]]
    assert len(dto.images) == 1
    assert dto.images[0]["image_url"] == "https://example.com/static/logo.png"
    assert dto.images[0]["alt_text"] == "Company Logo"

    assert len(dto.internal_links) == 1
    assert dto.internal_links[0]["target_url"] == "https://example.com/docs/guide"
    assert dto.internal_links[0]["is_external"] is False

    assert len(dto.external_links) == 1
    assert dto.external_links[0]["target_url"] == "https://github.com/project"
    assert dto.external_links[0]["is_external"] is True

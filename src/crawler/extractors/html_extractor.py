"""HTML Structural Parser and Feature Extractor Engine.

Parses raw HTML documents using BeautifulSoup4 and LXML to extract page title,
meta description, headings (H1-H6), paragraphs, lists, tables, images, and links.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from src.core.logging import logger
from src.utils.url_utils import is_external_link, resolve_absolute_url


@dataclass
class ExtractedContentDTO:
    """Data transfer object containing all structured elements extracted from HTML."""

    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: Dict[str, List[str]] = field(default_factory=dict)
    paragraphs: List[str] = field(default_factory=list)
    lists: List[List[str]] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    images: List[Dict[str, Optional[str]]] = field(default_factory=list)
    internal_links: List[Dict[str, Any]] = field(default_factory=list)
    external_links: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class HTMLExtractor:
    """Robust HTML document extractor built on BeautifulSoup4."""

    def __init__(self, parser: str = "lxml") -> None:
        self.parser = parser

    def parse(self, html: str, page_url: str) -> ExtractedContentDTO:
        """Parses HTML markup and extracts all target structural elements.

        Args:
            html (str): Raw HTML document string.
            page_url (str): Absolute base URL of the current page.

        Returns:
            ExtractedContentDTO: Structured data payload.
        """
        dto = ExtractedContentDTO(url=page_url)
        if not html or not html.strip():
            return dto

        try:
            soup = BeautifulSoup(html, self.parser)
        except Exception:
            # Fallback to standard html.parser if lxml fails
            soup = BeautifulSoup(html, "html.parser")

        # 1. Page Title
        title_tag = soup.find("title")
        if title_tag:
            extracted_title = title_tag.get_text(strip=True)
            if extracted_title:
                dto.title = extracted_title

        # 2. Meta Description
        meta_desc = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
        if meta_desc and meta_desc.get("content"):
            extracted_desc = str(meta_desc.get("content")).strip()
            if extracted_desc:
                dto.meta_description = extracted_desc

        # 3. Headings H1 to H6
        headings_dict: Dict[str, List[str]] = {}
        for level in range(1, 7):
            tag_name = f"h{level}"
            found_tags = soup.find_all(tag_name)
            texts = [t.get_text(strip=True) for t in found_tags if t.get_text(strip=True)]
            if texts:
                headings_dict[tag_name] = texts
        dto.headings = headings_dict

        # 4. Paragraphs
        paragraph_tags = soup.find_all("p")
        dto.paragraphs = [
            p.get_text(strip=True) for p in paragraph_tags if p.get_text(strip=True)
        ]

        # 5. Lists (unordered & ordered)
        lists_data: List[List[str]] = []
        for list_tag in soup.find_all(["ul", "ol"]):
            items = [
                li.get_text(strip=True)
                for li in list_tag.find_all("li", recursive=False)
                if li.get_text(strip=True)
            ]
            if items:
                lists_data.append(items)
        dto.lists = lists_data

        # 6. Tables
        tables_data: List[List[List[str]]] = []
        for table in soup.find_all("table"):
            table_rows: List[List[str]] = []
            for tr in table.find_all("tr"):
                cells = [
                    cell.get_text(strip=True)
                    for cell in tr.find_all(["th", "td"])
                    if cell.get_text(strip=True)
                ]
                if cells:
                    table_rows.append(cells)
            if table_rows:
                tables_data.append(table_rows)
        dto.tables = tables_data

        # 7. Images & Alt Texts
        seen_images = set()
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src:
                continue
            abs_img_url = resolve_absolute_url(page_url, str(src))
            if abs_img_url not in seen_images:
                seen_images.add(abs_img_url)
                alt_text = img.get("alt")
                dto.images.append({
                    "image_url": abs_img_url,
                    "alt_text": str(alt_text).strip() if alt_text else None,
                })

        # 8. Hyperlinks (Internal vs External)
        seen_links = set()
        for anchor in soup.find_all("a"):
            href = anchor.get("href")
            if not href or str(href).startswith(("javascript:", "mailto:", "tel:", "#")):
                continue

            try:
                abs_link_url = resolve_absolute_url(page_url, str(href))
            except Exception:
                continue

            if abs_link_url in seen_links:
                continue
            seen_links.add(abs_link_url)

            anchor_text = anchor.get_text(strip=True) or None
            is_ext = is_external_link(page_url, abs_link_url)

            link_obj = {
                "source_url": page_url,
                "target_url": abs_link_url,
                "anchor_text": anchor_text,
                "is_external": is_ext,
            }

            if is_ext:
                dto.external_links.append(link_obj)
            else:
                dto.internal_links.append(link_obj)

        return dto

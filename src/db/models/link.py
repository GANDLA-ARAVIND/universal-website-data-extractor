"""PageLink ORM Model.

Stores internal and external hyperlinks discovered on an extracted web page.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.page import ExtractedPage


class PageLink(Base):
    """PageLink entity representing anchor links extracted from a page."""

    __tablename__ = "page_links"

    page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extracted_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    anchor_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_external: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    page: Mapped["ExtractedPage"] = relationship("ExtractedPage", back_populates="links")

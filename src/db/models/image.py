"""PageImage ORM Model.

Stores image assets and associated alt-text metadata extracted from a web page.
"""

import uuid
from typing import TYPE_CHECKING, Optional
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.page import ExtractedPage


class PageImage(Base):
    """PageImage entity representing HTML img tags extracted from a page."""

    __tablename__ = "page_images"

    page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extracted_pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    alt_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    page: Mapped["ExtractedPage"] = relationship("ExtractedPage", back_populates="images")

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.data.db_session import Base  # Importing Base from the central session file

class PDFMetadata(Base):
    """
    Stores high-level information about the PDF document.
    """
    __tablename__ = "pdf_metadata"
    
    id = Column(Integer, primary_key=True)
    pmid = Column(String, unique=True, index=True)
    title = Column(String)
    file_path = Column(String)
    processed = Column(Boolean, default=False)
    
    # Relationship to features
    features = relationship("LayoutFeatures", back_populates="pdf", cascade="all, delete-orphan")

class LayoutFeatures(Base):
    """
    Stores extracted layout features.
    CHANGED: Optimized to store Line-level data instead of Span-level data
    to reduce noise and text overlapping in reconstruction.
    """
    __tablename__ = "layout_features"
    
    id = Column(Integer, primary_key=True)
    pdf_id = Column(Integer, ForeignKey("pdf_metadata.id"))
    
    text_content = Column(String)
    font_size = Column(Float)
    
    # Style flags
    is_bold = Column(Boolean)
    is_italic = Column(Boolean, default=False)
    
    # Coordinates (Bbox)
    x0 = Column(Float)
    y0 = Column(Float)
    width = Column(Float)  # Added: Crucial for LaTeX textblock width
    height = Column(Float) # Added: Useful for density calculations
    
    page_number = Column(Integer)
    is_image = Column(Boolean, default=False)
    
    # The target label for training (title, header, body, footer, image)
    label = Column(String)
    
    pdf = relationship("PDFMetadata", back_populates="features")
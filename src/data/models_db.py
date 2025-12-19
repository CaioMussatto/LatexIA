from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class PDFMetadata(Base):
    __tablename__ = "pdf_metadata"
    id = Column(Integer, primary_key=True)
    pmid = Column(String, unique=True)
    title = Column(String)
    file_path = Column(String)
    processed = Column(Boolean, default=False)

class LayoutFeatures(Base):
    __tablename__ = "layout_features"
    id = Column(Integer, primary_key=True)
    pdf_id = Column(Integer, ForeignKey("pdf_metadata.id"))
    text_content = Column(String)
    font_size = Column(Float)
    is_bold = Column(Boolean)
    is_italic = Column(Boolean, default=False)
    x0 = Column(Float)
    y0 = Column(Float)
    page_number = Column(Integer) # ADICIONADO AQUI
    is_image = Column(Boolean, default=False)
    label = Column(String)

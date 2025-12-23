import fitz
import requests
import logging
from collections import Counter
from src.data.db_session import SessionLocal, init_db
from src.data.models_db import PDFMetadata, LayoutFeatures

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def sanitize_text(text):
    """Removes NUL bytes which crash the database driver."""
    if not text:
        return ""
    return text.replace('\x00', '')

def get_direct_pdf_url(pmcid):
    """Retrieves the direct PDF download link from PMC OA API."""
    api_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC{pmcid}"
    try:
        import xml.etree.ElementTree as ET
        r = requests.get(api_url, timeout=15)
        root = ET.fromstring(r.text)
        for link in root.findall(".//link"):
            if link.get("format") == "pdf":
                return link.get("href").replace("ftp://", "https://")
    except Exception as e:
        logger.warning(f"Failed to get URL for PMC{pmcid}: {e}")
    return None

def heuristic_labeling(text, size, is_bold, x0, y0, width, page_width, page_height):
    """
    Labels text segments based on rules (heuristics) to create training data.
    """
    text = text.strip()
    if not text: return "garbage"
    
    # Geometry-based rules
    is_wide = width > (page_width * 0.7)
    
    # 1. Footer/Header (based on Y position)
    if y0 > page_height * 0.93: return "footer"
    if y0 < page_height * 0.08: return "header"
    
    # 2. Titles (Large, usually centered or short & bold)
    if size > 16: return "title"
    
    # 3. Headers (Bold, medium size, not a full paragraph width)
    if size > 10 and is_bold and not is_wide: return "header"
    
    # 4. Body (Standard size, usually wide)
    if size < 12 and is_wide: return "body"
    
    return "body"

def process_and_label():
    """
    Downloads PDFs, extracts layout features at the LINE level, and saves to DB.
    """
    init_db() # Ensure tables exist
    db = SessionLocal()
    
    pdfs = db.query(PDFMetadata).filter(PDFMetadata.processed == False).all()
    layout_monitor = Counter()
    
    total_files = len(pdfs)
    logger.info(f"Starting processing: {total_files} files queued.")

    for index, pdf in enumerate(pdfs, 1):
        url = get_direct_pdf_url(pdf.pmid)
        current_pmid = pdf.pmid # Store locally to use in exception block safely
        
        if not url: 
            logger.warning(f"[{index}/{total_files}] No URL for PMC{current_pmid}")
            continue
            
        try:
            logger.info(f"Downloading PMC{current_pmid}...")
            response = requests.get(url, timeout=30)
            doc = fitz.open(stream=response.content, filetype="pdf")
            
            new_features = []
            
            for page_num, page in enumerate(doc):
                _, _, page_w, page_h = page.rect
                blocks = page.get_text("dict")["blocks"]
                
                for b in blocks:
                    # IMAGE BLOCK
                    if b["type"] == 1:
                        new_features.append(LayoutFeatures(
                            pdf_id=pdf.id, is_image=True,
                            x0=round(b["bbox"][0], 2), y0=round(b["bbox"][1], 2),
                            width=round(b["bbox"][2]-b["bbox"][0], 2),
                            height=round(b["bbox"][3]-b["bbox"][1], 2),
                            page_number=page_num, label="image"
                        ))
                        layout_monitor.update(["image"])
                        continue

                    # TEXT BLOCK
                    if "lines" in b:
                        for l in b["lines"]:
                            # --- AGGREGATE SPANS INTO A SINGLE LINE ---
                            line_text_parts = []
                            sizes = []
                            bolds = []
                            
                            for s in l["spans"]:
                                line_text_parts.append(s["text"])
                                sizes.append(s["size"])
                                bolds.append("bold" in s["font"].lower())
                            
                            full_text = " ".join(line_text_parts).strip()
                            full_text = sanitize_text(full_text) # <--- FIX APPLIED HERE
                            
                            if not full_text: continue

                            # Calculate Line Attributes
                            avg_size = sum(sizes) / len(sizes)
                            is_bold = sum(bolds) > (len(bolds) / 2)
                            x0, y0, x1, y1 = l["bbox"]
                            width = x1 - x0
                            height = y1 - y0
                            
                            # Heuristic Labeling
                            label = heuristic_labeling(full_text, avg_size, is_bold, x0, y0, width, page_w, page_h)

                            new_features.append(LayoutFeatures(
                                pdf_id=pdf.id,
                                text_content=full_text[:1000], # Truncate if huge
                                font_size=round(avg_size, 2),
                                is_bold=is_bold,
                                x0=round(x0, 2), y0=round(y0, 2),
                                width=round(width, 2),
                                height=round(height, 2),
                                page_number=page_num, label=label
                            ))
                            layout_monitor.update([label])
            
            if new_features:
                db.bulk_save_objects(new_features)

            pdf.processed = True
            db.commit()
            logger.info(f"[{index}/{total_files}] Processed PMC{current_pmid}")
            
        except Exception as e:
            # Rollback first to clean the session state
            db.rollback()
            logger.error(f"Error processing PMC{current_pmid}: {e}")

    logger.info("\n--- Class Distribution ---")
    for cls, count in layout_monitor.most_common():
        logger.info(f"{cls}: {count}")
    
    db.close()

if __name__ == "__main__":
    process_and_label()
import fitz
import requests
import xml.etree.ElementTree as ET
from collections import Counter
from src.data.db_session import SessionLocal
from src.data.models_db import PDFMetadata, LayoutFeatures

def get_direct_pdf_url(pmcid):
    api_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC{pmcid}"
    try:
        r = requests.get(api_url, timeout=15)
        root = ET.fromstring(r.text)
        for link in root.findall(".//link"):
            if link.get("format") == "pdf":
                return link.get("href").replace("ftp://", "https://")
    except: return None
    return None

def heuristic_labeling(text, size, is_bold):
    if size > 16: return "title"
    if size > 11 and is_bold: return "header"
    if size < 9: return "footer"
    return "body"

def process_and_label():
    db = SessionLocal()
    pdfs = db.query(PDFMetadata).filter(PDFMetadata.processed == False).all()
    layout_monitor = Counter()
    
    total_files = len(pdfs)
    print(f"Starting processing: {total_files} files identified for structure classification")

    for index, pdf in enumerate(pdfs, 1):
        url = get_direct_pdf_url(pdf.pmid)
        if not url: 
            print(f"[{index}/{total_files}] Warning: Direct URL not found for PMC{pdf.pmid}")
            continue
        try:
            response = requests.get(url, timeout=30)
            doc = fitz.open(stream=response.content, filetype="pdf")
            
            for page_num, page in enumerate(doc):
                blocks = page.get_text("dict")["blocks"]
                for b in blocks:
                    if b["type"] == 1:
                        db.add(LayoutFeatures(
                            pdf_id=pdf.id, is_image=True,
                            x0=round(b["bbox"][0], 2), y0=round(b["bbox"][1], 2),
                            page_number=page_num, label="image"
                        ))
                        layout_monitor.update(["image"])
                        continue

                    if "lines" in b:
                        for l in b["lines"]:
                            for s in l["spans"]:
                                label = heuristic_labeling(s["text"], s["size"], "bold" in s["font"].lower())
                                db.add(LayoutFeatures(
                                    pdf_id=pdf.id,
                                    text_content=s["text"][:500],
                                    font_size=round(s["size"], 2),
                                    is_bold="bold" in s["font"].lower(),
                                    x0=round(s["bbox"][0], 2), y0=round(s["bbox"][1], 2),
                                    page_number=page_num, label=label
                                ))
                                layout_monitor.update([label])
            
            pdf.processed = True
            db.commit()
            print(f"[{index}/{total_files}] Processed: PMC{pdf.pmid}")
        except Exception as e:
            print(f"[{index}/{total_files}] Error processing PMC{pdf.pmid}: {e}")
            db.rollback()

    print("\nStructure Monitoring Summary (Training Classes)")
    for cls, count in layout_monitor.most_common():
        print(f"Class: {cls:<10} | Total Blocks: {count}")
    
    db.close()

if __name__ == "__main__":
    process_and_label()
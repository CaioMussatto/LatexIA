import requests
import xml.etree.ElementTree as ET
from src.data.db_session import SessionLocal
from src.data.models_db import PDFMetadata

def seed_massive_diverse_pdfs():
    terms = [
        "physics", "law", "economics", "engineering", "history", "biology", "mathematics", "sociology", 
        "chemistry", "philosophy", "psychology", "archaeology", "astronomy", "linguistics", "geology", 
        "medicine", "architecture", "politics", "art", "music", "literature", "ecology", "robotics", 
        "nanotechnology", "genetics", "neuroscience", "anthropology", "theology", "agriculture", 
        "cryptography", "paleontology", "meteorology", "oceanography", "robotics", "aeronautics", 
        "marketing", "journalism", "dentistry", "veterinary", "pharmacy", "nursing", "criminology", 
        "ethics", "pedagogy", "statistics", "metallurgy", "toxicology", "virology", "botany", "zoology",
        "hydrology", "seismology", "optics", "acoustics", "thermodynamics", "microbiology", "immunology", 
        "pathology", "epidemiology", "dermatology", "radiology", "surgery", "oncology", "pediatrics", 
        "geriatrics", "psychiatry", "neurology", "cardiology", "endocrinology", "orthopedics", 
        "urology", "gynecology", "ophthalmology", "otolaryngology", "gastronomy", "fashion", "forestry",
        "mining", "logistics", "management", "accounting", "banking", "insurance", "real estate",
        "transportation", "telecommunications", "energy", "environment", "climatology", "urbanism",
        "human rights", "international relations", "globalization", "cybersecurity", "blockchain",
        "artificial intelligence", "data science", "quantum computing", "biotechnology", "space exploration"
    ]
    
    db = SessionLocal()
    total_terms = len(terms)
    print(f"Starting metadata collection for {total_terms} areas")

    for index, term in enumerate(terms, 1):
        try:
            api_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={term}&retmax=10"
            r = requests.get(api_url, timeout=10)
            root = ET.fromstring(r.text)
            ids = [id_elem.text for id_elem in root.findall(".//Id")]
            
            new_count = 0
            for pmid in ids:
                exists = db.query(PDFMetadata).filter(PDFMetadata.pmid == pmid).first()
                if not exists:
                    db.add(PDFMetadata(pmid=pmid, processed=False))
                    new_count += 1
            
            db.commit()
            if new_count > 0:
                print(f"[{index}/{total_terms}] {term.capitalize()}: {new_count} new PDFs added.")
                
        except Exception as e:
            print(f"[{index}/{total_terms}] Error searching {term}: {e}")
            db.rollback()
            continue
            
    db.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed_massive_diverse_pdfs()
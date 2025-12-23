import requests
import logging
import xml.etree.ElementTree as ET
from src.data.db_session import SessionLocal, init_db
from src.data.models_db import PDFMetadata

# Setup professional logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def seed_massive_diverse_pdfs():
    """
    Searches PubMed Central (PMC) for diverse topics and seeds the database
    with PDF metadata (PMIDs) for later processing.
    """
    # 1. Initialize the database (Create tables if they don't exist)
    init_db()

    terms = [
        "physics", "law", "economics", "engineering", "history", "biology", "mathematics", "sociology", 
        "chemistry", "philosophy", "psychology", "archaeology", "astronomy", "linguistics", "geology", 
        "medicine", "architecture", "politics", "art", "music", "literature", "ecology", "robotics", 
        "nanotechnology", "genetics", "neuroscience", "anthropology", "theology", "agriculture", 
        "cryptography", "paleontology", "meteorology", "oceanography", "aeronautics", 
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
    logger.info(f"Starting metadata collection for {total_terms} areas")

    for index, term in enumerate(terms, 1):
        try:
            # Fetch PMIDs from NCBI
            api_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term={term}&retmax=10"
            r = requests.get(api_url, timeout=10)
            root = ET.fromstring(r.text)
            ids = [id_elem.text for id_elem in root.findall(".//Id")]
            
            new_count = 0
            for pmid in ids:
                # Check if already exists to avoid duplicates
                exists = db.query(PDFMetadata).filter(PDFMetadata.pmid == pmid).first()
                if not exists:
                    db.add(PDFMetadata(pmid=pmid, processed=False))
                    new_count += 1
            
            db.commit()
            if new_count > 0:
                logger.info(f"[{index}/{total_terms}] {term.capitalize()}: {new_count} new PDFs added.")
                
        except Exception as e:
            logger.error(f"[{index}/{total_terms}] Error searching {term}: {e}")
            db.rollback()
            continue
            
    db.close()
    logger.info("Database seeding completed.")

if __name__ == "__main__":
    seed_massive_diverse_pdfs()
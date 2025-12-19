# LaTeX.IA: Cloud-Native PDF-to-LaTeX Layout Reconstruction

LaTeX.IA is a high-performance machine learning pipeline designed to resolve the structural loss inherent in PDF-to-text conversions. By combining spatial analysis with a cloud-integrated Random Forest classifier, the system identifies document hierarchies (Titles, Headers, Body) and reconstructs them into high-fidelity, editable LaTeX code.

The project follows a **Stateless Architecture** and is delivered as a pre-configured containerized service for a zero-setup user experience.

---

## 🏗️ System Architecture & Engineering

The pipeline is built on four core technical pillars:

### 1. Cloud-Integrated Data Engineering (Supabase)
* **Unified Persistence:** All extracted document features—spatial coordinates, font metadata, and text blocks—are stored in a centralized **Supabase (PostgreSQL)** instance.
* **Redundancy Control:** A database-level status flag system indexes processed documents, preventing redundant computational load and optimizing cloud I/O.
* **Stateless Training:** The training module fetches data directly via SQLAlchemy, performing all feature engineering in memory to maintain a clean environment.

### 2. Feature Engineering & Intelligence
* **Contextual Features:** The model utilizes calculated metrics such as `rel_font_size` (normalized against page average) and `center_dev` (horizontal alignment analysis) to improve prediction accuracy.
* **Random Forest Classifier:** A robust ML model trained to classify text blocks into structural roles based on their typographic and spatial signatures.
* **Dynamic Model Sync:** The inference engine synchronizes model weights from **Supabase Storage** on startup, allowing for updates without redeploying the container.

### 3. Absolute Layout Reconstruction
* **Precision Mapping:** Instead of standard text flow, the system utilizes the LaTeX `textpos` package to map predicted coordinates onto a coordinate system, ensuring visual parity with the source PDF.
* **Anonymization Logic:** Integrated text processing to handle document reconstruction while maintaining layout integrity.

### 4. Containerization & DevOps (Docker)
* **Encapsulated Security:** Cloud credentials and API endpoints are injected during the build process, ensuring they remain internal to the container and hidden from the end-user.
* **ARM64 Optimization:** Specifically tuned for Linux ARM64 environments.
* **User Mapping:** Automatic UID/GID synchronization to prevent permission conflicts on the host system.

---

## 🐳 Deployment and Usage

The service is designed for immediate execution with zero manual configuration.



### Commands

**1. Build the Environment**
This initializes the engine and prepares the container:
```bash
docker compose build
```

**2. Process Documents**
Place your source PDF files in the `data/raw/` directory.

```bash
# Process default document (teste.pdf)
docker compose up

# Process a specific file
FILE=my_document.pdf docker compose up

```

**3. Output**
The generated `.tex` files are saved to the local `./output/` folder via persistent volumes.

---

## 📂 Project Structure

* `src/data/`: Cloud database schemas and SQLAlchemy session management.
* `src/models/trainer.py`: Cloud-to-model training pipeline.
* `src/models/inference.py`: Core prediction engine and LaTeX generation logic.
* `data/raw/`: Input directory for source PDFs.
* `output/`: Output directory for generated LaTeX files.
* `Dockerfile` & `docker-compose.yml`: Production orchestration.

---

## 👤 Author

**Caio Mussatto** - [Caio.mussatto@gmail.com](mailto:Caio.mussatto@gmail.com)

---

*Licensed under the MIT License.*

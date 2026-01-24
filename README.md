# LaTeX.IA: Single-Page Academic Layout Reconstructor
![Python](https://img.shields.io/badge/python-3.13-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![UV](https://img.shields.io/badge/UV-0.9-blue.svg?style=for-the-badge&logo=python&logoColor=white)

LaTeX.IA is a high-performance machine learning pipeline designed to reconstruct complex document layouts into high-fidelity, editable LaTeX code. By leveraging spatial analysis and a pre-trained **Random Forest** classifier, the system intelligently positions images, tables, and text blocks to fit perfectly within a single-page academic constraint.

The project is delivered as a **Dockerized Microservice**, optimized for lightness and portability, featuring a fully integrated **TinyTeX** environment.

---

## Technical Architecture

The pipeline is built on four core technical pillars:

### 1. Hybrid Environment Logic (Local & Docker)

* **Dual-Mode Execution:** The engine automatically detects its environment. It dynamically maps paths whether running natively on a host (Linux/Debian) or inside a container.
* **Stateless Inference:** The core logic treats each layout generation as a stateless transaction, ensuring consistency across multiple runs.
* **Permission Shield:** Automatic directory permission handling (`chmod 0777`) to prevent UID/GID conflicts between the Docker root user and the host user.

### 2. ML Intelligence & Layout Engine

* **Random Forest Classifier:** Uses typographic and spatial signatures (font size, coordinates, alignment) to predict the structural role of each document element.
* **Component-Based Generation:** Support for multiple layout architectures:
* `Full`: Standard two-column academic flow.
* `Top/Bottom/Middle`: Horizontal component insertion with text wrapping.
* `Left/Right`: Lateral positioning using the `wrapfig` LaTeX package.



### 3. Optimized TeX Stack

* **Ultra-Lean TinyTeX:** Instead of the full 5GB TeXLive, the container uses a custom-built **TinyTeX** footprint (~150MB), containing only the essential packages (`multicol`, `tcolorbox`, `microtype`, etc.).
* **Auto-Cleanup:** Build-stage optimization that purges compiler logs and temporary build artifacts to keep the image size at a minimum.

### 4. Persistence & I/O

* **Local Database Mode:** Optimized for local development, utilizing a SQLite architecture for feature storage, removing the overhead of cloud latency.
* **Versioned Models:** Models are stored in `src/models/export/`, ensuring the "brain" of the engine is versioned alongside the code.

---

## Getting Started

### Prerequisites

* Docker & Docker Compose
* Python 3.13+ (if running locally)

### Commands

**1. Build the Engine**
Optimizes the image and installs the TeX environment:

```bash
docker compose build --no-cache

```

**2. Generate Layouts (Docker)**
Pass the layout type and position as arguments:

```bash
# Generate a bottom-positioned image with middle alignment
docker compose run --rm reconstructor uv run python src/models/inference.py bottom image --pos middle

# Generate a left-positioned table
docker compose run --rm reconstructor uv run python src/models/inference.py left table --pos top

```

**3. Run Locally**

```bash
uv run python src/models/inference.py full image

```

---

## Project Structure

* `src/models/inference.py`: Core engine and LaTeX generation logic.
* `src/models/export/`: Pre-trained `.joblib` model binaries.
* `src/output/`: **Generated Files.** All `.tex` results are saved here.
* `data/`: Local SQLite databases and raw data storage.
* `Dockerfile`: Multi-stage build with TinyTeX optimization.

---

## Author

**Caio Mussatto** - [caio.mussatto@gmail.com](mailto:caio.mussatto@gmail.com)

---

*Licensed under the MIT License.*


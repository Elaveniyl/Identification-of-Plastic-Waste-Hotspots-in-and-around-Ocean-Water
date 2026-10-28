# AI-GIS Detection and Prioritisation of Plastic Waste Hotspots

A unified environmental computing platform integrating **Deep Learning Vision Classification**, **Geographic Information Systems (GIS) Spatial Prioritisation**, and **Formal Languages and Automata (FLA)** theory to identify, rank, and track ocean plastic pollution.

---

## Key Capabilities

1. **Computer Vision Inference (`/object`):**
   - In-memory TensorFlow session loading retrained Inception-v3 graph (`tf_files/retrained_graph.pb`, 83.41 MB).
   - Real-time softmax classification over 6 material classes: `paper`, `metal`, `cardboard`, `trash`, `glass`, `plastic` (taxonomy matches TrashNet; model appears to have been trained on a TrashNet-style dataset).
   - OS-agnostic input normalization ($(1, 299, 299, 3)$, $[-1.0, 1.0]$) accepting JPEG, PNG, and WebP images.
   - *Model Status & Sanity Checks:* No accuracy evaluation was run. Sanity check runs on `ocean.jpg` (seascape), `Home.jpg` (banner), and `asd.jpg` (logo) all predicted "plastic" at 70-97%, demonstrating out-of-distribution overconfidence. These tests served strictly as inference pipeline sanity checks.

2. **GIS Hotspot Prioritisation Engine (`/hotspot`):**
   - Parses 3,532 genuine oceanographic survey tows from Laurent Lebreton et al. (2018), *Scientific Reports*.
   - Computes deterministic **Hotspot Priority Index (HPI)** combining mass concentration, Great Pacific Garbage Patch (GPGP) gyre convergence, and numerical density.
   - Interactive Leaflet geospatial map displaying color-coded priority tiers (Critical, Moderate, Baseline) and macro-accumulation grid clusters.

3. **Formal Languages and Automata (FLA) Engine (`/automata`):**
   - Models the waste observation lifecycle as a formal **Deterministic Finite Automaton (DFA)** $M = (Q, \Sigma, \delta, q_0, F)$ with 8 states, 7 event symbols, and 2 accepting states (`ARCHIVED`, `REJECTED`).
   - Total transition completion via explicit $\text{TRAP}$ state ($\delta_{\text{complete}}$ with 63 total rules).
   - Regular expression derivation via GNFA state elimination (32 distinct accepted words in $L(M)$).
   - Minimality verification under the Myhill-Nerode theorem via partition refinement.
   - Real-time word acceptance endpoint (`POST /api/fsm/accepts`).

4. **Oceanographic Analytics & Visualizations (`/visualizations`):**
   - Embedded historical Tableau analytics (`Master_Project_Tableau.twbx`) depicting longitudinal accumulation trends across the North Pacific Subtropical Gyre.

---

## System Requirements

- **Operating System:** Windows 10/11 x64 (or Linux / macOS)
- **Python Version:** Python 3.13.x (tested on Python 3.13.15)
- **Virtual Environment:** Recommended (`.venv`)

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/parineeta16/Identification-of-Plastic-Waste-Hotspots-in-and-around-Ocean-Water-using-Machine-Learning.git
cd Identification-of-Plastic-Waste-Hotspots-in-and-around-Ocean-Water-using-Machine-Learning-master
```

### 2. Create and Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Modernized Dependencies
```powershell
pip install -r requirements_modern.txt
```

> **Note on Windows Long Path Support:** Native TensorFlow 2.21 wheels on Windows require avoiding C++ header path truncation during wheel unzipping. The application runtime utilizes pure Python bytecode and DLLs, configured out-of-the-box in `.venv`.

---

## Running the Application

Start the local Flask development server:
```powershell
python main.py
```

Access the interactive web portal at: **`http://127.0.0.1:5000`**

### Available Pages:
- **`http://127.0.0.1:5000/`** — Research Overview & Global Impact
- **`http://127.0.0.1:5000/object`** — Deep Learning Plastic Classifier (Drag-and-Drop)
- **`http://127.0.0.1:5000/hotspot`** — Interactive GIS Prioritisation & Map Console
- **`http://127.0.0.1:5000/automata`** — Formal FLA Lifecycle Automaton Simulator
- **`http://127.0.0.1:5000/visualizations`** — Tableau & Oceanographic Analytics
- **`http://127.0.0.1:5000/mission`** — Environmental Mission & SDG 14 Alignment
- **`http://127.0.0.1:5000/team`** — Scientific Contributors & Faculty Advisors

---

## API Reference

| Endpoint | Method | Description | Sample Request / Parameters |
| :--- | :---: | :--- | :--- |
| `/predict` | `GET` | Health check & model diagnostic telemetry | `curl http://127.0.0.1:5000/predict` |
| `/predict` | `POST` | Execute Inception-v3 image classification | JSON: `{"image": "data:image/jpeg;base64,..."}` |
| `/api/hotspots` | `GET` | Retrieve ranked GIS observation records | Query params: `?tier=Critical&inside_gpgp=1&limit=50` |
| `/api/hotspots/stats` | `GET` | Overall dataset statistics & spatial bounds | `curl http://127.0.0.1:5000/api/hotspots/stats` |
| `/api/hotspots/clusters` | `GET` | Spatial grid accumulation clusters | Query param: `?grid_size=5.0` |
| `/api/fsm/spec` | `GET` | Formal 5-tuple specification of DFA | Query param: `?completed=true` (includes TRAP) |
| `/api/fsm/transition` | `POST` | Stepwise atomic state transition | JSON: `{"current_state": "DRAFT", "symbol": "add_coords"}` |
| `/api/fsm/accepts` | `POST` | Evaluate input word $w \in \Sigma^*$ | JSON: `{"symbols": ["add_coords", "classify_image", "operator_verify", "complete_archive"]}` |

---

## Theoretical Automata Analysis (`tools/fsm_analysis.py`)

Run the standalone FLA theoretical verification tool:
```powershell
python tools/fsm_analysis.py
```

This tool automatically executes:
1. Formal 5-tuple dynamic extraction.
2. State reachability analysis (all 8 states reachable).
3. Markdown transition tables (partial domain $\delta$ and total $\delta_{\text{complete}}$ with $\text{TRAP}$).
4. Graphviz DOT and Mermaid state transition diagrams.
5. GNFA state elimination deriving the regular expression $R$ for $L(M)$ (32 paths).
6. Exhaustive verification of Regex vs DFA across 671 empirical test strings (100% agreement).
7. Myhill-Nerode partition refinement proving unlabelled equivalence of `ARCHIVED` and `REJECTED`.

---

## Verification & Automated Test Suite

Run the full automated test suite (17 tests covering DB persistence, routes, GIS, FLA, and CNN inference):
```powershell
python -m unittest discover -s tests -v
```

Expected output:
```
Ran 17 tests in 2.6s
OK
```

---

## Project Structure

```
├── data/
│   └── lebreton2018_historical_dataset.csv  # 3,532 genuine oceanographic survey records
├── docs/
│   ├── REPORT.md                            # Comprehensive 16-page academic report
│   └── REPORT.docx                          # Formatted Word document submission
├── instance/
│   └── contact.db                           # Local SQLite database for contact inquiries
├── legacy/                                  # Preserved original prototypes & scripts
│   ├── firebase.py
│   ├── plastic_prediction.py
│   ├── prediction.py
│   ├── service.py
│   ├── service_localtest.py
│   ├── testing.py
│   └── README.md
├── static/                                  # Production CSS, JS, images, vendor libraries
│   ├── css/research-theme.css
│   ├── img/
│   ├── vendor/
│   └── index.js
├── templates/                               # Modernized, semantic HTML5 templates
│   ├── home.html
│   ├── hotspot1.html                        # Active object prediction template
│   ├── hotspot.html                         # Active GIS Leaflet dashboard
│   ├── automata.html                        # Active FLA lifecycle simulator
│   ├── visualizations.html
│   ├── mission.html
│   ├── team.html
│   ├── contact.html
│   └── about.html
├── tf_files/
│   ├── retrained_graph.pb                   # Inception-v3 frozen graph (83.41 MB)
│   └── retrained_labels.txt                 # 6 class labels (paper..plastic)
├── tools/
│   ├── fsm_analysis.py                      # Standalone theoretical FLA analysis script
│   └── generate_docx.py                     # Report conversion utility
├── tests/
│   └── test_suite.py                        # 17 automated verification unit tests
├── env.example.py                           # Sanitized credentials template
├── hotspot_service.py                       # GIS Prioritisation and HPI engine
├── main.py                                  # Flask application entry point
├── observation_fsm.py                       # Formal Languages & Automata DFA implementation
├── prediction_service.py                    # Singleton TensorFlow in-memory inference service
├── requirements_modern.txt                  # Python 3.13 dependencies
├── util.py                                  # Image decoding & RFC 2397 Data URL regular language
├── Master_Project_Tableau.twbx              # Original Tableau mapping workbook
└── README.md
```

---

## Model Limitations & Scientific Context

1. **No Accuracy Evaluation:** No benchmark accuracy evaluation was conducted because labeled marine debris test datasets are absent from the repository.
2. **Out-of-Distribution Overconfidence:** Sanity checks on non-debris images (`ocean.jpg`, `Home.jpg`, `asd.jpg`) returned "plastic" classifications with 70.33% to 97.11% confidence, illustrating closed-world softmax overconfidence.
3. **Training Dataset Pedigree:** The six output classes match TrashNet. Training scripts reference `--image_dir=training_dataset`, but the dataset itself is not included in the repository; the model appears to have been trained on a TrashNet-style dataset.
4. **GIS Independence:** Oceanic hotspot prioritisation is completely decoupled from the vision classifier and is driven by the 3,532 genuine oceanographic survey records from Lebreton et al. (2018).

---

## Academic References

1. Lebreton, L., Slat, B., Ferrari, F. et al. *Evidence that the Great Pacific Garbage Patch is rapidly accumulating plastic.* **Sci Rep 8, 4666 (2018)**. https://doi.org/10.1038/s41598-018-22939-w
2. Hopcroft, J. E., Motwani, R., & Ullman, J. D. *Introduction to Automata Theory, Languages, and Computation.* 3rd Edition, Pearson (2006).
3. Szegedy, C., Vanhoucke, V., Ioffe, S., Shlens, J., & Wojna, Z. *Rethinking the Inception Architecture for Computer Vision.* **CVPR (2016)**.
4. Thung, G., & Yang, M. *Classification of Trash for Recyclability Status.* Stanford CS229 Project Report (2016).

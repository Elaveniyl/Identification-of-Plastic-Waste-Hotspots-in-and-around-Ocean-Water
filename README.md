# AI-GIS Detection and Prioritisation of Plastic Waste Hotspots in and around Ocean Water

An integrated computational framework coupling **Deep Learning Computer Vision**, **Geographic Information Systems (Spatial Geostatistics)**, and **Formal Languages & Automata Theory** to identify marine debris materials, mathematically prioritize oceanic plastic accumulation zones, and formally verify oceanographic survey data lifecycles.

---

## 1. Project Overview & Vision

Marine plastic debris represents one of the most critical anthropogenic threats to global ocean ecosystems. Millions of metric tons of synthetic polymers enter the marine environment annually, resisting biological degradation and fragmenting under solar ultraviolet radiation into persistent microplastics. Oceanographic circulation patterns driven by wind stress and the Coriolis force concentrate this debris into massive subtropical convergence zones known as oceanic gyres—most prominently the **Great Pacific Garbage Patch (GPGP)**.

This project delivers a multi-disciplinary computational system designed to address three fundamental challenges in marine environmental monitoring:
1. **Material Identification:** Classifying marine debris images by material type using deep convolutional neural networks.
2. **Spatial Prioritization:** Quantifying and ranking oceanic waste accumulation zones using a mathematical Hotspot Priority Index (HPI) calibrated against genuine oceanographic expedition records.
3. **Data Verification:** Guaranteeing the formal integrity of oceanographic field records through a Deterministic Finite Automaton (DFA) that mathematically verifies every observation's lifecycle transitions.

---

## 2. Problem Statement & Environmental Motivation

The world ocean produces over 50% of the planet's atmospheric oxygen, absorbs roughly 30% of anthropogenic carbon dioxide emissions, and supports essential marine biodiversity. However:
- An estimated **8 to 14 million metric tons** of plastic enter waterways each year.
- Plastics in ocean water do not biodegrade; mechanical abrasion and photodegradation break macro-plastics into durable micro- and nanoplastics that adsorb toxic chemical pollutants and penetrate marine food webs.
- Oceanic cleanup vessels and mitigation programs operate under severe logistical and fuel constraints. Allocating maritime cleanup assets randomly or through unweighted spatial models leads to inefficient retrieval operations.

By fusing algorithmic image classification with geostatistical prioritization and formal automata verification, this framework provides a scientifically rigorous foundation for targeted marine waste mitigation and verifiable environmental data management.

---

## 3. Core Technical Pillars & Architecture

The framework is structured around three core scientific pillars, supported by interactive spatial analytics:

### Pillar 1: Deep Learning Image Classification
- **Neural Network Architecture:** Utilizes the Google Inception-v3 convolutional neural network topology pre-trained on ImageNet and retrained for waste debris classification.
- **Input Tensor Preprocessing:** Accepts visual imagery rescaled and normalized to `(1, 299, 299, 3)` with float32 inputs mapped to the range $[-1.0, 1.0]$.
- **Classification Taxonomy:** Predicts class probabilities across six distinct material categories:
  - `plastic` (synthetic polymers, packaging, maritime fragments)
  - `metal` (beverage cans, metallic debris, hardware)
  - `glass` (bottles, containers, fragments)
  - `cardboard` (packaging, paperboard)
  - `paper` (processed cellulose debris)
  - `trash` (unclassified composite refuse)
- **Role in the System:** Serves as a frontend material classification pipeline to identify debris composition from field photography or autonomous survey cameras.

### Pillar 2: GIS Spatial Hotspot Prioritization Engine
- **Baseline Oceanographic Dataset:** Ingests 3,532 genuine oceanographic survey records compiled by Laurent Lebreton et al. (*Nature Scientific Reports*, 2018), representing standardized manta and mega net tows across the North Pacific Subtropical Gyre.
- **Hotspot Priority Index (HPI):** A deterministic, normalized composite score ($\\text{HPI} \\in [0, 100]$) that quantifies cleanup priority for any geographic coordinate based on three weighted components:
  $$\\text{HPI} = \\left( 0.50 \\cdot M_{\\text{norm}} + 0.35 \\cdot G_{\\text{score}} + 0.15 \\cdot R_{\\text{recency}} \\right) \\times 100$$
  - **Standardized Mass Concentration ($M_{\\text{norm}}$, 50%):** Logarithmic transformation of plastic mass density (g/km²) normalized against the empirical peak value:
    $$M_{\\text{norm}} = \\frac{\\log_{10}(1.0 + M)}{\\log_{10}(1.0 + M_{\\text{ceiling}})}$$
  - **Gyre Convergence Weight ($G_{\\text{score}}$, 35%):** Binary containment score based on spatial location relative to the GPGP $0.1\\,\\text{g/m}^2$ outer boundary (1.0 for observations within the boundary, 0.2 for outer perimeter records).
  - **Temporal Recency ($R_{\\text{recency}}$, 15%):** Normalized temporal recency metric favoring recent survey observations over historical baselines.
- **Prioritization Tiers:**
  - **Critical Priority ($\\text{HPI} \\ge 70$):** High-density accumulation zones inside gyre convergence zones requiring immediate cleanup intervention (467 stations identified).
  - **Moderate Priority ($40 \\le \\text{HPI} < 70$):** Intermediate concentration areas along drift pathways.
  - **Baseline Priority ($\\text{HPI} < 40$):** Low-density background oceanic observations.
- **Spatial Clustering:** Implements grid-based spatial aggregation ($\\Delta \\text{lat} \\times \\Delta \\text{lon}$) summarizing total mass density, average HPI, and station counts per oceanic grid cell.

### Pillar 3: Formal Languages & Automata (FLA) Verification Engine
- **Theoretical Formulation:** Formally models the observation lifecycle as a 5-tuple Deterministic Finite Automaton (DFA):
  $$M = (Q, \\Sigma, \\delta, q_0, F)$$
  - **State Set ($Q$):** 8 formal states:
    $$\\{\\text{DRAFT}, \\text{CAPTURED}, \\text{GEOCODED}, \\text{CLASSIFIED}, \\text{PRIORITIZED}, \\text{VERIFIED}, \\text{ARCHIVED}, \\text{REJECTED}\\}$$
  - **Alphabet ($\\Sigma$):** 7 operational input event symbols:
    $$\\{\\text{add\\_coords}, \\text{classify\\_image}, \\text{calculate\\_priority}, \\text{operator\\_verify}, \\text{complete\\_archive}, \\text{invalidate}, \\text{reset}\\}$$
  - **Initial State ($q_0$):** $\\text{DRAFT}$
  - **Accepting / Final States ($F$):** $\\{\\text{ARCHIVED}, \\text{REJECTED}\\}$
- **Total Transition Function ($\\delta_{\\text{complete}}$):** Completed with an explicit sink/dead state ($\\text{TRAP}$), defining all $9 \\times 7 = 63$ transitions to guarantee complete mathematical specification.
- **Regular Expression & Language Derivation:** Using Generalized NFA (GNFA) state elimination, the accepted language $L(M)$ contains exactly 32 distinct words representing all valid verification lifecycles.
- **Minimality & Equivalence Verification:** Analyzed via Moore's partition refinement algorithm under the Myhill-Nerode theorem, establishing that the 8 states are pairwise distinguishable when accepting outputs differentiate terminal states.

### Pillar 4: Oceanographic Analytics & Longitudinal Visualizations
- Ingests longitudinal survey metrics reflecting decadal accumulation patterns across the North Pacific Gyre.
- Integrates geospatial dashboards exploring plastic mass distribution, numerical piece density, and historical drift trajectories.

---

## 4. System Capabilities & Workflows

The platform integrates research workflows into a unified computational environment:
- **Marine Debris Classifier:** Web interface for classifying debris imagery across 6 material classes.
- **GIS Hotspot Explorer:** Geospatial mapping console enabling filtering of 3,532 survey stations by priority tier, boundary containment, and geographic bounds.
- **FLA Lifecycle Simulator:** Visual state-machine console allowing researchers to step through transitions, evaluate input sequences ($w \\in \\Sigma^*$), and inspect automaton configurations.
- **Spatial & Hotspot Telemetry APIs:** Programmatic services providing ranked observation points, summary statistics, and grid accumulation clusters.
- **Automata Telemetry APIs:** Programmatic services providing the complete DFA 5-tuple specification, single-step state transitions, and whole-word acceptance evaluation.

---

## 5. Model Limitations & Scientific Context

Scientific rigor requires explicit transparency regarding algorithmic capabilities and data constraints:

1. **Absence of Accuracy Benchmarks:** No formal accuracy evaluation was conducted because labeled marine debris ground-truth datasets were not included in the original project files.
2. **Out-of-Distribution Overconfidence:** Sanity checks using non-debris images (`ocean.jpg` seascape, `Home.jpg` banner, `asd.jpg` logo) produced "plastic" classifications with 70.33% to 97.11% softmax confidence. This behavior is typical of closed-world softmax models evaluated on out-of-distribution inputs.
3. **Training Pedigree:** The six output classes precisely match the Stanford TrashNet taxonomy. Historical retraining configurations reference a local directory not bundled in the repository; the model appears to have been trained on a TrashNet-style dataset.
4. **Decoupled Architecture:** Image classification identifies debris material type only. Oceanic hotspot prioritization is computed independently from genuine GIS expedition records and is not altered by single-image inferences.
5. **Static Survey Baseline:** The 3,532 GIS points represent standardized historical expedition tows (Lebreton et al., 2018) rather than real-time satellite or IoT sensor telemetry.

---

## 6. Academic References

1. **Lebreton, L., Slat, B., Ferrari, F., et al.** (2018). *Evidence that the Great Pacific Garbage Patch is rapidly accumulating plastic.* **Nature Scientific Reports**, 8, 4666. https://doi.org/10.1038/s41598-018-22939-w
2. **Hopcroft, J. E., Motwani, R., & Ullman, J. D.** (2006). *Introduction to Automata Theory, Languages, and Computation.* 3rd Edition, Pearson Addison-Wesley.
3. **Szegedy, C., Vanhoucke, V., Ioffe, S., Shlens, J., & Wojna, Z.** (2016). *Rethinking the Inception Architecture for Computer Vision.* In **Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)**, pp. 2818–2826.
4. **Thung, G., & Yang, M.** (2016). *Classification of Trash for Recyclability Status.* Stanford University CS229 Computer Science Technical Report.
5. **Eriksen, M., Lebreton, L., Carson, H. S., et al.** (2014). *Plastic Pollution in the World's Oceans: More than 5 Trillion Plastic Pieces Weighing over 250,000 Tons Afloat at Sea.* **PLoS ONE**, 9(12), e111913. https://doi.org/10.1371/journal.pone.0111913

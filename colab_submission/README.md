# Formal Languages and Automata Theory (21CSC301T)
## Google Colab Submission Package: Waste Observation Lifecycle Automaton

**Course:** Formal Languages and Automata Theory (21CSC301T)  
**Project:** AI-GIS Detection and Prioritisation of Plastic Waste Hotspots in and around Ocean Water  
**Submission Artifact:** Self-Contained Google Colab Demonstration Notebook  

---

## 1. Submission Contents & Manifest

This folder (`colab_submission/`) is an isolated, self-contained academic submission package containing everything needed to review and execute the Formal Languages & Automata (FLA) theoretical component of this project:

| File | Purpose & Description |
| :--- | :--- |
| **`Plastic_Waste_DFA_Demonstration.ipynb`** | **Primary Submission:** Self-contained, executable Jupyter notebook containing the full formal 5-tuple specification, semantic state/alphabet descriptions, partial and total transition tables, state graph visualization, GNFA regular expression derivation (32 accepted words), Moore's partition refinement minimality analysis, and empirical test suites (671 words evaluated with 100% agreement). |
| **`README.md`** | **Documentation:** This guide detailing how to upload, execute, and evaluate the notebook in Google Colab, along with technical prerequisites and theoretical context. |

---

## 2. How to Open and Execute in Google Colab

The notebook is designed to run out-of-the-box in Google Colab with **zero configuration** and **zero local machine dependencies**.

### Step 1: Open Google Colab
1. In any modern web browser, navigate to:  
   **[https://colab.research.google.com](https://colab.research.google.com)**
2. Sign in with your Google account if prompted.

### Step 2: Upload the Notebook
1. In the Colab modal dialog, select the **Upload** tab.
2. Click **Browse** (or drag and drop) and select:  
   `colab_submission/Plastic_Waste_DFA_Demonstration.ipynb`
3. Colab will allocate a cloud runtime and display the interactive notebook.

### Step 3: Run All Cells
1. In the top menu bar, click **Runtime** &rarr; **Run all** (or press keyboard shortcut **`Ctrl + F9`** on Windows / **`Cmd + F9`** on macOS).
2. The notebook executes completely sequentially from top to bottom in approximately **5 to 8 seconds**.
3. All transition tables, high-resolution state diagrams, regular expression outputs, and test suite pass rates will be rendered inline.

---

## 3. Dependencies & Runtime Environment

- **Python Version:** Python 3.9+ (Google Colab default runtime uses Python 3.10+).
- **Libraries Used:**
  - `pandas` (Transition tables and test case formatting)
  - `matplotlib` (State graph diagram rendering)
  - `networkx` (Graph topological layout and edge routing)
  - Standard library modules: `typing`, `itertools`, `random`, `re`, `json`
- **Zero Extra Installs:** All required packages come pre-installed in the standard Google Colab CPU environment. No `!pip install` commands or system-level `apt-get` packages are required.
- **Path Portability:** Contains no hardcoded Windows paths, no external database dependencies, and no machine learning model weights.

---

## 4. Theoretical Summary of the DFA for Course Evaluation

For quick academic reference by the university evaluator:

### 1. Formal 5-Tuple
$$M = (Q, \Sigma, \delta, q_0, F)$$
- **State Set $Q$ ($|Q| = 8$):**
  $$\{\text{DRAFT}, \text{GEO\_TAGGED}, \text{CLASSIFIED}, \text{HOTSPOT\_FLAGGED}, \text{VERIFIED}, \text{DISPATCHED}, \text{ARCHIVED}, \text{REJECTED}\}$$
- **Alphabet $\Sigma$ ($|\Sigma| = 7$):**
  $$\{\text{add\_coords}, \text{classify\_image}, \text{flag\_hotspot}, \text{operator\_verify}, \text{dispatch\_cleanup}, \text{complete\_archive}, \text{invalidate}\}$$
- **Initial State $q_0$:** $\text{DRAFT}$
- **Accepting States $F$ ($|F| = 2$):** $\{\text{ARCHIVED}, \text{REJECTED}\}$
- **Partial Transitions:** 18 domain workflow rules.
- **Total Completion ($\delta_{\text{complete}}$):** 9 states (including $\text{TRAP}$) $\times$ 7 symbols = **63 total transitions**.

### 2. Language Properties (Acyclicity & Finiteness)
- **Topological Rank Property:** Every transition $(u, \sigma, v)$ satisfies $\text{Rank}(u) < \text{Rank}(v)$. The state-transition graph is a **Directed Acyclic Graph (DAG)**.
- **Language Finiteness:** Because there are no directed cycles, the GNFA state elimination produces a regular expression with **zero Kleene stars ($^*$)**.
- **Exact Language Cardinality:** The language accepted by $M$ contains **exactly 32 distinct words** ($|L(M)| = 32$), with a maximum path length of 5 events.

### 3. Minimality via Moore's Partition Refinement (Myhill-Nerode)
- Running Moore's algorithm on the completed total DFA converges in **3 iterations** to **8 equivalence classes**.
- **Terminal State Merging:** $\text{ARCHIVED}$ and $\text{REJECTED}$ have identical right languages ($L(\text{ARCHIVED}) = L(\text{REJECTED}) = \{\epsilon\}$), making them indistinguishable in an unlabelled binary acceptor, while all non-terminal operational states and $\text{TRAP}$ are strictly pairwise distinguishable.

### 4. Empirical Verification
- **Suite 1:** 12 canonical operational test cases covering happy paths, vision-first routes, fast invalidation, premature dispatch, post-terminal transitions, and out-of-alphabet symbols (100% pass).
- **Suite 2:** Exhaustive empirical comparison between the algorithmic DFA simulator and the GNFA-derived compiled regular expression across **671 unique words**, yielding **100.0% agreement (0 mismatches)**.

---

## 5. Scope and Academic Nuance

1. **Self-Contained Isolation:** This submission folder isolates the formal automata component of the broader project. It intentionally omits the 83 MB Inception-v3 frozen graph (`retrained_graph.pb`) and Tableau workbooks, as they belong to machine learning and GIS domains and are unnecessary for automata theory evaluation.
2. **Interactive Testing:** Evaluators can use the provided `evaluate_custom_word()` function in Cell 19 of the notebook to test any arbitrary sequence of event symbols and inspect the real-time execution trace.

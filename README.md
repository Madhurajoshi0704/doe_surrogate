# FormuAI: DOE-Validated Formulation Surrogate Model Stack

FormuAI is a digital R&D workflow system designed for FMCG product development. It automates laboratory data ingestion, runs predictive quality simulations, compares classical statistical Response Surface Methodology (RSM) with modern Machine Learning (Random Forest), and implements a conversational AI agent for formula optimization. 

This project implements the exact **Central Composite Design (CCD)** formulation modeling curriculum.

---

## 🏗️ System Architecture

```
                                  +-----------------------+
                                  |      R&D Chemist      |
                                  +-----------+-----------+
                                              |
                                              v
                                  +-----------+-----------+
                                  |     Streamlit App     |
                                  +-----+-----------+-----+
                                        |           |
                     +------------------+           +------------------+
                     | LIMS SQL DB                                     | Dual Models
                     v                                                 v
             +-------+-------+                                 +-------+-------+
             | SQLite LIMS   |                                 | statsmodels   |
             | Database      |                                 | (OLS-RSM)     |
             | (20 CCD Runs) |                                 | vs. Sklearn   |
             +---------------+                                 | (RandomForest)|
                                                               +---------------+
```

---

## ✨ Core Workflows

1. **Design of Experiments (DOE) Setup**: Automatically generates a 3-factor **Central Composite Design (CCD)** matrix of 20 runs (8 cube, 6 star/axial, 6 center replicates) scaled to actual chemical ranges:
   - **SLES % (Primary Surfactant)**: 8.0% - 15.0% w/w
   - **CAPB % (Co-Surfactant)**: 2.0% - 6.0% w/w
   - **NaCl % (Salt/Thickener)**: 1.0% - 3.0% w/w
2. **Mock LIMS/ELN Storage**: Integrates an SQLite database containing real-world quality measurements (viscosity efflux cup time, pH, initial and 5-min foam heights) with simulated non-linear physics (e.g. over-salting viscosity drops).
3. **Dual Modeling (RSM vs. ML)**:
   - **OLS-RSM**: Fits a quadratic polynomial with linear, interaction, and squared terms using `statsmodels`.
   - **Random Forest**: Fits a decision-tree ensemble using `scikit-learn`.
   - Performs a 5-fold cross-validation comparison showing R², Adjusted R², and RMSE side-by-side.
4. **Visual Analytics**: Interactive 3D Plotly project of the CCD design space, predicted-vs-actual validation charts, and ingredient sensitivity curves.
5. **AI Lab Copilot Agent**: An NLP query processing agent routing researcher instructions (e.g. *"Show experiments with viscosity > 40"*) to custom SQL queries or optimizer models.

---

## 📁 Repository Map

```
formu_ai/
├── src/
│   ├── app.py               # Streamlit application & visualizations
│   ├── database/
│   │   └── lims_db.py       # CCD generation & SQLite LIMS seeder
│   ├── models/
│   │   └── dual_modeling.py # OLS-RSM and Random Forest fitting engine
│   └── agent/
│       └── lab_copilot.py   # NLP lab copilot routing agent
├── tests/
│   └── test_formu_ai.py     # Automated validation tests
├── requirements.txt         # Project package requirements
└── README.md                # System documentation
```

---

## 🚀 Getting Started

### Local Setup & Execution
Run the following commands to install and start the web platform:

```bash
# 1. Navigate to directory
cd /Users/harshitgautam/.gemini/antigravity/scratch/formu_ai

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install packages
pip install -r requirements.txt

# 4. Start dashboard
streamlit run src/app.py
```
Open **`http://localhost:8501`** in your browser.

### Running Test Suite
Execute the pytest suite:
```bash
pytest -v
```

---

## 📝 Key Resume Bullet Points for FMCG R&D Roles

- **Engineered a DOE-Validated Formulation Surrogate Model** using pyDOE2 to generate a 3-factor **Central Composite Design (CCD)** for shampoo recipe optimization, reducing chemical trial-and-error runs.
- **Implemented Dual Modeling Workflows** comparing classical Response Surface Methodology (RSM) quadratic polynomials (via statsmodels) with Random Forest Regressors, demonstrating why RSM outperforms ML on small designs ($N=20$) with cross-validated R² comparison tables.
- **Developed a natural language LIMS database agent** translating chemist instructions (e.g. SQL lookups and target-viscosity optimization searches) into execution pipelines.
- **Designed interactive Streamlit dashboards** projecting 3D factor spaces and multi-variable ingredient sensitivity curves to support data storytelling.

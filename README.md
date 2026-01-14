# TTE2026_sleep: Precision Sleep for Brain Aging

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A precision medicine platform for analyzing sleep-brain aging associations using target trial emulation and causal inference methods.

## 🎯 Overview

This project develops:

1. **Sleep-to-Brain Aging Signatures** from actigraphy and multimodal biomarkers
2. **Target Trial Emulation** for sleep interventions (dCBT-I, OSA treatment, circadian regularity)
3. **Digital Sleep Platform** with patient and clinician interfaces for personalized interventions

## 📁 Project Structure

```
TTE2026_sleep/
│
├── 📊 data/                    # Data files (not tracked in git)
│   ├── raw/                    # Original immutable data
│   ├── external/               # External datasets (OASIS, NSRR, etc.)
│   ├── interim/                # Intermediate processed data
│   └── processed/              # Final analysis-ready data
│
├── 📓 notebooks/               # Jupyter notebooks for exploration
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   └── 03_model_experiments.ipynb
│
├── 🔧 src/                     # Source code - main analysis pipeline
│   ├── __init__.py
│   ├── data/                   # Data loading and processing
│   │   ├── __init__.py
│   │   ├── loader.py           # Data loading functions
│   │   ├── preprocessing.py    # Data preprocessing
│   │   └── quality_control.py  # QC checks
│   │
│   ├── features/               # Feature extraction
│   │   ├── __init__.py
│   │   ├── sleep_features.py   # Sleep architecture, circadian metrics
│   │   └── brain_features.py   # Brain aging biomarkers
│   │
│   ├── models/                 # Statistical and ML models
│   │   ├── __init__.py
│   │   ├── brain_age.py        # Brain age prediction models
│   │   ├── risk_models.py      # Risk stratification
│   │   └── causal.py           # Causal inference (IPTW, etc.)
│   │
│   └── visualization/          # Plotting and figures
│       ├── __init__.py
│       └── plots.py
│
├── 🌐 platform/                # Web applications
│   ├── patient_app.py          # Patient-facing dashboard
│   └── clinician_dashboard.py  # Clinician interface
│
├── 🧪 tests/                   # Unit and integration tests
│   ├── __init__.py
│   ├── test_data.py
│   ├── test_features.py
│   └── test_models.py
│
├── 🤖 models/                  # Trained model files (not tracked)
│   └── .gitkeep
│
├── 📈 outputs/                 # Results and outputs
│   ├── figures/                # Generated plots
│   ├── reports/                # Analysis reports
│   ├── models/                 # Saved model artifacts
│   └── feasibility/            # Feasibility analysis results
│
├── 📚 docs/                    # Documentation
│   ├── data_access_guide.md    # How to access external data
│   ├── data_source_feasibility.md
│   └── methodology.md
│
├── 📜 scripts/                 # Utility scripts
│   ├── download_physionet_sleep.py
│   └── data_source_analysis.py
│
├── 📖 references/              # Papers, manuals, citations
│   └── bibliography.bib
│
├── ⚙️ config/                  # Configuration files
│   └── config.yaml
│
├── 📝 logs/                    # Log files (not tracked)
│   └── .gitkeep
│
├── .env.example                # Environment variable template
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── setup.py                    # Package installation
└── pyproject.toml              # Modern Python packaging
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/TTE2026_sleep.git
cd TTE2026_sleep

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your credentials
```

### 2. Configure Data Access

See [docs/data_access_guide.md](docs/data_access_guide.md) for instructions on:

- Registering for OASIS-3 brain MRI data
- Requesting NSRR MESA sleep data
- Downloading PhysioNet sample data

### 3. Run Analysis Pipeline

```bash
# Step 1: Data processing
python -m src.data.loader

# Step 2: Extract sleep features
python -m src.features.sleep_features

# Step 3: Build brain aging signatures
python -m src.models.brain_age

# Step 4: Run target trial emulation
python -m src.models.causal
```

### 4. Launch Platform

```bash
# Patient dashboard
streamlit run platform/patient_app.py

# Clinician dashboard
streamlit run platform/clinician_dashboard.py
```

## 📊 Data Requirements

| Data Type            | Source    | Access                                       |
| -------------------- | --------- | -------------------------------------------- |
| Brain MRI/PET        | OASIS-3   | [Request Access](https://www.oasis-brains.org/) |
| Sleep PSG/Actigraphy | NSRR MESA | [Request Access](https://sleepdata.org/)        |
| Sample Sleep Data    | PhysioNet | Open Access                                  |

## 🔬 Methodology

### Sleep Feature Extraction

- Cole-Kripke algorithm for sleep/wake detection
- Circadian metrics: IS, IV, relative amplitude, acrophase
- Sleep architecture: TST, efficiency, WASO, fragmentation
- Sleep regularity index (SRI), social jet lag

### Brain Aging Signature

- Brain age prediction using elastic net, random forest, gradient boosting
- Brain age gap = Predicted age - Chronological age
- Sex-stratified models

### Target Trial Emulation

| Intervention         | Target Population | Primary Outcome        |
| -------------------- | ----------------- | ---------------------- |
| dCBT-I               | Insomnia symptoms | Brain age acceleration |
| OSA Treatment        | AHI ≥ 15         | Hippocampal volume     |
| Circadian Regularity | IS < 0.5          | Cognitive trajectory   |

### Causal Inference

- Propensity score estimation (super learner)
- Inverse probability of treatment weighting (IPTW)
- Sensitivity analysis (E-values)
- Bootstrap confidence intervals

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## 📝 Citation

If you use this code, please cite:

```bibtex
@software{sleeptte,
  title = {Precision Sleep for Brain Aging},
  author = {Minh Nguyen},
  year = {2026},
  url = {https://github.com/yourusername/SleepTTE}
}
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Contact

- **Project Lead**: Minh Nguyen
- **Email**: minhnt@ump.edu.vn
- **Issues**: [GitHub Issues](https://github.com/yourusername/TTE2026_sleep/issues)

"""
TTE2026_sleep: Precision Sleep for Brain Aging

A precision medicine platform for analyzing sleep-brain aging associations
using target trial emulation and causal inference methods.
"""

__version__ = "0.1.0"
__author__ = "Minh Nguyen"
__email__ = "minhnt@ump.edu.vn"

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_EXTERNAL = DATA_DIR / "external"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
MODELS_DIR = OUTPUT_DIR / "models"
REPORTS_DIR = OUTPUT_DIR / "reports"

# Config directory
CONFIG_DIR = PROJECT_ROOT / "config"

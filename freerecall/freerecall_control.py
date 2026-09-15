from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from random_nums import random_nums
from display import display_sequence

# ============================================================
# NORMAL SETTINGS FOR CONTROLE EXPERIMENT
# ============================================================

nums = random_nums(count=5, interval=(10, 99))

# settings
display_sequence(
    nums,
    interval=2,
    font_size=512,
    tts=True,
    csv_name="control.csv"
)
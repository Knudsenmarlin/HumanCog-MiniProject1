import random
from pathlib import Path
import sys

"""
THIS ONE IS TO SHOW THE EFFECTS OF CHUNKING
"""


WORDS = [
    "cat", "dog", "sun", "car", "hat", "cup", "bed", "box", "key", "pen",
    "map", "bag", "egg", "leg", "arm", "tree", "book", "door", "fish", "hand",
    "milk", "moon", "rain", "ship", "road", "ring", "bird", "star", "lamp", "shoe",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from serial_recall import display_sequence

if __name__ == "__main__":
    sequence = random.sample(WORDS, 7)
    
    display_sequence(
        sequence,
        interval=2,
        sleep=0,
        tts=True,
        csv_name="serial_recall_chunking.csv",
    )
    print(sequence)

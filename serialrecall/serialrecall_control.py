import random
import string
from typing import List
from pathlib import Path
import sys

"""
CONTROL, JUST REMEMBER THE ITEMS IN ORDER
"""

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from serial_recall import display_sequence


def generate_letters(n: int = 10, uppercase: bool = True):
    """
    Return `n` random Latin letters (A-Z) with no repeats.

    The result is a list of single-character strings, so it can be
    passed straight into display_sequence() as the sequence.
    """

    letters = string.ascii_uppercase if uppercase else string.ascii_lowercase

    if not 0 <= n <= len(letters):
        raise ValueError(f"n must be between 0 and {len(letters)}")

    # random.sample never picks the same element twice
    return random.sample(letters, n)


if __name__ == "__main__":
    sequence = generate_letters(7)
    
    display_sequence(
        sequence,
        interval=2,
        sleep=0,
        tts=True,
        csv_name="serial_recall.csv",
    )
    print(sequence)

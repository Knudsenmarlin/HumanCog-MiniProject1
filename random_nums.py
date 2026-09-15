import random as r
from display import display_sequence


l = []
for _ in range(15):
    num = r.randint(10, 99)
    if num in l:
        pass
    else:
        l.append(num)

if __name__ == "__main__":
    display_sequence(
        l,
        2,
        font_size=512,
        tts=True
    )

# def display_sequence(
#     sequence: Any,
#     interval: Optional[float] = None,
#     bg: str = "black",
#     fg: str = "white",
#     font_size: int = 120,
#     on_finish: Optional[Callable] = None,
#     tts: bool = False,
# ):

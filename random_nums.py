import random as r
from display import display_sequence

def random_nums(times, range: tuple[int, int]):
    l = []
    for _ in range(times):
        num = r.randint(range[0], range[1])
        if num in l:
            pass
        else:
            l.append(num)
    
    print(l)
    return l

if __name__ == "__main__":
    display_sequence(
        random_nums(times=15, range=(10, 99)),
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

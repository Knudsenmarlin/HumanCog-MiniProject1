import random as r
from display import display_sequence

def random_nums(count=15, interval=(10, 99)):
    nums = []

    while len(nums) < count:
        num = r.randint(interval[0], interval[1])

        if num not in nums:
            nums.append(num)

    print(nums)
    return nums

if __name__ == "__main__":
    display_sequence(
        random_nums(count=15, interval=(10, 99)),
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

from typing import Tuple


def tsc_divmod(dividend, divisor) -> Tuple[int, int]:
    result = int(dividend / divisor)
    remainder = dividend % divisor
    return (result, remainder)

def twos_complement(num: int, bits: int) -> int:
    if num & (1 << (bits-1)) != 0:
        # sign bit is set; compute 2s complement
        num -= (1 << bits)
    return num

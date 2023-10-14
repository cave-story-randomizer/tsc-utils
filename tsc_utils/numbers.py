from typing import List, Union

from tsc_utils.util import tsc_divmod, twos_complement


TscValue = bytes
TscInput = Union[TscValue, str]

def tsc_value_to_num(value: TscInput) -> int:
    """
    Converts a TSC value to a number.

    :param value: TSC value as a string of any length.
    :return: The integer encoded by the TSC value.

    Example::
        >>> tsc_value_to_num("1234")
        1234
        >>> tsc_value_to_num("000/")
        -1
        >>> tsc_value_to_num("10/01")
        9901
    """
    if isinstance(value, str):
        value = bytes(value, 'utf-8')

    input_length = len(value) - 1
    num = 0
    for i, digit in enumerate(value):
        digit = twos_complement(digit, 8)
        digit -= ord('0')
        dec_place = input_length - i
        num += digit * 10**dec_place
    return num

def num_to_tsc_value(num: int, output_length: int = 4, min_char: bytes = b' ', max_char: bytes = b'~') -> TscValue:
    """
    Converts a number to a TSC value.
    Generates an "ideal" value for a given number according to the smallest and largest permissible bytes.
    Where possible, generates a value using only a single out of bounds character.

    :param num: The integer to encode.
    :param output_length: How long the resulting value should be. Defaults to 4, used by all vanilla TSC commands.
    :param min_char: The smallest character that can be used to encode the value. Defaults to b' ', for printable characters.
    :param max_char: The largest character that can be used to encode the value. Defaults to b'~', for printable characters.

    :return: A bytestring representing the number.

    :raises ValueError: min_char or max_char provided with length other than 1
    :raises ValueError: min_char is greater than b'0'
    :raises ValueError: max_char is smaller than b'9'
    :raises ValueError: num is too small or too large to encode with the provided arguments

    Example::
        >>> num_to_tsc_value(0)
        b'0000'
        >>> num_to_tsc_value(-1)
        b'000/'
        >>> num_to_tsc_value(100000, output_length=5)
        b':0000'
        >>> num_to_tsc_value(100000, max_char=b'\\xff')
        b'\\x94000'
    """
    if len(min_char) != 1 or len(max_char) != 1:
        raise ValueError(f"Both min_char ({min_char!r}) and max_char ({max_char!r}) must be exactly 1 byte long.")

    if min_char > b'0' and min_char < b'\x80':
        raise ValueError(f"min_char {min_char!r} must be less than or equal to b'0'")
    if max_char < b'9' or max_char > b'\x7f':
        raise ValueError(f"max_char {max_char!r} must be greater than or equal to b'9'")

    min_value = tsc_value_to_num(min_char*output_length)
    max_value = tsc_value_to_num(max_char*output_length)
    if num not in range(min_value, max_value+1):
        raise ValueError(f"{num} is outside the possible values of [{min_value!r}, {max_value!r}] using min_char {min_char!r} and max_char {max_char!r}")

    # within standard bounds
    if num >= 0 and num <= 10**(output_length-1):
        return str(num).zfill(output_length).encode('utf-8', errors="backslashreplace")

    # magnitude is greater than can be represented with a single printable out of bounds character
    min_single = tsc_value_to_num(b' ' + b"0"*(output_length-1))
    max_single = tsc_value_to_num(b'~' + b"9"*(output_length-1))
    if num not in range(min_single, max_single+1):
        return _multi_char_value(num, output_length, min_char, max_char)

    # within range for a value with a single out of bounds character
    return _single_char_value(num, output_length-1)

def _multi_char_value(num: int, output_length: int, min_char: bytes, max_char: bytes) -> TscValue:
    """
    Generates a TSC value from a given number, using more than one out-of-bounds character.
    Character usage limited only by the min_char and max_char arguments.
    Adapted from code by @Brayconn.
    """
    value: List[int] = []
    for i in range(output_length):
        dec_place = 10**((output_length-1)-i)
        char = max(ord(min_char)-ord('0'), min(int(num / dec_place), ord(max_char)-ord('0')))

        num -= dec_place * char

        value.append(char+ord('0'))
    return TscValue(value)

def _single_char_value(num: int, dec_place: int) -> TscValue:
    """
    Recursively generates a TSC value from a given number, using only a single out-of-bounds character.
    Limited to characters within [b' ', b'~'].
    """
    digit, remainder = tsc_divmod(num, 10**dec_place)

    if remainder and digit < 0:
        digit -= 1

    out = TscValue([ord('0') + digit])

    if dec_place == 0:
        return out

    if digit != 0:
        # We've used an OOB character, so the rest is trivial
        return out + str(remainder).zfill(dec_place).encode('utf-8', errors="backslashreplace")

    return out + _single_char_value(num, dec_place-1)

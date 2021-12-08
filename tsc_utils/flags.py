from typing import NamedTuple, Optional, Union
from typing_extensions import get_args
from tsc_utils.numbers import tsc_value_to_num, num_to_tsc_value, TscInput


class Address(NamedTuple):
    offset: int
    bit: int

    @property
    def bits(self) -> int:
        return self.offset * 8 + self.bit

    def __str__(self) -> str:
        return f"{hex(self.offset)}, bit {self.bit}"
    
    def __add__(self, other: Union["Address", int]) -> "Address":
        if isinstance(other, int):
            other = Address(other, 0)
        offset, bit = divmod(self.bit + other.bit, 8)
        offset += self.offset + other.offset
        return Address(offset, bit)
    
    def __sub__(self, other: Union["Address", int]) -> "Address":
        return self + Address(-other.offset, -other.bit)

FREEWARE_FLAGS = Address(0x49DDA0, 0)

def flag_to_address(flag: Union[TscInput, int], base: Address = FREEWARE_FLAGS) -> Address:
    """
    Converts a flag to its corresponding memory address.

    :param flag: The flag to find the address of.
    :param base: The address in memory of the flags array.

    :return: The specific offset and bit referenced by the flag.

    Example::
        >>> flag_to_address(0)
        0x49dda0, bit 0
        >>> flag_to_address(1234)
        0x49de3a, bit 2
        >>> flag_to_address(b'000/')
        0x49dd9f, bit 7
    """
    if isinstance(flag, get_args(TscInput)):
        flag = tsc_value_to_num(flag)

    offset, bit = divmod(flag, 8)
    return Address(offset, bit) + base

def twos_complement(num: int, bits: int) -> int:
    if num & (1 << (bits-1)) != 0:
        # sign bit is set; compute 2s complement
        num -= (1 << bits)
    return num

def address_to_flag(address: Union[Address, int],
                    value: Optional[int] = None,
                    bits: int = 32,
                    base: Address = FREEWARE_FLAGS,
                    min_char=b'\x00',
                    max_char=b'\xff'):
    """
    Converts a memory address to a list of flags, or, optionally, a list of <FL-/<FL+ commands to set a given value.
    Based on code by @thomas-xin for Miza.

    :param address: The memory address to find flags for.
    :param value: The value to set the address to using flag commands.
    :param bits: The number of flags to represent the value at the address.
    :param base: The address in memory of the flags array.
    :param min_char: The smallest legal value to use for the flag values.
    :param max_char: The largest legal value to use for the flag values.

    :return: A list of either raw flag values, or the flag commands to set those flags to the provided value.

    Example::
        >>> address_to_flag(0x49dda0)
        [b'0000', b'0001', b'0002', b'0003', b'0004', b'0005', b'0006', b'0007', b'0008', b'0009', b'0010', b'0011', b'0012', b'0013', b'0014', b'0015', b'0016', b'0017', b'0018', b'0019', b'0020', b'0021', b'0022', b'0023', b'0024', b'0025', b'0026', b'0027', b'0028', b'0029', b'0030', b'0031']
        >>> address_to_flag(0x49dda0, bits=8)
        [b'0000', b'0001', b'0002', b'0003', b'0004', b'0005', b'0006', b'0007']

    Set the player's Booster fuel to 256::
        >>> address_to_flag(0x49e6e8, 256)
        ['<FL-C008', '<FL-C016', '<FL-C024', '<FL-C032', '<FL-C040', '<FL-C048', '<FL-C056', '<FL-C064', '<FL+C072', '<FL-C080', '<FL-C088', '<FL-C096', '<FL-C104', '<FL-C112', '<FL-C120', '<FL-C128', '<FL-C136', '<FL-C144', '<FL-C152', '<FL-C160', '<FL-C168', '<FL-C176', '<FL-C184', '<FL-C192', '<FL-C200', '<FL-C208', '<FL-C216', '<FL-C224', '<FL-C232', '<FL-C240', '<FL-C248', '<FL-C256']
    """

    if value is not None:
        if value >= 1<<(bits):
            raise ValueError(f"{value} too large for a {bits}-bit number.")
        if value < 0:
            value = twos_complement(value, bits)
    
    if isinstance(address, int):
        address = Address(address, 0)

    num = address - base
    flags = []
    for i in range(bits):
        f = num_to_tsc_value((num+i).bits, 4, min_char, max_char)
        if value is None:
            flags.append(f)
        else:
            command = "<FL+" if value&(1<<i) != 0 else "<FL-"
            flags.append(f"{command}{f.decode('utf-8')}")
    return flags

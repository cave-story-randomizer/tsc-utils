from typing import Callable, Optional, Sequence
from tsc_utils.numbers import TscInput, TscValue, num_to_tsc_value, tsc_value_to_num


def default_behavior(value: int) -> str:
    return f"BEHAVIOR {value}"

def codec(event_no: TscInput,
          flags: Sequence[TscValue],
          max_val: Optional[int] = None,
          credit: bool = False,
          behavior: Callable[[int], str] = default_behavior
    ) -> str:
    """
    Generates a TSC script which decodes the value in a given set of flags and calls a different event for each possible value.
    This is mostly useful for rando stuff but is completely applicable to other mods if for some reason <VAR can't be used.

    :param event_no: The first event number to use for the script.
    :param flags: A sequence of flag values representing an integer in memory.
    :param max_val: If provided, limits the codec to at most this many events.
    :param credit: Whether this is a Credits TSC script.
    :param behavior: Specific behavior to include in each event's script.

    :return: A script with one event corresponding to each possible value that can be encoded in the given flags.
    """
    highest_possible = 2**len(flags)
    if max_val is None:
        max_val = highest_possible
    max_val = min(max_val, highest_possible)

    event_label = "l" if credit else "#"
    conditional_jump = "f" if credit else "<FLJ"

    base_event_num = tsc_value_to_num(event_no)
    
    script = ""
    for val in range(max_val):
        eve = num_to_tsc_value(base_event_num+val)
        script += f"{event_label}{eve}\n"

        first_flag_to_check = val.bit_length()
        if first_flag_to_check < len(flags):
            flagjumps = ""
            for i in range(first_flag_to_check, len(flags)):
                num = (val|(1<<i))
                if num >= max_val:
                    continue
                flagjumps += f"{conditional_jump}{flags[i]}:{num_to_tsc_value(base_event_num+num)}"
            if len(flagjumps) > 0:
                script += f'{flagjumps}\n'
        script += f'{behavior(val)}\n'
    return script

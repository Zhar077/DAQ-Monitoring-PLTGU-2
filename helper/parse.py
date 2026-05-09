def parse_current(value):
    """Converts UINT16 to signed float for Charge/Discharge current."""
    # If the value is > 32767, it's a negative value (discharging)
    if value > 32767:
        value -= 65536
    return value / 10.0  # Standard scaling for BMS current


def parse_em619001_signed_32(registers):
    """Converts 2 registers (32-bit) to signed integer.

    Used for EM619001 current and power register when meter is in
    bidirectional mode (metering_mode = 0). Sign indicates direction:
      - positive: forward (PV producing, battery charging)
      - negative: reverse (battery discharging)

    In unidirectional mode (metering_mode = 1), values are always positive.
    """
    if len(registers) < 2:
        return 0
    raw = (registers[0] << 16) | registers[1]
    if raw >= 0x80000000:
        raw -= 0x100000000
    return raw

"""
Low-level bit-packing helpers used by both compressors.

These are plain I/O helpers (no compression logic lives here) -- they just
let the Huffman and LZ77 encoders write/read individual bits instead of
whole bytes, since compressed tokens are rarely byte-aligned.
"""


class BitWriter:
    """Accumulates individual bits (MSB-first) into a bytes buffer."""

    def __init__(self):
        self._bytes = bytearray()
        self._current = 0
        self._nbits = 0

    def write_bit(self, bit):
        self._current = (self._current << 1) | (1 if bit else 0)
        self._nbits += 1
        if self._nbits == 8:
            self._bytes.append(self._current)
            self._current = 0
            self._nbits = 0

    def write_bits(self, bitstring):
        """bitstring: an iterable of '0'/'1' characters or 0/1 ints."""
        for b in bitstring:
            self.write_bit(1 if (b == "1" or b == 1) else 0)

    def write_uint(self, value, nbits):
        """Write `value` as a big-endian unsigned integer using nbits bits."""
        for i in range(nbits - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def getvalue(self):
        """Return (bytes, padding_bits_added_to_last_byte)."""
        padding = 0
        if self._nbits:
            padding = 8 - self._nbits
            self._current <<= padding
            self._bytes.append(self._current)
            self._current = 0
            self._nbits = 0
        return bytes(self._bytes), padding


class BitReader:
    """Reads individual bits (MSB-first) out of a bytes buffer."""

    def __init__(self, data):
        self._data = data
        self._byte_pos = 0
        self._bit_pos = 0  # 0..7, next bit to read within current byte

    def read_bit(self):
        if self._byte_pos >= len(self._data):
            raise EOFError("No more bits to read")
        byte = self._data[self._byte_pos]
        bit = (byte >> (7 - self._bit_pos)) & 1
        self._bit_pos += 1
        if self._bit_pos == 8:
            self._bit_pos = 0
            self._byte_pos += 1
        return bit

    def read_uint(self, nbits):
        value = 0
        for _ in range(nbits):
            value = (value << 1) | self.read_bit()
        return value

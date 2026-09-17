"""
LZ77 / LZSS-style sliding-window compression implemented from scratch.

Encoding scheme
----------------
The input is scanned left to right. At each position we look for the
longest earlier occurrence (within a bounded "window" behind the current
position) of the bytes that come next. If a long-enough match is found we
emit a back-reference (offset, length) token; otherwise we emit the raw
byte as a literal. This is the classic LZSS variant of LZ77 (a match/
literal flag bit precedes each token instead of always encoding a
(offset, length, next-literal) triple).

Token bitstream layout (MSB-first bits, packed via bitio.BitWriter):

    flag bit 0  -> literal:  8 bits  raw byte value
    flag bit 1  -> match:   12 bits  offset-1  (offset is 1..4096, i.e. how
                                                 many bytes back the match
                                                 starts)
                             4 bits  length-3  (length is 3..18 bytes)

File format (.lz), all multi-byte integers big-endian:

    4 bytes  magic     b"LZ71"
    8 bytes  orig_len  number of bytes in the original data
    1 byte   padding   padding bits added to the final byte (0-7)
    remainder the token bitstream
"""

from bitio import BitReader, BitWriter

MAGIC = b"LZ71"

WINDOW_SIZE = 4096      # how far back a match can point (fits in 12 bits)
MIN_MATCH = 3           # shortest match worth encoding as a back-reference
MAX_MATCH = 18          # 15 (4 bits) + MIN_MATCH
MAX_CANDIDATES = 64     # cap search effort per position for pathological input


def _insert(table: dict, data: bytes, i: int) -> None:
    """Record position i under the 3-byte key starting there, pruning
    positions that have fallen outside the sliding window."""
    if i + 3 > len(data):
        return
    key = data[i:i + 3]
    positions = table.setdefault(key, [])
    positions.append(i)
    while positions and i - positions[0] > WINDOW_SIZE:
        positions.pop(0)


def _find_match(data: bytes, i: int, table: dict):
    """Return (offset, length) of the best match at position i, or (0, 0)
    if nothing worth encoding was found."""
    n = len(data)
    if i + MIN_MATCH > n:
        return 0, 0

    key = data[i:i + 3]
    candidates = table.get(key)
    if not candidates:
        return 0, 0

    max_len_possible = min(MAX_MATCH, n - i)
    best_len = 0
    best_offset = 0
    checked = 0

    for p in reversed(candidates):
        if i - p > WINDOW_SIZE:
            break
        checked += 1
        if checked > MAX_CANDIDATES:
            break

        length = 0
        while length < max_len_possible and data[p + length] == data[i + length]:
            length += 1

        if length > best_len:
            best_len = length
            best_offset = i - p
            if best_len == max_len_possible:
                break

    if best_len >= MIN_MATCH:
        return best_offset, best_len
    return 0, 0


def compress(data: bytes) -> bytes:
    """Compress raw bytes into the .lz file format described above."""
    table = {}
    writer = BitWriter()
    n = len(data)
    i = 0

    while i < n:
        offset, length = _find_match(data, i, table)
        if length >= MIN_MATCH:
            writer.write_bit(1)
            writer.write_uint(offset - 1, 12)
            writer.write_uint(length - MIN_MATCH, 4)
            end = i + length
            while i < end:
                _insert(table, data, i)
                i += 1
        else:
            writer.write_bit(0)
            writer.write_uint(data[i], 8)
            _insert(table, data, i)
            i += 1

    bitstream, padding = writer.getvalue()

    out = bytearray()
    out += MAGIC
    out += n.to_bytes(8, "big")
    out.append(padding)
    out += bitstream
    return bytes(out)


def decompress(blob: bytes) -> bytes:
    """Reverse `compress`, reconstructing the exact original bytes."""
    if blob[:4] != MAGIC:
        raise ValueError("Not a valid LZ77 (.lz) file")

    pos = 4
    orig_len = int.from_bytes(blob[pos:pos + 8], "big")
    pos += 8
    _padding = blob[pos]
    pos += 1

    if orig_len == 0:
        return b""

    reader = BitReader(blob[pos:])
    output = bytearray()

    while len(output) < orig_len:
        flag = reader.read_bit()
        if flag == 0:
            output.append(reader.read_uint(8))
        else:
            offset = reader.read_uint(12) + 1
            length = reader.read_uint(4) + MIN_MATCH
            start = len(output) - offset
            for k in range(length):
                output.append(output[start + k])

    return bytes(output)

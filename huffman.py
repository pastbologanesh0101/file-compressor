"""
Huffman coding implemented from scratch.

Format of a .huf file (all multi-byte integers are big-endian):

    4 bytes   magic       b"HUF1"
    8 bytes   orig_len    number of bytes in the original (uncompressed) data
    2 bytes   num_symbols number of distinct byte values in the frequency table
    num_symbols * (1 + 4) bytes
              symbol table: for each entry, 1 byte symbol value followed by
              a 4 byte frequency count
    1 byte    padding     number of padding bits added to the final byte of
                           the bitstream (0-7), kept for completeness even
                           though decoding stops once orig_len bytes have
                           been produced
    remainder the Huffman-coded bitstream

The decoder rebuilds the exact same Huffman tree from the stored
frequency table (tree construction is deterministic) and does not need
the codes themselves to be stored.
"""

import heapq
import itertools

from bitio import BitReader, BitWriter

MAGIC = b"HUF1"


class _Node:
    __slots__ = ("freq", "symbol", "left", "right", "order")

    def __init__(self, freq, symbol=None, left=None, right=None, order=0):
        self.freq = freq
        self.symbol = symbol
        self.left = left
        self.right = right
        self.order = order  # tie-breaker to make heap ordering deterministic

    def is_leaf(self):
        return self.left is None and self.right is None

    def __lt__(self, other):
        if self.freq != other.freq:
            return self.freq < other.freq
        return self.order < other.order


def build_frequency_table(data: bytes) -> dict:
    """Return {byte_value: count} for every distinct byte in data."""
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    return freq


def build_huffman_tree(freq: dict) -> _Node:
    """Build a Huffman tree from a {symbol: frequency} table.

    Deterministic: nodes are pulled from a min-heap ordered by
    (frequency, insertion order), so the same frequency table always
    produces the same tree -- this is what lets the decoder rebuild it
    without the encoder having to serialize the tree shape itself.
    """
    if not freq:
        return None

    counter = itertools.count()
    heap = [_Node(f, symbol=s, order=next(counter)) for s, f in sorted(freq.items())]
    heapq.heapify(heap)

    if len(heap) == 1:
        # Degenerate case: only one distinct symbol in the whole input.
        return heap[0]

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = _Node(left.freq + right.freq, left=left, right=right, order=next(counter))
        heapq.heappush(heap, merged)

    return heap[0]


def generate_codes(root: _Node) -> dict:
    """Walk the tree and return {symbol: code_string_of_0s_and_1s}."""
    codes = {}
    if root is None:
        return codes

    if root.is_leaf():
        # Single-symbol tree: no real branching happened, so assign the
        # symbol a 1-bit code by convention.
        codes[root.symbol] = "0"
        return codes

    stack = [(root, "")]
    while stack:
        node, prefix = stack.pop()
        if node.is_leaf():
            codes[node.symbol] = prefix
        else:
            stack.append((node.left, prefix + "0"))
            stack.append((node.right, prefix + "1"))
    return codes


def compress(data: bytes) -> bytes:
    """Compress raw bytes into the .huf file format described above."""
    freq = build_frequency_table(data)
    tree = build_huffman_tree(freq)
    codes = generate_codes(tree)

    writer = BitWriter()
    for b in data:
        writer.write_bits(codes[b])
    bitstream, padding = writer.getvalue()

    out = bytearray()
    out += MAGIC
    out += len(data).to_bytes(8, "big")
    out += len(freq).to_bytes(2, "big")
    for symbol in sorted(freq):
        out.append(symbol)
        out += freq[symbol].to_bytes(4, "big")
    out.append(padding)
    out += bitstream
    return bytes(out)


def decompress(blob: bytes) -> bytes:
    """Reverse `compress`, reconstructing the exact original bytes."""
    if blob[:4] != MAGIC:
        raise ValueError("Not a valid Huffman (.huf) file")

    pos = 4
    orig_len = int.from_bytes(blob[pos:pos + 8], "big")
    pos += 8
    num_symbols = int.from_bytes(blob[pos:pos + 2], "big")
    pos += 2

    freq = {}
    for _ in range(num_symbols):
        symbol = blob[pos]
        pos += 1
        count = int.from_bytes(blob[pos:pos + 4], "big")
        pos += 4
        freq[symbol] = count

    padding = blob[pos]
    pos += 1

    if orig_len == 0:
        return b""

    tree = build_huffman_tree(freq)

    if tree.is_leaf():
        # Degenerate single-symbol case: no bits were meaningfully coded,
        # just repeat the one known symbol orig_len times.
        return bytes([tree.symbol]) * orig_len

    bitstream = blob[pos:]
    reader = BitReader(bitstream)

    output = bytearray()
    node = tree
    while len(output) < orig_len:
        bit = reader.read_bit()
        node = node.left if bit == 0 else node.right
        if node.is_leaf():
            output.append(node.symbol)
            node = tree

    return bytes(output)

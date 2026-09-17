# File Compression Tool

A small, self-contained Python implementation of two classic lossless
compression algorithms, **Huffman coding** and **LZ77 (LZSS)**, built from
scratch with no help from `zlib`, `gzip`, or `bz2`. The only standard-library
functionality used is for plain I/O and bit-packing (reading/writing files
and turning individual bits into bytes) — the actual compression logic is
hand-rolled.

## How each algorithm works

### Huffman coding (`huffman.py`)

Huffman coding is a **variable-length, frequency-based** compression scheme:
symbols (bytes) that occur more often get shorter bit codes, and rarer
symbols get longer ones.

1. **Frequency table** — count how many times each byte value (0-255)
   appears in the input.
2. **Tree construction** — repeatedly take the two lowest-frequency nodes
   from a min-heap and merge them into a new internal node whose frequency
   is their sum, until only one node (the root) remains. Ties are broken by
   insertion order so the same frequency table always produces the same
   tree deterministically.
3. **Code generation** — walk the tree from the root; each left branch
   appends a `0` and each right branch appends a `1`. The bit string
   collected on the way to each leaf is that byte's code. Because every
   symbol lives at a leaf, no code is ever a prefix of another, so the
   bitstream can be decoded unambiguously with no separators.
4. **Encoding** — replace every input byte with its code and pack the
   resulting bit string into bytes.
5. **Header** — rather than serializing the tree shape itself, the
   compressed file stores the frequency table (symbol + count for each
   distinct byte). Since tree construction is deterministic, the decoder
   rebuilds an identical tree from that table and doesn't need the codes
   to be stored explicitly.

Decoding walks the rebuilt tree bit by bit (left on `0`, right on `1`),
emitting the original byte every time a leaf is reached, until the known
original length has been produced.

### LZ77 / LZSS (`lz77.py`)

LZ77 is a **dictionary-based** scheme: instead of recoding individual bytes,
it looks for runs of bytes that already appeared earlier in the data and
replaces them with a short "go back `offset` bytes and copy `length`
bytes" reference.

1. **Sliding window** — the encoder scans left to right. At each position it
   searches the previous 4096 bytes (the "window") for the longest run of
   bytes that matches what comes next (up to 18 bytes, the longest length
   that fits the token format below). A hash table keyed by 3-byte prefixes
   keeps the search fast instead of comparing against every prior position.
2. **Tokens** — if a match of at least 3 bytes is found, a **match token**
   `(offset, length)` is emitted (offset is 1-4096, encoded in 12 bits;
   length is 3-18, encoded as `length - 3` in 4 bits). Otherwise a
   **literal token** (the raw byte, 8 bits) is emitted. Each token is
   preceded by a single flag bit so the decoder knows which kind it is
   reading.
3. **Overlap** — matches are allowed to reference data that overlaps with
   the match itself (e.g. `"aaaaaaaa"` can be encoded as one literal `"a"`
   followed by a match that copies "18 bytes starting 1 byte back"), which
   is what makes long repeated runs compress extremely well.

Decoding just replays the tokens: literals are appended as-is, and match
tokens copy `length` bytes starting `offset` bytes behind the *current* end
of the output (copying byte-by-byte so overlapping references resolve
correctly).

### Bit packing (`bitio.py`)

Both formats need to pack sub-byte-sized codes (Huffman codes of varying
bit-length, LZ77's 1+8 or 1+12+4-bit tokens) into a byte stream. `BitWriter`
and `BitReader` are small, dependency-free helpers that accumulate/consume
individual bits MSB-first — they contain no compression logic themselves,
just bit-plumbing.

## Usage

```bash
# Compress
python compress.py huffman input.txt output.huf
python compress.py lz77    input.bin  output.lz

# Decompress
python decompress.py huffman output.huf restored.txt
python decompress.py lz77    output.lz  restored.bin
```

`compress.py` prints the original size, compressed size, and compression
ratio. `decompress.py` writes the exact original bytes back out.

## Example compression ratios

Running both algorithms against `sample_data/sample.txt` (900 bytes of a
short sentence repeated 10 times — deliberately repetitive so the effect of
each algorithm is easy to see):

| Algorithm | Original | Compressed | Ratio |
|-----------|---------:|-----------:|------:|
| Huffman   | 900 bytes | 670 bytes | 1.34x |
| LZ77      | 900 bytes | 166 bytes | 5.42x |

Huffman coding only re-encodes *individual byte frequencies*, so it does
comparatively little on this sample because English text has fairly mild
frequency skew over a small alphabet. LZ77 directly exploits the fact that
the whole sentence repeats verbatim, so it compresses far more aggressively
here. In general, Huffman coding tends to do better on data with skewed
byte-frequency distributions but little repetition, while LZ77 does better
on data with long repeated sequences — real-world compressors (like DEFLATE)
combine both ideas for exactly this reason.

## Running the tests

```bash
python -m unittest discover -s tests -v
```

(or `pytest tests/` if you have pytest installed). The test suite covers
byte-exact round-trips for both algorithms on text and binary data, edge
cases (empty input, single repeated byte, all-unique bytes, highly
repetitive data, no-repetition data), internal invariants (prefix-free
codes, frequency table correctness), and a sanity check that compression
ratio is meaningfully better than 1.0 on repetitive input.

A GitHub Actions workflow (`.github/workflows/tests.yml`) runs the same
suite on Python 3.11 and 3.12 on every push and pull request.

## Project layout

```
compress.py       CLI for compressing a file
decompress.py      CLI for decompressing a file
huffman.py         Huffman coding implementation
lz77.py            LZ77 / LZSS implementation
bitio.py           Bit-level I/O helpers shared by both algorithms
sample_data/       Sample input used in the README's ratio example
tests/             Unit tests
.github/workflows/ CI configuration
```

## License

MIT — see [LICENSE](LICENSE).

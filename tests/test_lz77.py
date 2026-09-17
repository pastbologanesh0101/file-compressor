import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lz77


class TestLZ77RoundTrip(unittest.TestCase):
    def test_round_trip_text(self):
        data = b"the quick brown fox jumps over the lazy dog. " * 20
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)

    def test_round_trip_binary(self):
        random.seed(7)
        data = bytes(random.randint(0, 255) for _ in range(2000))
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)

    def test_round_trip_mixed_content(self):
        random.seed(99)
        chunk = bytes(random.randint(0, 255) for _ in range(64))
        data = (chunk * 3) + b"structured repeating text " * 10 + chunk
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)


class TestLZ77EdgeCases(unittest.TestCase):
    def test_empty_input(self):
        data = b""
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)

    def test_highly_repetitive_data(self):
        data = b"x" * 5000
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)
        self.assertLess(len(compressed), len(data))

    def test_no_repetition_data(self):
        # Every 3-byte window is unique, so matches should be rare/absent
        # and the round trip must still be exact.
        data = bytes(range(256)) + bytes(reversed(range(256)))
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)

    def test_single_byte_input(self):
        data = b"q"
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)

    def test_short_input_below_min_match(self):
        data = b"ab"
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)

    def test_overlapping_match_beyond_offset(self):
        # "a" repeated: a match can legally reference bytes that are
        # themselves part of the match being copied (overlap).
        data = b"a" * 20
        compressed = lz77.compress(data)
        restored = lz77.decompress(compressed)
        self.assertEqual(restored, data)


class TestLZ77CompressionRatio(unittest.TestCase):
    def test_repetitive_data_compresses_well(self):
        data = b"abcabcabcabcabcabcabcabcabcabcabcabcabcabcabcabc" * 100
        compressed = lz77.compress(data)
        self.assertLess(len(compressed), len(data))
        ratio = len(data) / len(compressed)
        self.assertGreater(ratio, 2.0)


if __name__ == "__main__":
    unittest.main()

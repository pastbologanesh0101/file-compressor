import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import huffman


class TestHuffmanRoundTrip(unittest.TestCase):
    def test_round_trip_text(self):
        data = b"the quick brown fox jumps over the lazy dog. " * 20
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)

    def test_round_trip_binary(self):
        random.seed(42)
        data = bytes(random.randint(0, 255) for _ in range(2000))
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)

    def test_round_trip_english_paragraph(self):
        data = (
            b"Huffman coding assigns shorter bit sequences to more frequent "
            b"byte values and longer bit sequences to rarer ones, which is "
            b"why text with skewed character frequencies compresses well."
        )
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)


class TestHuffmanEdgeCases(unittest.TestCase):
    def test_empty_input(self):
        data = b""
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)

    def test_single_repeated_byte(self):
        data = b"a" * 500
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)

    def test_single_byte_input(self):
        data = b"z"
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)

    def test_all_unique_bytes(self):
        data = bytes(range(256))
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)

    def test_two_symbols_only(self):
        data = b"ababababababababab"
        compressed = huffman.compress(data)
        restored = huffman.decompress(compressed)
        self.assertEqual(restored, data)


class TestHuffmanInternals(unittest.TestCase):
    def test_frequency_table(self):
        freq = huffman.build_frequency_table(b"aabbbc")
        self.assertEqual(freq, {ord("a"): 2, ord("b"): 3, ord("c"): 1})

    def test_codes_are_prefix_free(self):
        freq = huffman.build_frequency_table(b"aaaabbbccd")
        tree = huffman.build_huffman_tree(freq)
        codes = huffman.generate_codes(tree)
        codes_list = list(codes.values())
        for i, c1 in enumerate(codes_list):
            for j, c2 in enumerate(codes_list):
                if i != j:
                    self.assertFalse(
                        c2.startswith(c1),
                        f"Code {c1!r} is a prefix of {c2!r}, codes are not prefix-free",
                    )

    def test_more_frequent_symbol_gets_shorter_or_equal_code(self):
        freq = huffman.build_frequency_table(b"a" * 100 + b"b" * 10 + b"c" * 1)
        tree = huffman.build_huffman_tree(freq)
        codes = huffman.generate_codes(tree)
        self.assertLessEqual(len(codes[ord("a")]), len(codes[ord("c")]))


class TestHuffmanCompressionRatio(unittest.TestCase):
    def test_repetitive_data_compresses_well(self):
        data = b"abababababababababababababababababababababababab" * 50
        compressed = huffman.compress(data)
        self.assertLess(len(compressed), len(data))
        ratio = len(data) / len(compressed)
        self.assertGreater(ratio, 1.5)


if __name__ == "__main__":
    unittest.main()

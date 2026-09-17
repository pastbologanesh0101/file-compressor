#!/usr/bin/env python3
"""
CLI entry point for compressing a file.

Usage:
    python compress.py huffman input.txt output.huf
    python compress.py lz77    input.bin  output.lz
"""

import sys

import huffman
import lz77

ALGORITHMS = {
    "huffman": huffman,
    "lz77": lz77,
}


def main(argv):
    if len(argv) != 4:
        print("Usage: python compress.py <huffman|lz77> <input file> <output file>")
        return 1

    _, algo_name, input_path, output_path = argv
    algo_name = algo_name.lower()

    if algo_name not in ALGORITHMS:
        print(f"Unknown algorithm '{algo_name}'. Choose 'huffman' or 'lz77'.")
        return 1

    module = ALGORITHMS[algo_name]

    with open(input_path, "rb") as f:
        data = f.read()

    compressed = module.compress(data)

    with open(output_path, "wb") as f:
        f.write(compressed)

    original_size = len(data)
    compressed_size = len(compressed)
    ratio = (original_size / compressed_size) if compressed_size else float("inf")

    print(f"Algorithm:        {algo_name}")
    print(f"Original size:    {original_size} bytes")
    print(f"Compressed size:  {compressed_size} bytes")
    print(f"Compression ratio: {ratio:.2f}x")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

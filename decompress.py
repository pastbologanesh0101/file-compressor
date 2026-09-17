#!/usr/bin/env python3
"""
CLI entry point for decompressing a file produced by compress.py.

Usage:
    python decompress.py huffman output.huf restored.txt
    python decompress.py lz77    output.lz  restored.bin
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
        print("Usage: python decompress.py <huffman|lz77> <compressed file> <output file>")
        return 1

    _, algo_name, input_path, output_path = argv
    algo_name = algo_name.lower()

    if algo_name not in ALGORITHMS:
        print(f"Unknown algorithm '{algo_name}'. Choose 'huffman' or 'lz77'.")
        return 1

    module = ALGORITHMS[algo_name]

    with open(input_path, "rb") as f:
        compressed = f.read()

    data = module.decompress(compressed)

    with open(output_path, "wb") as f:
        f.write(data)

    print(f"Algorithm:       {algo_name}")
    print(f"Compressed size: {len(compressed)} bytes")
    print(f"Restored size:   {len(data)} bytes")
    print(f"Wrote restored file to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

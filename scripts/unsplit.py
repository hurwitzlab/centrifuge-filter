#!/usr/bin/env python3

"""Unsplit FASTA files"""

import argparse
import os
import re
from collections import defaultdict

# --------------------------------------------------
def get_args():
    """command-line args"""
    parser = argparse.ArgumentParser(description='Unsplit FASTA files')
    parser.add_argument('-d', '--dir', help='FASTA directory',
                        type=str, metavar='DIR', required=True)
    parser.add_argument('-o', '--out_dir', help='Output directory',
                        type=str, metavar='DIR', required=True)
    return parser.parse_args()

# --------------------------------------------------
def main():
    """main"""
    args = get_args()
    in_dir = args.dir
    out_dir = args.out_dir

    if not os.path.isdir(in_dir):
        print("Bad --dir '{}'\n".format(in_dir))

    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    files = defaultdict(list)
    for file in os.listdir(in_dir):
        name = os.path.basename(file)
        match = re.search(r'^(.+)\.([0-9]+)(\.[a-zA-Z]+)$', name)
        if not match is None:
            groups = match.groups()
            root = "".join([groups[0], groups[2]])
            num = groups[1]
            files[root].append((num, file))

    for file in files.keys():
        out_fh = open('cat-' + file + '.sh', 'w')
        ordered = [a[1] for a in sorted(files[file], key=lambda a: int(a[0]))]
        for num, split in enumerate(ordered):
            out_fh.write("cat {} {} {}\n".format(
                os.path.join(in_dir, split),
                '>' if num == 0 else '>>',
                os.path.join(out_dir, file)))

# --------------------------------------------------
if __name__ == '__main__':
    main()

#!/usr/bin/env python3

"""Classify and segregate reads using Centrifuge"""

import argparse
import csv
import os
import re
import sys
from Bio import SeqIO

# --------------------------------------------------
def get_args():
    """get args"""
    parser = argparse.ArgumentParser(
        description='Filter FASTA with Centrifuge',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-v',
                        '--verbose',
                        action='store_true',
                        help='Verbose')

    parser.add_argument('-f',
                        '--fasta',
                        type=str,
                        metavar='FILE',
                        required=True,
                        help='FASTA file')

    parser.add_argument('-s',
                        '--summary',
                        type=str,
                        metavar='FILE',
                        required=True,
                        help='Centrifuge summary file')

    parser.add_argument('-e',
                        '--exclude',
                        metavar='IDS_NAMES',
                        default='',
                        help='Comma-separated taxIDs/names to exclude')

    parser.add_argument('-t',
                        '--take',
                        metavar='IDS_NAMES',
                        default='',
                        help='Comma-separated taxIDs/names to take')

    parser.add_argument('-o',
                        '--out_file',
                        type=str,
                        metavar='DIR',
                        default='filtered.fa',
                        help='File to write taken sequences')

    parser.add_argument('-x',
                        '--exclude_file',
                        metavar='FILE',
                        default='',
                        help='File to write excluded sequences')

    return parser.parse_args()

# --------------------------------------------------
def warn(msg):
    """print to stderr"""

    print(msg, file=sys.stderr)

# --------------------------------------------------
def die(msg):
    """warn and quit"""

    warn(msg)
    sys.exit(1)

# --------------------------------------------------
def read_tsv(sum_file):
    """Find the TSV file, read into a lookup table"""

    if not sum_file.endswith('.sum'):
        die('--summary ({}) does not end with ".sum"'.format(sum_file))

    tsv_file = re.sub(r'\.sum$', '.tsv', sum_file)
    if not os.path.exists(tsv_file):
        die('Cannot find expected TSV file ({})'.format(tsv_file))

    name_to_id = dict()
    with open(tsv_file) as tsv_fh:
        reader = csv.DictReader(tsv_fh, delimiter='\t')
        for rec in reader:
            name_to_id[rec['name'].lower()] = rec['taxID']

    return name_to_id

# --------------------------------------------------
def get_taxids(taxa, name_to_id, verbose):
    """Look up taxID (ints) given a list of ints/strings"""

    if len(taxa) == 0:
        return []

    tax_ids = set()
    for tax in re.split(r'\s*,\s*', taxa.lower()):
        tmp_ids = set()

        # If an integer, verify it's one we have in the TSV file
        if str.isdigit(tax):
            if tax in name_to_id.values():
                tmp_ids.add(tax)

        # Check if it's a full species name?
        elif tax in name_to_id:
            tmp_ids.add(name_to_id[tax])

        # Also re.match to all names
        for name in name_to_id.keys():
            if re.match(tax, name):
                tmp_ids.add(name_to_id[name])

        if len(tmp_ids) > 0:
            if verbose:
                warn('"{}" = {}'.format(tax, ', '.join(tmp_ids)))

            for tax_id in tmp_ids:
                tax_ids.add(tax_id)
        else:
            warn('Cannot find tax "{}"'.format(tax))

    return tax_ids

# --------------------------------------------------
def main():
    """main"""
    args = get_args()
    sum_file = args.summary
    fasta_file = args.fasta
    verbose = args.verbose

    if not os.path.isfile(sum_file):
        die('--summary "{}" is not a file'.format(sum_file))

    if not os.path.isfile(fasta_file):
        die('--fasta "{}" is not a file'.format(fasta_file))

    #
    # Figure out which tax IDs we will take/exclude
    #
    tax_name_to_id = read_tsv(sum_file)
    exclude_ids = get_taxids(args.exclude, tax_name_to_id, verbose)
    take_ids = get_taxids(args.take, tax_name_to_id, verbose)

    if len(exclude_ids) == 0 and len(take_ids) == 0:
        die('Must have --take and/or --exclude species')

    if verbose and exclude_ids:
        warn('Will exclude {} tax ID{}'.format(len(exclude_ids),
                                               '' if len(exclude_ids) == 1
                                               else 's'))

    if verbose and take_ids:
        warn('Will take {} tax ID{}'.format(len(take_ids),
                                            '' if len(take_ids) == 1
                                            else 's'))

    #
    # Figure out where to write the results
    #
    take_file = args.out_file
    exclude_file = args.exclude_file

    if len(take_file) == 0 and len(exclude_file) == 0:
        die('Must have --out_file and/or --exclude_file')

    for filename in filter(bool, [take_file, exclude_file]):
        dirname = os.path.dirname(os.path.abspath(filename))
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)

    #
    # Create a lookup from seqID -> taxID
    #
    seq_to_tax = dict()
    with open(sum_file) as sum_fh:
        reader = csv.DictReader(sum_fh, delimiter='\t')
        for rec in reader:
            seq_to_tax[rec['readID']] = rec['taxID']

    #
    # Now filter the input file and segregate the reads
    #
    num_taken = 0
    num_skipped = 0
    take_fh = open(take_file, 'w') if take_file else None
    exclude_fh = open(exclude_file, 'wt') if exclude_file else None
    id_to_name = {v: k for k, v in tax_name_to_id.items()}

    for seq in SeqIO.parse(fasta_file, 'fasta'):
        tax_id = seq_to_tax.get(seq.id, '')

        if not tax_id.isdigit() or int(tax_id) < 1:
            continue
        species_name = id_to_name.get(tax_id, 'NA')

        if tax_id in exclude_ids:
            num_skipped += 1

            if verbose:
                print('{:5d}: SKIP {} = {} ({})'.format(num_skipped,
                                                        seq.id,
                                                        tax_id,
                                                        species_name))

            if exclude_fh:
                SeqIO.write(seq, exclude_fh, 'fasta')

        elif len(take_ids) == 0 or tax_id in take_ids:
            num_taken += 1

            if verbose:
                print('{:5d}: TAKE {} = {} ({})'.format(num_taken,
                                                        seq.id,
                                                        tax_id,
                                                        species_name))

            if take_fh:
                SeqIO.write(seq, take_fh, "fasta")

    #
    # Report
    #
    msg = 'Done, wrote '
    msgs = []

    if exclude_file:
        msgs.append('{:,} to "{}"'.format(num_skipped, exclude_file))

    if take_file:
        msgs.append('{:,} to "{}"'.format(num_taken, take_file))

    print(msg + ', '.join(msgs) + '.')

# --------------------------------------------------
if __name__ == '__main__':
    main()

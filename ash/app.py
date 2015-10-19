#! /usr/bin/env python3
'''
Simple command line poetry generation app wrapping the VerseGenerator
class.
'''
from generator import VerseGenerator
from argparse import ArgumentParser
from time import sleep

parser = ArgumentParser()
parser.add_argument('--corpus', help='Path to directory containing source text')
parser.add_argument('--scheme', help='Rhyme scheme to use for generated lines')
parser.add_argument('--nwords', help='Number of lines to generate')

args = parser.parse_args()

vg = VerseGenerator()

if args.corpus:
    vg.load_corpus(args.corpus)
    for stanza in vg.lines_for_rhyme_scheme(int(args.nwords), args.scheme):
        print(stanza + '\n')
        sleep(1)
else:
    print('Error: no corpus specified')

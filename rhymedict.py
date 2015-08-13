# Rhyming dictionary module
import os
import re
import random
import string
import pykov
from itertools import chain

#CMU_PATH = os.path.dirname(os.path.realpath(__file__))
CMU_SYL_PATH = os.getcwd() + "/cmudict.syl"
CMU_PATH = os.getcwd() + "/cmudict.rep"


def flatten(lst):
    """Collapse a nested list into a flat list"""
    return list(chain.from_iterable(lst))

def identical(lst):
    """Returns True if all items in given list are the same, False otherwise"""
    return lst.count(lst[0]) == len(lst)

def issubsequence(a, b):
    """Returns True if a is a subsequence of b"""
    return b[:len(a)] == a


class Word(object):
    """Represents an English word in the rhyming dictionary"""

    # TODO:
    # Support more levels of stress than just "stressed" or "unstressed"
    # Support different levels of rhyme
    # Method to determine consonance or alliteration with another Word

    def __init__(self, text, syllables):

        self.string = text.lower()
        self.syllables = syllables
        self.phonemes = flatten(self.syllables)

    def is_stressed(self, syllable):
        """Determine whether a given syllable is stressed."""
        return True if ('1' or '2') in ''.join(syllable) else False

    def stress_pattern(self):
        """Return a representation of this word's pattern of stressed and
        unstressed syllables."""
        pattern = []

        for syllable in self.syllables:
            if self.is_stressed(syllable):
                pattern.append("-")
            else:
                pattern.append("_")

        return pattern

    def rhymeswith(self, word):
        """Returns True if given Word instance rhymes with this one."""
        final_phone_sets = []

        for w in [self.phonemes, word.phonemes]:

            last_stress_index = 0
            for i, phone in enumerate(w):
                if phone[-1] in ['1', '2']:
                    last_stress_index = i

            final_phone_sets.append(w[last_stress_index:])

        return identical(final_phone_sets)

    def __repr__(self):
        return "<Word: {}, {} syllables>".format(self.string, len(self.syllables))


class PoetryDict(object):

    # TODO:
    # If speed becomes a problem, the internal word dictionary could be
    # reimplemented as a suffix tree, using the syllables?

    foot_types = {
        "iambic":       ['_', '-'],
        "pyrrhic":      ['_', '_'],
        "trochaic":     ['-', '_'],
        "spondaic":     ['-', '-'],
        "dactylic":     ['-', '_', '_'],
        "anapestic":    ['_', '_', '-'],
        "amphibrachic": ['-', '_', '-']
    }

    def __init__(self, path):
        """Read phoneme and syllable data from the augmented CMU pronouncing
        dictionary. Data is stored as a dictionary where keys are words
        and values are lists of syllables, which are lists of phonemes as
        per CMU format."""

        self.words = {}

        with open(path) as f:
            lines = [line for line in f.readlines() if not line.startswith("#")]

            for line in lines:
                word = line.split()[0].lower()
                rest = line[len(word)+1:]

                # Syllables are separated by -, individual phonemes by a space
                syls = [s.lstrip().rstrip().split() for s in rest.split("-")]

                self.words[word] = Word(word, syls)

    def get_rhyming_words(self, word):
        """Returns a list of all words in dictionary which rhyme 
        with given word."""
        wobj = self.words[word]
        return [w.string for w in self.words.itervalues() if w.rhymeswith(wobj)]

    def meter(self, line):
        """Determine which meter the given line is written in."""
        line_pat = []
        for word in line.split():
            word_pattern = self.words[word.lower()].stress_pattern()
            line_pat.extend(word_pattern)

        # I convert both pattern lists to strings because it's easier to
        # find subsequences this way, using .count
        line_pat = ''.join(line_pat)

        for name, foot_pat in self.foot_types.iteritems():
            foot_pat = ''.join(foot_pat)
            if line_pat.count(foot_pat) * len(foot_pat) == len(line_pat):
                return name
        return False

    def words_for_pattern(self, pattern):
        """Return all words in the dictionary which have a stress pattern
        that fits into the given pattern."""
        result = []
        for word in self.words.itervalues():
            if issubsequence(word.stress_pattern(), pattern):
                result.append(word)
        return result

    def random_line(self, foot, length):
        """Generate a new line using the specified metrical foot."""
        # Without line-based stress analysis this is very unsatisfactory.
        # It's unsatisfactory for other reasons - when you're randomly
        # generating text, you can guide the random selection by restricting
        # it to words with certain properties. If none of these are "semantic"
        # properties then the text is just boring gibberish, even if you
        # selected so it lined up sounds. This is why Markov text works well,
        # the Markov property has the effect of "simulating" grammar. What I'm
        # going to try next is selecting words using a Markov chain, but also
        # filtering the possible choices at each node of the graph by rhyme,
        # alliteration, and stress to hopefully produce "metrical" Markov text.
        line = []
        pattern = self.foot_types[foot] * length
        
        while pattern:
            print "Remaining pattern: {}".format(pattern)
            candidates = self.words_for_pattern(pattern)
            print "Number of candidates: {}".format(len(candidates))
            choice = random.choice(candidates)
            line.append(choice.string)
            pattern = pattern[len(choice.syllables):]

        return ' '.join(line)

    def __getitem__(self, word):
        return self.words[word]
                

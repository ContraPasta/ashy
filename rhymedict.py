# Rhyming dictionary module
import os
import re
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


class PoetryDict(object):

    # Need to think of a good way to record metrical patterns. Start by
    # writing function to recognise them, then generalise as necessary
    metrical_types = {
        "iambic":       "_-",
        "trochaic":     "-_",
        "spondaic":     "--",
        "anapestic":    "__-",
        "dactylic":     "-__",
        "pyrrhic":      "__",
        "amphibrachic": "-_-"
    }

    def __init__(self, path):
        """Read phoneme and syllable data from the augmented CMU pronouncing
        dictionary. Data is stored as a dictionary where keys are words
        and values are lists of syllables, which are lists of phonemes as
        per CMU format."""
        
        self.words = {}
        
        with open(path) as f:
            lines = f.readlines()

            for line in lines:
                if line[0] != "#":
                    word = line.split()[0].lower()
                    rest = line[len(word)+1:]

                    # Syllables are separated by -, individual phonemes by a space
                    syls = [s.lstrip().rstrip().split() for s in rest.split("-")]

                    self.words[word] = syls

    def rhymes(self, *args):
        """Returns True if given words all rhyme, False otherwise."""
        
        final_phone_sets = []
        for word in args:
            phones = flatten(self.words[word.lower()])
            
            last_stressed_index = 0
            for index, phone in enumerate(phones):
                if phone[-1] in ['1', '2']: # Primary or secondary stress
                    last_stressed_index = index
                    
            final_phone_sets.append(phones[last_stressed_index:])

        print final_phone_sets

        if identical(final_phone_sets):
            return True
        else:
            return False

    def get_rhyming_words(self, word):
        """Returns a list of all words in dictionary which rhyme with
        given word."""

        result = []
        for candidate in self.words.iterkeys():
            if self.rhymes(word, candidate):
                result.append(candidate)

        return result

    def alliteration(self, a, b):
        """Alliteration is a special case of consonance where the repeated
        consonant sound is at the stressed syllable. - Wiki"""
        pass
        

    def get_alliterative_words(self, word):
        """Alliteration is a special case of consonance where the repeated
        consonant sound is at the stressed syllable. - Wiki"""

        result = []
        for candidate, syllables in self.words.iteritems():
            if flatten(self.words[word])[0] == flatten(syllables)[0]:
                result.append(candidate)

        return result

    def num_syllables(self, word):

        return len(self.words[word])

    def count_stressed_syllables(self, word):

        syllables = self.words[word]

        count = 0
        for syllable in syllables:
            for phone in syllable:
                if phone[-1] in ['1', '2']:
                    count += 1

        return count

    def examine_string(self, s):
        """Convenience method to help me reverse engineer Pentametron"""

        for word in s.split():
            print word, self.words[word.lower()]

    # Some of the following methods do pretty much the same thing, can
    # clean them up when I know which versions to use in the more complex
    # stuff.

    @staticmethod
    def stressed(syllable):

        stress = False
        for phone in syllable:
            if phone[-1] in ['1', '2']:
                stress = True

        return stress
        
    def stress_pattern(self, s):

        pattern = []
        
        for word in s.split():
            syllables = self.words[word.lower()]

            for syl in syllables:
                if stressed(syl):
                    pattern.append("-")
                else:
                    pattern.append("_")

        return "".join(pattern)

    def find_meter(self, line):
        """Determine what poetic meter a line is written in"""

        stresses = self.stress_pattern(line)

        for meter, pattern in self.metrical_types.iteritems():
            if stresses.count(pattern) * len(pattern) == len(stresses):
                return meter

        return False
        
    def __getitem__(self, word):
        
        return self.words[word]

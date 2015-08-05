# Rhyming dictionary module
import os
import re
from itertools import chain

#CMU_PATH = os.path.dirname(os.path.realpath(__file__))
CMU_SYL_PATH = os.getcwd() + "/cmudict.syl"
CMU_PATH = os.getcwd() + "/cmudict.rep"


def flatten(lst):
    return list(chain.from_iterable(lst))

def identical(lst):
    return len(set(lst)) <= 1


class RhymeDict(object):

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
        for word in [a, b]:
            phones = flatten(self.words[word.lower()])
            
            last_stressed_index = 0
            for index, phone in enumerate(phones):
                if phone[-1] in ['1', '2']: # Primary or secondary stress
                    last_stressed_index = index
                    
            final_phone_sets.append(phones[last_stressed_index:])

        if identical(final_phone_sets):
            return True
        else:
            return False

    def get_rhyming_words(self, word):

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

    def __getitem__(self, word):
        
        return self.words[word]

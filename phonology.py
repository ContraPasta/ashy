import os
import itertools

CMU_PATH = 'cmudict.syl'

def flatten(lst):
    '''Collapse a nested list into a flat list'''
    return list(itertools.chain.from_iterable(lst))

def identical(lst):
    '''Returns True if all items in given list are the same, False otherwise'''
    return lst.count(lst[0]) == len(lst)

def issubsequence(a, b):
    '''Returns True if a is a subsequence of b'''
    return b[:len(a)] == a


def load_cmu_data(path):
    '''Read the phoneme and syllable data from the CMU pronounciation
    dictionary file into a dictionary and return it.'''
    word_table = {}

    with open(path) as f:
        lines = [line for line in f.readlines() if not line.startswith('#')]
        
        for line in lines:
            word = line.split()[0].lower()
            rest = line[len(word)+1:]

            # Syllables are separated by -, individual phonemes by a space
            syls = [s.lstrip().rstrip().split() for s in rest.split('-')]

            word_table[word] = syls

    return word_table


# This is run when the module is loaded, so new Word objects can look up
# phonemic data when they're created from a string.
CMU_DATA = load_cmu_data(CMU_PATH)


class Word(str):
    '''Represents an English word in the rhyming dictionary'''

    # TODO:
    # Support more levels of stress than just 'stressed' or 'unstressed'
    # Support different levels of rhyme
    # Method to determine consonance or alliteration with another Word
    # Possibly, inherit from TextBlob's excellent Word class, with its
    # lemmatization, Wordnet integration methods

    def __init__(self, strng):

        self.string = strng.lower()
        try:
            self.syllables = CMU_DATA[strng.lower()]
            self.phonemes = flatten(self.syllables)
        # Word has no pronounciation information in dictionary used
        except KeyError:
            self.syllables = []
            self.phonemes = []

    def is_stressed(self, syllable):
        '''Determine whether a given syllable is stressed.'''
        return True if ('1' or '2') in ''.join(syllable) else False

    def stress_pattern(self):
        '''Return a representation of this word's pattern of stressed and
        unstressed syllables.'''
        pattern = []

        for syllable in self.syllables:
            if self.is_stressed(syllable):
                pattern.append('-')
            else:
                pattern.append('_')

        return pattern

    def matches_pattern(self, pattern):
        '''Returns True if word fits into the given stress pattern.'''
        return pattern == self.stress_pattern()

    def rhymeswith(self, word, exclusive=True):
        '''Returns True if given Word instance rhymes with this one.
        '''
        if exclusive and self.string == word.string:
            return False
        
        final_phone_sets = []
        for w in [self.phonemes, word.phonemes]:
            last_stress_index = 0

            for i, phone in enumerate(w):
                if phone[-1] in ['1', '2']:
                    last_stress_index = i

            final_phone_sets.append(w[last_stress_index:])

        return identical(final_phone_sets)

    def __repr__(self):
        return u'Word({})'.format(self.string)

    def __str__(self):
        return self.string


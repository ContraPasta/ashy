import os
import itertools
from nltk.corpus import wordnet

CMU_PATH = 'cmudict.syl'

ARPABET = {
    'vowels': [
        # Monophthongs
        'AO', 'AA', 'IY', 'UW', 'EH', 'IH', 'UH', 'AH', 'AX', 'AE',
        # Diphthongs
        'EY', 'AY', 'OW', 'AW', 'OY',
        # R-coloured vowels. Note the CMU is for American English.
        # R-coloured vowels only exist in rhotic dialects such as yank
        # and canuck
        'ER', 'AXR', 'EHR', 'UHR', 'AOR', 'AAR', 'IHR', 'IYR', 'AWR'
    ],
    'consonants': [
        # Stops
        'P', 'B', 'T', 'D', 'K', 'G',
        # Affricates
        'CH', 'JH',
        # Fricatives
        'F', 'V', 'TH', 'DH', 'S', 'Z', 'SH', 'ZH', 'HH',
        # Nasals
        'M', 'EM', 'N', 'NG', 'ENG',
        # Liquids
        'L', 'EL', 'R', 'DX', 'NX',
        # Semivowels
        'Y', 'W', 'Q'
    ]
}

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


class Word:
    '''Represents an English word in the rhyming dictionary'''

    # TODO:
    # Support more levels of stress than just 'stressed' or 'unstressed'
    # Support different levels of rhyme

    def __init__(self, strng, pos_tag=None):

        self.string = strng.lower()
        self.pos_tag = pos_tag
        try:
            self.syllables = CMU_DATA[strng.lower()]
            self.phonemes = flatten(self.syllables)
            # Need a hashable version of the CMU data for each word
            self.syl_string = ''.join(self.phonemes)
        # Word has no pronounciation information in dictionary used
        except KeyError:
            self.syllables = []
            self.phonemes = []
            self.syl_string = None

        self.collection_has_rhyme = False

    def __key(self):
        return (self.string, self.pos_tag, self.syl_string)

    def __eq__(self, other):
        return type(self) == type(other) and self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    def _is_comparable(self, word):
        '''A 'sanity check' for phonemic comparison methods. Checks
        whether it makes sense to compare this word and the given word.
        '''
        if self == word:
            return False
        if not self.phonemes or not word.phonemes:
            return False

        return True

    def has_data(self):
        return True if self.phonemes else False

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

        return ''.join(pattern)

    def matches_pattern(self, pattern):
        '''Returns True if word fits into the given stress pattern.'''
        return pattern == self.stress_pattern()

    def final_phone_set(self):
        '''
        Return all phonemes after the last stressed vowel.
        '''
        last_stress_index = 0
        for i, phone in enumerate(self.phonemes):
            if phone[-1] in ['1', '2']:
                last_stress_index = i

        return self.phonemes[last_stress_index:]

    def rhymeswith(self, word):
        '''Returns True if given Word instance rhymes with this one.
        '''
        if not self._is_comparable(word):
            return False

        return self.final_phone_set() == word.final_phone_set()

    def set_rhyme_in_collection(self, val):
        self.collection_has_rhyme = val

    def has_rhyme_in_collection(self):
        return self.collection_has_rhyme

    def alliterateswith(self, word, exclusive=True):
        '''Returns True if given word starts with the same sound as
        this one. (Special case of consonance)'''
        if not self._is_comparable(word):
            return False
        if self.phonemes[0] not in ARPABET['consonants']:
            return False
        if self.phonemes[0] == word.phonemes[0]:
            return True

        return False

    def assonancewith(self, word, exclusive=True):
        '''
        Returns True if both words start with the same vowel sound.
        '''
        if not self._is_comparable(word):
            return False
        if self.phonemes[0] not in ARPABET['vowels']:
            return False
        if self.phonemes[0] == word.phonemes[0]:
            return True

        return False

    def synsets(self):
        return wordnet.synsets(self.string)

    def __repr__(self):
        return u'Word({})'.format(self.string)

    def __str__(self):
        return self.string

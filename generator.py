from __future__ import division
import random
import phonology
from collections import Counter
from string import punctuation as punc

class VerseGenerator(object):

    def __init__(self, source_text):
        '''Build a markov chain from the given source text.'''
        self.chain = {}
        self.words = []
        
        # This should probably be replaced with a real tokeniser.
        # FIXME: Stripping should be done to each word
        sents = [s.lower().strip(punc) for s in source_text.split('.')]

        for sent in sents:
            previous = None
            for strng in sent.split():
                current = phonology.Word(strng)
                if current not in self.chain:
                    self.chain[current] = []
                if previous:
                    self.chain[previous].append(current)
                previous = current

        for word, succ in self.chain.iteritems():
            self.chain[word] = Counter(succ).most_common()

        self.all_words = [w for w in self.chain.iterkeys()]
            
    def _select(self, pairs):
        '''Roulette wheel selection from markov chain'''
        r = random.random()
        current_sum = 0
        for word, count in pairs:
            prob = count / len(pairs)
            current_sum += prob
            if r <= current_sum:
                return word
        return None

    def random_line(self, length, stress_pattern=None):
        '''Generate a random line from markov chain'''
        line = [random.choice(self.all_words)]
        while len(line) < length:
            candidates = self.chain[line[-1]]
            if candidates:
                w = self._select(candidates)
            # A word was selected with no following words
            else:
                w = random.choice(self.all_words)
            line.append(w)
        return ' '.join(line)

    def random_block(self, nwords, nlines):
        '''Generate a set of random lines.'''
        block = []
        while len(block) < nlines:
            block.append(self.random_line(nwords))
        return block
        

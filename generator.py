from __future__ import division
import random
import phonology
from collections import Counter, namedtuple
from string import punctuation


def chunks(lst, n):
    '''Split a list into chunks of length n'''
    n = max(1, n)
    return [lst[i:i + n] for i in xrange(0, len(lst), n)]

def tokenise(text):
    '''Split given text into a list of words for each sentence'''
    # This should probably be replaced with a real tokeniser.
    sents = []
    for sent in [s.split() for s in text.split('.')]:
        sents.append([w.lower().strip(punctuation) for w in sent])
    return sents


class VerseGenerator(object):

    def __init__(self, source_text):
        '''Build a markov chain from the given source text.'''
        self.chain = {}
        self.words = []

        sents = tokenise(source_text)
        for sent in sents:
            previous = None
            for strng in sent:
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

    def _random_word(self):
        '''Return any random word from the markov chain'''
        return random.choice(self.all_words)
    
    def random_line(self, length, stress_pattern=None):
        '''Generate a random line from markov chain'''
        line = [random.choice(self.all_words)]
        while len(line) < length:
            candidates = self.chain[line[-1]]
            if candidates:
                w = self._select(candidates)
            # TODO: Random any word should only return words with
            # followers, which would avoid this check and make things
            # neater
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

    def random_rhyming_verse(self, nwords, nlines):
        '''Generate a random verse in rhyming couplets'''
        # TODO:
        # - Encapsulate the index and selection parts so they're
        # easy to reuse for different checks
        # - Change random any word func
        # - What happens when there are no rhyming words?
        
        total_words = nwords * nlines
        words = [self._random_word()]
        
        for i in xrange(2, total_words + 1):
            cands = self.chain[words[-1]]
            if cands:
                # If we've reached the end of a line and there's a
                # previous line in the pattern to rhyme it with
                if i % nwords == 0 and i != nwords:
                    prev_last_w = words[i - nwords]
                    cands = [p for p in cands if p[0].rhymeswith(prev_last_w)]
                w = self._select(cands)
            else:
                w = self._random_word()
            words.append(w)

        print words
        lines = [' '.join(line) for line in chunks(words, nwords)]
        return '\n'.join(lines)

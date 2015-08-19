import os
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

def test_loader():
    for root, _, fpaths in os.walk(os.getcwd() + '/corpus/'):
        texts = []
        for path in fpaths:
            fullpath = os.path.join(root, path)
            print(fullpath)
            with open(fullpath) as f:
                texts.append(f.read())
    return texts

class VerseGenerator(object):

    def __init__(self, source_text=None):
        '''Build a markov chain from the given source text.'''
        self.chain = {}
        if source_text:
            self.import_text(source_text)

    def import_text(self, source_text):
        '''Add the given block of text to the markov chain'''
        sentences = tokenise(source_text)
        for sentence in sentences:
            previous = None
            for strng in sentence:
                current = phonology.Word(strng)
                if current not in self.chain:
                    self.chain[current] = {}
                if previous:
                    if current not in self.chain[previous]:
                        self.chain[previous][current] = 1
                    else:
                        self.chain[previous][current] += 1
                previous = current

    def import_corpus(self, folder):
        '''Load text files in given folder and any subfolders into the
        markov chain.'''
        for root, _, fpaths in os.walk(folder):
            for path in fpaths:
                fullpath = os.path.join(root, path)
                with codecs.open(fullpath, 'r', 'utf-8-sig') as f:
                    text = f.read()
                    self.import_text(text)

    def _select(self, counter):
        '''Roulette wheel selection from markov chain'''
        r = random.random()
        current_sum = 0
        for word, count in counter.items():
            prob = count / len(counter)
            current_sum += prob
            if r <= current_sum:
                return word
        return None

    def _random_word(self):
        '''Return any random word from the markov chain, if it has
        words following it.'''
        return random.choice([w for w in self.chain.keys()])

    def random_line(self, length, stress_pattern=None):
        '''Generate a random line from markov chain'''
        line = [self._random_word()]
        while len(line) < length:
            candidates = self.chain[line[-1]]
            if candidates:
                w = self._select(candidates)
            # A word was selected with no following words
            else:
                w = self._random_word()
            line.append(w)
        return line

    def random_block(self, nwords, nlines):
        '''Generate a set of random lines.'''
        block = []
        while len(block) < nlines:
            block.append(self.random_line(nwords))
        return block

    def rhyming_couplet(self, nwords):
        '''Generate a random rhyming couplet'''
        line1 = self.random_line(nwords)
        while True:
            line2 = self.random_line(nwords)
            #print(line1, line2)
            if line1[-1].rhymeswith(line2[-1]):
                break
        return '\n'.join([' '.join(l) for l in [line1, line2]])
        
        

        

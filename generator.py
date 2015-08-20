import os
import regex
import random
import phonology
from collections import Counter, namedtuple
from string import punctuation

def strip_punctuation(s):
    '''Strip all punctuation characters, including unicode punctuation,
    from given string.'''
    return regex.sub('\p{P}+', '', s)

def chunks(lst, n):
    '''Split a list into chunks of length n'''
    n = max(1, n)
    return [lst[i:i + n] for i in xrange(0, len(lst), n)]

def tokenise(text):
    '''Split given text into a list of words for each sentence'''
    # This should probably be replaced with a real tokeniser.
    sents = []
    for sent in [s.split() for s in text.split('.')]:
        sents.append([strip_punctuation(w.lower()) for w in sent])
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
            self.load_text(source_text)

    def load_text(self, source_text):
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

    def load_corpus(self, folder):
        '''Load text files in given folder and any subfolders into the
        markov chain.'''
        for root, _, fpaths in os.walk(folder):
            for path in fpaths:
                fullpath = os.path.join(root, path)
                with codecs.open(fullpath, 'r', 'utf-8-sig') as f:
                    text = f.read()
                    self.load_text(text)

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

    def _filter_select(self, counter, method, arg=None):
        '''Like roulette wheel selection, but filters the candidate
        words in `counter` according to the criteria given in 
        `restrictions` before selection.'''
        filtered = {w: c for w, c in counter.items() if method(w, arg)}
        return self._select(filtered)

    def _filter_counter(self, counter, method, *args):
        '''As above but return filtered counter instead of doing the
        selection.'''
        return {w: c for w, c in counter.items() if method(w, *args)}

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
        # What if the last word of the first line has no CMU data?
        line1 = self.random_line(nwords)
        last1 = line1[-1]
        while True:
            line2 = self.random_line(nwords)
            last2 = line2[-1]
            if last1.rhymeswith(last2) and last1 != last2:
                break
        return '\n'.join([' '.join(l) for l in [line1, line2]])

    def construct_line(self, length, constraints=None):
        '''Search the markov chain graph in depth-first order for a
        for a sequence of words rooted at a randomly selected word, as
        close to the given length as possible.
        '''
        stack = [(self._random_word(), None, 0)]
        current = None

        while stack and level < length:
            current = stack.pop()
            level = current[3]
            for node in self.chain[current[0]]:
                stack.append((level + 1, node, current))

        line = []
        for i in range(level):
            line.append(current[0])
            current = current[1]

        return line


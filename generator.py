import os
import regex
import random
from string import punctuation
from collections import Counter, namedtuple
from phonology import Word

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


class VerseGenerator(object):

    Constraint = namedtuple('Constraint', ['index', 'method', 'args'])

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
                current = Word(strng)
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

    def construct_line(self, length, constraints=[]):
        '''Search the markov chain graph in depth-first order for a
        for a random sequence of words rooted at a randomly selected
        word, as close to the given length as possible.
        '''
        level = 0
        stack = [(self._random_word(), None, 0)]
        current = None

        while stack and level < length:
            print(len(stack))
            current = stack.pop()
            level = current[2]
            adj = self.chain[current[0]]

            # Apply constraints, if any. Constraints supplied as tuples:
            # (index, method, args)
            for con in constraints:
                if con[0] == level:
                    adj = self._filter_counter(adj, con[1], con[2])
            
            succ = [word for word in adj]
            random.shuffle(succ)
            for word in succ:
                stack.append((word, current, level + 1))

        # Walk backwards from final node to build list
        line = []
        for i in range(level):
            line.append(current[0])
            current = current[1]
        line.reverse()
        
        return line

    def rhyming_couplet(self, nwords, nlines):
        '''Generate a random rhyming couplet.
        '''
        lines = []

        while len(lines) < nlines:
            print('Couplet loop iter')
            line_a = self.construct_line(nwords)
            print('line_a: ', line_a)
            constraint = (nwords - 1, Word.rhymeswith, line_a[-1])
            line_b = self.construct_line(nwords, [constraint])
            lines.extend([line_a, line_b])

        return lines

def testsetup():
    vg = VerseGenerator()
    vg.load_corpus(os.getcwd() + '/corpus/')
    return vg
        
        

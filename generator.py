import os
import regex
import codecs
import random
import networkx
from queue import Queue
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

# This is for storing the constraints that a word must obey to appear
# at a certain position in the line. `index` should be a position in
# the line or None, `method` should be a method of the Word class, and
# `args` the arguments, if any, to that method.
Filter = namedtuple('Filter', ['index', 'method', 'args'])


class XVerseGenerator(object):

    def __init__(self, text=None):
        self.chain = networkx.DiGraph()
        if text:
            self.load_text(text)

    def __getitem__(self, item):
        return vg.chain[item]

    def load_text(self, text):
        '''Add the given text to the Markov chain
        '''
        for sentence in tokenise(text):
            previous = None
            for w in sentence:
                current = Word(w)
                if previous:
                    if (previous, current) not in self.chain:
                        self.chain.add_edge(previous, current, count=1)
                    else:
                        self.chain[previous][current]['count'] += 1
                previous = current

    def load_corpus(self, folder):
        '''Load text files in given folder and any subfolders into the
        markov chain.
        '''
        for root, _, fpaths in os.walk(folder):
            for path in fpaths:
                fullpath = os.path.join(root, path)
                with codecs.open(fullpath, 'r', 'utf-8-sig') as f:
                    text = f.read()
                    self.load_text(text)

    def roulette_select(self, node, pred=False):
        '''Pick a node adjacent to given node using roulette wheel
        selection and return it.
        node -> node
        '''
        r = random.random()
        current_sum = 0
        if pred: 
            adjacent = self.chain.pred[node]
        else:
            adjacent = self.chain.succ[node]

        for node, props in adjacent.items():
            count = props['count']
            prob = count / len(adjacent)
            current_sum += prob
            if r <= current_sum:
                return node

        return None

    def filter_nodes(self, filters=[]):
        '''Return list of all graph nodes, filtered by filters'''
        if not filters:
            return self.chain.nodes()
        out = []
        for node in self.chain.nodes():
            for f in filters:
                if f.method(node, *f.args):
                    out.append(node)
        return out

    def filter_adjacent(self, node, filters=[], pred=False):
        '''Filter successor or predecessor nodes nodes for the given
        node, according to the supplied filters, and return them. 
        Filters are to be supplied as (method, args) tuples.
        node -> [node]
        '''
        # TODO: Weight proportional ordering
        try:
            adj = self.chain.pred[node] if pred else self.chain.succ[node]
        except KeyError:
            raise Exception('Tried to operate on empty chain')

        if not filters:
            return [word for word in adj]

        out = []
        for word in adj:
            for f in filters:
                if f.method(word, *f.args):
                    out.append(word)

        return out

    def construct_line(self, length, constraints=[], pred=False):
        '''Search the markov chain graph in depth-first order for a
        for a random sequence of words rooted at a randomly selected
        word, as close to the given length as possible.
        '''
        level = 0
        first = (random.choice(self.chain.nodes()), None, level)
        stack = [first]
        current = None

        while stack and level < length:
            current = stack.pop()
            level = current[2]
            curr_word = current[0]
            filters = [f for f in constraints if f.index == level]
            next_words = self.filter_adjacent(curr_word, filters, pred=pred)
            random.shuffle(next_words)
            stack.extend([(w, current, level + 1) for w in next_words])

        line = []
        for i in range(level):
            print(current)
            line.append(current[0])
            current = current[1]
        if not pred:
            line.reverse()

        return line

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
        '''Roulette wheel selection from a dict of {item: count}
        '''
        r = random.random()
        current_sum = 0
        for word, count in counter.items():
            prob = count / len(counter)
            current_sum += prob
            if r <= current_sum:
                return word
        return None

    def _roulette_sort(self, counter):
        '''Return a list of words in counter, ordered by roulette wheel
        selection.
        '''
        output = []
        counter_copy = counter.copy()

        while counter_copy:
            selected = self._select(counter_copy)
            output.append(selected)
            del counter_copy[selected]

        return output

    def _filter_select(self, counter, method, arg=None):
        '''Like roulette wheel selection, but filters the candidate
        words in `counter` according to the criteria given in 
        `restrictions` before selection.
        '''
        filtered = {w: c for w, c in counter.items() if method(w, arg)}
        return self._select(filtered)

    def _filter_counter(self, counter, method, *args):
        '''As above but return filtered counter instead of doing the
        selection.
        '''
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

    def construct_line(self, length, constraints=[], sort='random'):
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

            if sort == 'roulette':
                succ = self._roulette_sort(adj)
            else:
                # Default to random search ordering
                succ = [w for w in adj]
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
        '''Generate a verse consisting of random rhyming couplets.
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
        
        

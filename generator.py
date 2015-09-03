import os
import regex # Better unicode support than stdlib re
import codecs
import random
import networkx
from queue import Queue
from string import punctuation
from collections import Counter, namedtuple
from functools import partial
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

def nltokenise(text):
    '''Split the text into words and sentences using NLTK's tokenisers.'''
    pass

def reverse(lst):
    '''
    Return reversed version of sequence, because they made `reversed
    an iterator in Python 3 :/
    '''
    return [x for x in reversed(lst)]


# This is for storing the constraints that a word must obey to appear
# at a certain position in the line. `index` should be a position in
# the line or None, `method` should be a method of the Word class, and
# `args` the arguments, if any, to that method.
Filter = namedtuple('Filter', ['index', 'method', 'args'])


class VerseGenerator(object):

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

    def build_match_list(self, words, comparison_methods):

        match_table = {}
        iters = 0
        for method in comparison_methods:
            match_table[method] = []
            word_list = list(words)
            while word_list:
                iters += 1
                current = word_list.pop()
                pruned = []
                for word in word_list:
                    if method(current, word):
                        match_table[method].append(word)
                    else:
                        pruned.append(word)
                word_list = pruned
        print(iters)
        return match_table

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
    
    def filter_words(self, words, predicates=[]):
        '''Filter given list by multiple predicates.
        '''
        if not predicates:
            return words

        out = []
        for word in words:
            for predicate in predicates:
                if predicate(word):
                    out.append(word)

        return out

    def build_word_seq(self, length, predicates=[], first=None, max_iters=6000):
        '''
        Traverse the graph in depth first order to build a sequence
        of the given length which fits the supplied predicates. If a
        matching sequence is not found, return partially constructed
        sequence. Begins with a randomly selected word from the graph
        
        predicates - list of (index, partial(Word.method, arg)) tuples
        '''
        level = 0
        iters = 0
        
        if not first:
            preds = [p[1] for p in predicates if p[0] == 0]
            try:
                first = random.choice(self.filter_words(self.chain.nodes(), preds))
            except IndexError:
                raise Exception('No word in chain matches given predicate')
                
        stack = [{'word': first, 'parent': None, 'level': level}]
        
        while stack and level < length:

            iters += 1
            if iters > max_iters:
                break

            current_entry = stack.pop()
            level = current_entry['level'] + 1
            word = current_entry['word']
            preds = [p[1] for p in predicates if p[0] == level]
            successors = self.filter_words(self.chain.successors(word), preds)
            random.shuffle(successors)

            for succ in successors:
                entry = {'word': succ, 'parent': current_entry, 'level': level}
                stack.append(entry)
                
        #print('iterations: {}\npath: {}'.format(iters, current_entry))
        
        line = []
        for i in range(level):
            line.append(current_entry['word'])
            current_entry = current_entry['parent']

        return reverse(line)

    def build_poem_line(self, length, predicates=[]):
        '''
        Wrapper around `build_word_seq`. Calls `build_word_seq` as many
        times as necessary to fill the line with the correct number of
        words. This fixes the problem of short lines because the DFS
        couldn't find a path of the right length.
        '''
        line = []
        slots = length

        while slots > 0:
            line.extend(self.build_word_seq(slots, predicates))
            slots = length - len(line)
            # Adjust predicate indices to compensate
            predicates = [(i - slots, pred) for i, pred in predicates]
            print(predicates)

        return line

    def t_construct_line(self, nwords, rhyme_word=None):
        '''As `build_word_seq`, but assume the only filter is going to be for rhyme
        at the end of the line and so build it backwards.
        TODO: Fold this functionality into `build_word_seq`
        '''
        level = 0

        if rhyme_word:
            rhymes = [w for w in self.chain.nodes() if w.rhymeswith(rhyme_word)]
        else:
            rhymes = self.chain.nodes()

        stack = [{'word': random.choice(rhymes), 'prev': None, 'level': level}]

        while stack and level < nwords - 1:
            this_entry = stack.pop()
            level = this_entry['level']
            current = this_entry['word']
            preds = self.chain.predecessors(current)
            random.shuffle(preds)

            for word in preds:
                entry = {'word': word, 'prev': this_entry, 'level': level + 1}
                stack.append(entry)

        line = []

        for i in range(nwords):
            line.append(this_entry['word'])
            this_entry = this_entry['prev']

        return line

    def rhyming_couplets(self, nwords, nlines):
        '''Generate a verse of random rhyming couplets'''
        lines = []

        while len(lines) < nlines:
            line_a = self.construct_line(nwords)
            constraint = Filter(nwords - 1, Word.rhymeswith, [line_a[-1]])
            line_b = self.construct_line(nwords, [constraint])
            lines.extend([line_a, line_b])

        return lines

    def lines_for_rhyme_scheme(self, scheme, nwords):
        '''Generate a poem for the given rhyme scheme. Scheme should be
        provided as a string like ABAB, ABBAABBACDE, etc.
        '''
        rhymes = {}
        lines = []

        for slot in scheme:
            if slot not in rhymes:
                line = self.construct_line(nwords)
                lines.append(line)
                rhymes[slot] = line[-1]
            else:
                rhymeword = rhymes[slot]
                f = Filter(nwords - 1, Word.rhymeswith, [rhymeword])
                line = self.construct_line(nwords, filters=[f])
                lines.append(line)
        return lines

def testsetup():
    vg = VerseGenerator()
    vg.load_corpus(os.getcwd() + '/corpus/')
    return vg


def argstest(*args, **kwargs):
    return args, kwargs

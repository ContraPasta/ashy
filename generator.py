import os
import copy
import regex # Better unicode support than stdlib re
import codecs
import pickle
import random
import networkx
from phonology import Word
from functools import partial
from collections import namedtuple

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

Predicate = namedtuple('Predicate', ['partial', 'index'])
Constraint = namedtuple('Constraint', ['method', 'indices'])

class VerseGenerator(object):

    def __init__(self, text=None):
        self.chain = networkx.DiGraph()
        self.rhyme_table = {}
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

                # Check whether graph contains a word that rhymes with
                # this one. If it does, mark it. Need to check that it
                # hasn't been considered already so we don't count the
                # same word twice.
                if w not in self.chain:
                    finals = ''.join(current.final_phone_set())
                    if finals:
                        if finals not in self.rhyme_table:
                            self.rhyme_table[finals] = 1
                        else:
                            self.rhyme_table[finals] += 1

                        if self.rhyme_table[finals] > 1:
                            current.set_rhyme_in_collection(True)

                # Add connection between word and previous to the graph,
                # or increment the edge counter if it already exists
                if previous:
                    try:
                        self.chain[previous][current]['count'] += 1
                    except KeyError:
                        self.chain.add_edge(previous, current, count=1)

                previous = current

    def load_corpus(self, folder):
        '''Load text files in given folder and any subfolders into the
        markov chain.
        '''
        for root, _, fpaths in os.walk(folder):
            for path in fpaths:
                fullpath = os.path.join(root, path)
                with codecs.open(fullpath, 'r', 'utf-8-sig') as f:
                    try:
                        text = f.read()
                        self.load_text(text)
                    except UnicodeDecodeError as e:
                        msg = '{} is not utf-8'.format(fullpath)
                        raise IOError(msg) from e

    def dump_chain(self, path):
        '''
        Serialize the markov chain digraph to a file
        '''
        with open(path, 'wb') as f:
            pickle.dump(self.chain, f)

    def load_chain(self, path):
        '''
        Load a pickled markov chain. Wipes any existing data
        '''
        with open(path, 'rb') as f:
            self.chain = pickle.load(f)

    def shuffled_adjacent(self, node, pred=False):
        '''A generator which returns successors or predecessors to the
        given node in roulette-wheel selected random order.
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
                yield node

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

    def build_sequence(self, length, predicates, constraints, order='roulette'):
        ''' Traverse the graph in depth first order to build a sequence
        of the given length which fits the supplied predicates. If a
        matching sequence is not found, return partially constructed
        sequence. Begins with a randomly selected word from the graph
        '''

        # If there are any multiple-word constraints that begin at
        # this level, we need to create predicates so they can be
        # applied at future search levels
        def apply_constraints(cands, path, level, preds, cons):
            cs = [c for c in cons if c.indices[0] == level]
            search_nodes = []
            for can in cands:
                new_preds = []
                for con in cs:
                    curried = partial(con.method, can)
                    sub = con.indices[1:]
                    new_preds.extend([Predicate(curried, i) for i in sub])
                rec = {'word': can, 'parent': path, 'level': level,
                       'preds': preds + new_preds}
                search_nodes.append(rec)
            return search_nodes

        stack = []
        level = 0

        # Get candidate starting nodes
        apply = [p.partial for p in predicates if p.index == level]
        cands = self.filter_words(self.chain.nodes(), apply)
        random.shuffle(cands)
        branches = apply_constraints(cands, None, level, predicates, constraints)
        stack.extend(branches)

        while stack and level < length:
            path = stack.pop()
            prev = path['word']
            level = path['level'] + 1
            preds = path['preds']

            # Filter nodes following previous word to get candidates for
            # the next word in the sequence
            apply = [p.partial for p in preds if p.index == level]
            if order is 'roulette':
                succ = self.shuffled_adjacent(prev)
            elif order is 'random':
                succ = self.chain.successors(prev)
            else:
                raise ValueError('Invalid order argument: {}'.format(order))
            cands = self.filter_words(succ, apply)

            branches = apply_constraints(cands, path, level, preds, constraints)
            stack.extend(branches)

        # Walk backward through final recursive record to build the
        # resulting sentence
        result = []
        for i in range(level):
            result.append(path['word'])
            path = path['parent']

        return reverse(result)

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
            filtered = self.filter_words(self.chain.nodes(), preds)
            if not filtered:
                raise Exception('No words in chain for predicates {}'.format(preds))
            first = random.choice(filtered)

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

        #print('iterations: {}\npath: {}'o.format(iters, current_entry))

        line = []
        for i in range(level):
            line.append(current_entry['word'])
            current_entry = current_entry['parent']

        return reverse(line)

    def build_line(self, length, predicates=[]):
        '''
        Wrapper around `build_word_seq`. Calls `build_word_seq` as many
        times as necessary to fill the line with the correct number of
        words. This fixes the problem of short lines because the DFS
        couldn't find a path of the right length.
        '''
        slots = length
        line = []
        offset_preds = copy.copy(predicates)

        while len(line) < length:
            seq = self.build_word_seq(slots, offset_preds)
            line.extend(seq)
            slots = length - len(line)
            offset_preds = [(i - len(line), pred) for i, pred in predicates]

        return line

    def random_constraint(self, seq_len):
        '''
        Generate a random multi-word constraint to apply to a sequence
        generation.
        '''
        raise NotImplementedError

    def lines_to_string(self, lines):
        '''Convert the output of the different generation methods from
        lists of Words to strings for display or dispatch to other
        programmes
        '''
        strs = [' '.join(line).capitalize() for line in lines]
        return '\n'.join(strs)

    def lines_for_rhyme_scheme(self, nwords, scheme, device_thresh=0.4):
        '''Generate a poem for the given rhyme scheme. Scheme should be
        provided as a string like ABAB, ABBAABBACDE, etc.
        '''
        while True:
            rhymes = {}
            lines = []

            for slot in scheme:
                if slot not in rhymes:
                    predicate = (nwords - 1, Word.has_rhyme_in_collection)
                    line = self.build_line(nwords, [predicate])
                    lines.append(line)
                    rhymes[slot] = line[-1]
                else:
                    predicate = (nwords - 1, partial(Word.rhymeswith, rhymes[slot]))
                    line = self.build_line(nwords, [predicate])
                    lines.append(line)

            yield self.lines_to_string(lines)

def testsetup(folder):
    vg = VerseGenerator()
    vg.load_corpus(os.getcwd() + folder)
    return vg

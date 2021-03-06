import os
import regex # Better unicode support than stdlib re
import codecs
import pickle
import random
from networkx import DiGraph, single_source_shortest_path_length
from nltk import pos_tag
from functools import partial
from collections import namedtuple

from .phonology import Word

TAGSET = 'universal'

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

    def __init__(self, text=None, pos_tags=True, rhyme_table=True):
        self.rhyme_table = rhyme_table
        self.pos_tags = pos_tags
        self.chain = DiGraph()
        self.rhymes = {}
        if text:
            self.load_text(text)

    def __getitem__(self, item):
        return self.chain[item]

    def load_text(self, text):
        '''Add the given text to the Markov chain
        '''
        for sentence in tokenise(text):
            if self.pos_tags:
                tagged = pos_tag(sentence, tagset=TAGSET)
            else:
                tagged = ((w, None) for w in sentence)

            previous = None
            for w, tag in tagged:
                current = Word(w, tag)

                # Add connection between word and previous to the graph,
                # or increment the edge counter if it already exists
                if previous:
                    try:
                        self.chain[previous][current]['count'] += 1
                    except KeyError:
                        self.chain.add_edge(previous, current, count=1)

                previous = current

        if self.rhyme_table:
            rhymes = {w: self.rhymes_for_word(w) for w in self.chain.nodes()}
            self.rhymes = rhymes

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

    def roulette_select(self, node, pred=False):
        '''
        A generator which returns successors or predecessors to the
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
                return node

        return None

    def shuffled_successors(self, word, order='roulette'):
        '''
        Return successor words for given word in random order
        proportional to their frequency.
        '''
        if order is 'roulette':
            succ = self.chain.succ[word].items()
            key = lambda kv: random.expovariate(1/0.5) * kv[1]['count']
            return [pair[0] for pair in sorted(succ, key=key)]
        elif order is 'random':
            succ = self.chain.successors(word)
            random.shuffle(succ)
            return succ
        else:
            raise ValueError('Invalid order option: {}'.format(order))

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
            # the next word in the sequence.
            apply = [p.partial for p in preds if p.index == level]
            succ = self.shuffled_successors(prev, order=order)
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

    def rhymes_for_word(self, word):
        '''
        Search the graph for all words that rhyme with given word at all
        distances up to the maximum distance specified, and return them
        in a dict.
        '''
        nodes = single_source_shortest_path_length(self.chain, word)
        table = {}
        for node, level in nodes.items():
            if word.rhymeswith(node):
                try:
                    table[level].add(node)
                except KeyError:
                    table[level] = {node}
        return table

    def random_constraint(self, seq_len):
        '''
        Generate a random multi-word constraint to apply to a sequence
        generation.
        '''
        raise NotImplementedError

def testsetup(folder, tags=True):
    vg = VerseGenerator(pos_tags=tags)
    vg.load_corpus(os.getcwd() + folder)
    return vg

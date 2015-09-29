import os
import copy
import regex # Better unicode support than stdlib re
import codecs
import random
import networkx
from phonology import Word
from functools import partial

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

                # Add connection between word and previous to the graph
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

    def build_sequence(self, length, constraints=[], max_iters=6000):

        level = 0
        iters = 0

        cs = [c for c in constraints if c['indices'][0] == level]
        now = [c['predicate'] for c in cs if type(c['predicate']) is partial]
        later = [c for c in cs if type(c['predicate']) is not partial]

        succ = self.filter_words(self.chain.nodes(), now)
        first = random.choice(succ)
        record = {'word': first, 'path': None, 'level': level, 'constraints': []}


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

    def random_predicate(self, maxwords):
        '''
        Generate a random restriction to apply to a line, for example
        alliterate two words, internal rhymes, etc. I'll start with
        simple devices internal to the line.
        '''
        index_a = random.randint(0, maxwords - 1)
        index_b = random.randint(0, maxwords - 1)
        # Need a way of randomly selecting a comparison method from Word
        return None

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

    def lines_for_rhyme_scheme__(self, nwords, scheme, threshold=0.4):
        '''Generate a poem for the given rhyme scheme. Scheme should be
        provided as a string like ABAB, ABBAABBACDE, etc.
        '''
        rhymes = {}
        lines = []

        while True:
            for slot in scheme:
                predicates = []

                if slot not in rhymes:
                    rhyme_p = (nwords - 1, Word.has_rhyme_in_collection)
                else:
                    rhyme_p = (nwords - 1, partial(Word.rhymeswith, rhymes[slot]))
                predicates.append(rhyme_p)

                r = random.random()
                if r > threshold:
                    rand_p = self.random_predicate(nwords)
                    predicates.append(rand_p)

                line = self.build_line(nwords, predicates)
                lines.append(line)
                rhymes[slot] = line[-1]

            yield line

def testsetup():
    vg = VerseGenerator()
    vg.load_corpus(os.getcwd() + '/corpus/')
    return vg

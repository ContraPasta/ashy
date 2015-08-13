from __future__ import division
# Module for randomly generating lines of poetry, using a Markov chain
# extended with some other filters on the random selections
import random
import rhymedict
from collections import Counter


class VerseGenerator(object):

    # TODO:
    # The code that generates the Markov chain could probably be tidied
    # up so it only loops once, instead of through the source text once
    # and then through the chain dict to generate the frequencies.

    def __init__(self, source_text=''):
        """Build a Markov chain from the source text. Represented as a
        dictionary where keys are words and values are lists of
        (word, probability) tuples."""

        chain = {}
        sentences = [s.lower() for s in source_text.split('.')]

        for sentence in sentences:
            previous = None
            for word in sentence.split():
                if word not in chain:
                    chain[word] = []
                if previous:
                    chain[previous].append(word)
                previous = word

        self.chain = {}

        # Convert lists of following words into lists of (word, probability)
        # tuples
        for word, nexts in chain.iteritems():
            freqs = [(w, c / len(nexts)) for w, c in Counter(nexts).most_common()]
            self.chain[word] = freqs

    def roulette_select(self, pairs):
        """Roulette wheel selection"""

        r = random.random()
        current_sum = 0

        for pair in pairs:
            current_sum += pair[1]
            if r <= current_sum:
                return pair

        return None

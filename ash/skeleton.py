'''
Parser for a little "language" for specifying the form of randomly
generated poems. For example:
A rhyming couplet -
___[rh1]
___[rh1]
'''
import ply.lex as lex
from functools import partial

from .phonology import Word
from .generator import Predicate, Constraint

tokens = [
    'OPERATOR',
    'IDENTIFIER',
    'LBRACKET',
    'RBRACKET',
    'EMPTY'
]

t_OPERATOR   = r'[a-z]+'
t_LBRACKET   = r'\['
t_RBRACKET   = r'\]'
t_EMPTY      = r'_'
t_ignore     = ' \t'

# Convert identifier number strings to ints
def t_IDENTIFIER(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Track line numbers
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print('Illegal character {}'.format(t.value[0]))
    t.lexer.skip(1)

lexer = lex.lex()

operator_for_token = {
    'al': Word.alliterateswith,
    'rh': Word.rhymeswith,

}

def parse(lexer):
    constraints = {}
    word_index = -1
    while True:
        token = lexer.token()
        if not token: # End of input
            break
        if token.type == 'EMPTY':
            word_index += 1
        elif token.type == 'LBRACKET':
            word_index += 1
            token = lexer.token()
            while token.type != 'RBRACKET':
                op = operator_for_token[token.value]
                id = lexer.token().value
                try:
                    con = constraints[(token.value, id)]
                    thisop = con.method
                    thisidx = con.indices
                    new = Constraint(thisop, thisidx.append(word_index))
                except KeyError:
                    constraints[(token.value, id)] = Constraint(op, [word_index])
                token = lexer.token()
        else:
            raise SyntaxError('Unrecognised token: {}'.format(token))
    return (word_index + 1, list(constraints.values()))

def line_from_skeleton(gen, line):
    lexer.input(line)
    i, cs = parse(lexer)
    seq = map(str, gen.build_sequence(i, [], cs))
    return ' '.join(seq)

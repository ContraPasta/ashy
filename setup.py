#!/usr/bin/env python3

from distutils.core import setup

setup (
    name='ash',
    version='dev',
    description='ash is a Markov chain based random poetry generator.',
    author='Isaac Stead',
    author_email='isaac.stead@protonmail.com',
    url='https://github.com/isaac-rks/ash',
    packages=['ash'],
    package_data={'ash': ['data/cmudict.syl']},
    install_requires=[
        'networkx',
        'nltk',
        'ply',
        'regex'
    ]
)

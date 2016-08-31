#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:
'''Useful functions for evaluation of performance'''

def calc_prf(match, gold, test):
    '''Calculate Precision, Recall and F-Score, with:
    True Positive = match
    False Positive = test - match
    False Negative = gold - match

    >>> print calc_prf(0, 0, 0)
    (1.0, 1.0, 1.0)
    >>> print calc_prf(0, 0, 5)
    (0.0, 1.0, 0.0)
    >>> print calc_prf(0, 4, 5)
    (0.0, 0.0, 0.0)
    >>> print calc_prf(0, 4, 0)
    (0.0, 0.0, 0.0)
    >>> print calc_prf(2, 2, 8)
    (0.25, 1.0, 0.4)
    '''
    if gold == 0:
        if test == 0:
            return 1.0, 1.0, 1.0
        return 0.0, 1.0, 0.0
    if test == 0 or match == 0:
        return 0.0, 0.0, 0.0
    precision = match / float(test)
    recall = match / float(gold)
    try:
        fscore = 2 * match / (float(test + gold))
        return precision, recall, fscore
    except ZeroDivisionError:
        return 0.0, 0.0, 0.0

if __name__ == "__main__":
    print "Running doctest"
    import doctest
    doctest.testmod()

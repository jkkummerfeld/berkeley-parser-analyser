#!/usr/bin/env python

import sys

def cut_text_below(text, depth):
	'''Simplify text to only show the top parts of a tree
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 1)
	(ROOT)
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 2)
	(ROOT (NP) (VP))
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 3)
	(ROOT (NP (PRP I)) (VP (VBD ran) (NP)))
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 20)
	(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))
	'''
	# TODO: Adjust to play nicely with colours

	# Cut lower content
	cdepth = 0
	ntext = ''
	for char in text:
		if char == '(':
			cdepth += 1
		if cdepth <= depth:
			ntext += char
		if char == ')':
			cdepth -= 1

	# Walk back and remove extra whitespace
	text = ntext
	ntext = ''
	ignore = False
	for char in text[::-1]:
		if char == ')':
			ignore = True
			ntext += char
		elif ignore:
			if char != ' ':
				ntext += char
				ignore = False
		else:
			ntext += char
	return ntext[::-1]

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
	p = match / float(test)
	r = match / float(gold)
	try:
		f = (2 * p * r) / (p + r)
		return p, r, f
	except:
		return 0.0, 0.0, 0.0

if __name__ == "__main__":
	import doctest
	doctest.testmod()

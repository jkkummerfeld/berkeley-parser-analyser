#!/usr/bin/env python

def get_errors(self, gold):
	ans = []
	gold_spans = gold.span_list()
	test_spans = self.span_list()
	gold_spans.sort()
	test_spans.sort()
	test_span_set = {}
	for span in test_spans:
		key = (span[0], span[1], span[2].label) 
		if key not in test_span_set:
			test_span_set[key] = 0
		test_span_set[key] += 1
	gold_span_set = {}
	for span in gold_spans:
		key = (span[0], span[1], span[2].label) 
		if key not in gold_span_set:
			gold_span_set[key] = 0
		gold_span_set[key] += 1

	# Extra
	for span in test_spans:
		key = (span[0], span[1], span[2].label)
		if key not in gold_span_set or gold_span_set[key] < 1:
			if span[2].word is None:
				ans.append(('extra', (span[0], span[1]), span[2].label, span[2]))
		else:
			gold_span_set[key] -= 1

	# Missing and crossing
	for span in gold_spans:
		key = (span[0], span[1], span[2].label)
		if key not in test_span_set or test_span_set[key] < 1:
			if span[2].word is not None:
				continue
			is_crossing = False
			for tspan in test_span_set:
				if tspan[0] < span[0] < tspan[1] < span[1]:
					is_crossing = True
					break
				if span[0] < tspan[0] < span[1] < tspan[1]:
					is_crossing = True
					break
			if is_crossing:
				ans.append(('crossing', (span[0], span[1]), span[2].label, span[2]))
			else:
				ans.append(('missing', (span[0], span[1]), span[2].label, span[2]))
		else:
			test_span_set[key] -= 1
	return ans

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
		f = 2 * match / (float(test + gold))
		return p, r, f
	except:
		return 0.0, 0.0, 0.0

if __name__ == "__main__":
	print "Running doctest"
	import doctest
	doctest.testmod()


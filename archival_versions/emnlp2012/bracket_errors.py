#!/usr/bin/env python

import sys
import error_tree

class BracketError:
	def __init__(self, node, extra, missing):
		assert extra != missing
		self.node = node
		self.extra = extra
		self.missing = missing
	
	def __repr__(self):
		ans = 'extra'
		if self.missing:
			ans = 'missing'
		ans += ' ' + self.node.__repr__(single_line=True)
		return ans

def get_constituents_for_span(span, tree):
	'''For a given span, find the lowest node in the tree that has a set of
	constituents that cover the span.  Useful for cases like a missing error,
	where we wish to find the things it will cover.

	>>> import ptb
	>>> tree = ptb.PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP (NNP Mr.) (NNP Vinken)) (VP (VBZ is) (NP (NP (NN chairman)) (PP (IN of) (NP (NP (NNP Elsevier) (NNP N.V.)) (NP (DT the) (NNP Dutch) (VBG publishing) (NN group))))))))")
	>>> etree = error_tree.Error_Tree()
	>>> etree.set_by_ptb(tree)
	>>> print get_constituents_for_span((9, 11), etree)
	((NP (DT the) (NNP Dutch) (VBG publishing) (NN group)), 2, 3)
	>>> print get_constituents_for_span((6, 9), etree)
	(None, -1, -1)
	>>> print get_constituents_for_span((5, 7), etree)
	((NP (NP (NNP Elsevier) (NNP N.V.)) (NP (DT the) (NNP Dutch) (VBG publishing) (NN group))), 0, 0)
	'''
	left, right = -1, -1
	ptree = None
	while ptree != tree:
		ptree = tree
		for i in xrange(len(tree.subtrees)):
			if tree.subtrees[i].span[0] == span[0] and span[1] == tree.subtrees[i].span[1]:
				return tree, i, i
			elif tree.subtrees[i].span[0] <= span[0] and span[1] <= tree.subtrees[i].span[1]:
				tree = tree.subtrees[i]
				break
			elif tree.subtrees[i].span[0] == span[0]:
				left = i
			elif tree.subtrees[i].span[1] == span[1]:
				right = i
				return tree, left, right
	return None, -1, -1

def get_constituents_for_crossing_span(span, tree):
	'''For a crossing span, find the lowest node in the tree that has a set of
	constituents that cover the span.'''
	left, right = -1, -1
	ptree = None
	while ptree != tree:
		ptree = tree
		for i in xrange(len(tree.subtrees)):
			if tree.subtrees[i].span[0] <= span[0] and span[1] <= tree.subtrees[i].span[1]:
				tree = tree.subtrees[i]
				break
			elif tree.subtrees[i].span[0] <= span[0] < tree.subtrees[i].span[1]:
				left = i
			elif tree.subtrees[i].span[0] < span[1] <= tree.subtrees[i].span[1]:
				right = i
				break
	return tree, left, right

def get_errors(gold, test):
	'''Sort all brackets into matching, extra and missing.  The errors are
	returned in a dictionary, and the matching brackets are returned separately.

	Note - This function also sets the relevant members in the test tree (extra
	and lists of crossing entries).
	'''
	gold_spans, gold_span_set = gold.get_spans()
	test_spans, test_span_set = test.get_spans()

	errors = {'miss': [], 'extra': []}
	matching_brackets = []
	if gold is None or test is None or gold.label is None or test.label is None:
		return None

	# Missing
	for key in gold_span_set:
		if key not in test_span_set:
			for label in gold_span_set[key]:
				for node in gold_span_set[key][label]:
					errors['miss'].append(BracketError(node, False, True))

	# Extra
	for key in test_span_set:
		if key not in gold_span_set:
			for label in test_span_set[key]:
				for node in test_span_set[key][label]:
					errors['extra'].append(BracketError(node, True, False))
					node.extra = True
					for error in errors['miss']:
						gkey = error.node.span
						if gkey[0] < key[0] < gkey[1] < key[1]:
							node.crossing_ends.append(error)
						if key[0] < gkey[0] < key[1] < gkey[1]:
							node.crossing_starts.append(error)

	# Same span, but still an error
	for key in test_span_set:
		if key in gold_span_set:
			relevant_gold_spans = [span for span in gold_spans if key == (span.span[0], span.span[1])]
			relevant_test_spans = [span for span in test_spans if key == (span.span[0], span.span[1])]

			# remove matching spans
			# Note that there is a little randomness here, as the first match is
			# accepted (when there could be many)
			while True:
				matching = None
				for span in relevant_test_spans:
					for gspan in relevant_gold_spans:
						if gspan.label == span.label:
							matching = (gspan, span)
							break
					# once a matching is found, break and process it
					if matching is not None:
						break
				# When no matching can be found, break out
				if matching is None:
					break
				matching_brackets.append(matching)
				relevant_gold_spans.remove(matching[0])
				relevant_test_spans.remove(matching[1])

			if len(relevant_gold_spans) == len(relevant_test_spans) == 0:
				continue
			for node in relevant_gold_spans:
				errors['miss'].append(BracketError(node, False, True))
			for node in relevant_test_spans:
				errors['extra'].append(BracketError(node, True, False))
				node.extra = True
	return (errors, matching_brackets)

def get_extra_error(error_list, tree):
	'''Get the error in the list that this tree relates to
	'''
	for error in error_list:
		if error.extra:
			if error.node == tree.basis_tree:
				return error
	return None

def get_extra_tree(error, tree):
	if tree.basis_tree == error.node:
		return tree
	for subtree in tree.subtrees:
		ans = get_extra_tree(error, subtree)
		if ans is not None:
			return ans
	return None

def get_crossing_brackets(error, tree):
	ans = []
	if tree.span[0] < error.node.span[0] < tree.span[1] < error.node.span[1]:
		ans.append(tree)
	elif error.node.span[0] < tree.span[0] < error.node.span[1] < tree.span[1]:
		ans.append(tree)
	for subtree in tree.subtrees:
		ans += get_crossing_brackets(error, subtree)
	return ans

def error_crosses_bracket(error, tree):
	if tree.span[0] < error.node.span[0] < tree.span[1] < error.node.span[1]:
		return True
	if error.node.span[0] < tree.span[0] < error.node.span[1] < tree.span[1]:
		return True
	for subtree in tree.subtrees:
		if error_crosses_bracket(error, subtree):
			return True
	return False

def get_missing_errors(error_set, test_tree):
	ans = []
	for error in error_set['miss']:
		span = error.node.span
		crossing = False
		ctree = test_tree
		ptree = None
		while ctree != ptree:
			ptree = ctree
			for subtree in ctree.subtrees:
				cspan = subtree.span
				if cspan[0] < span[0] < cspan[1] < span[1]:
					crossing = True
					break
				if span[0] < cspan[0] < span[1] < cspan[1]:
					crossing = True
					break
				if cspan[0] <= span[0] < span[1] <= cspan[1]:
					ctree = subtree
					break
		ans.append((span[0], span[1], error.node.label, crossing))
	return ans

def calc_depth(error):
	node = error.node
	depth = 0
	while node.parent is not None:
		node = node.parent
		depth += 1
	return depth
def sort_by_depth(errors):
	errors.sort(reverse=True, key=calc_depth)

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print "Usage:\n%s <gold> <test>" % sys.argv[0]
		print "The files should contain one parse per line, with a 1-1 mapping (use blank lines where there is a missing parse)."
		print "Running doctest"
		import doctest
		doctest.testmod()
	else:
		import ptb

		gold_in = open(sys.argv[1])
		test_in = open(sys.argv[2])
		while True:
			gold_text = gold_in.readline()
			test_text = test_in.readline()
			if gold_text == '' or test_text == '':
				break

			gold_text = gold_text.strip()
			test_text = test_text.strip()
			if len(gold_text) == 0 or len(test_text) == 0:
				continue

			tree = ptb.PTB_Tree()
			tree.set_by_text(gold_text)
			tree = ptb.apply_collins_rules(tree)
			gold_tree = error_tree.Error_Tree()
			gold_tree.set_by_ptb(tree)

			tree = ptb.PTB_Tree()
			tree.set_by_text(test_text)
			tree = ptb.apply_collins_rules(tree)
			test_tree = error_tree.Error_Tree()
			test_tree.set_by_ptb(tree)

			error_set = get_errors(gold_tree, test_tree)[0]
			missing = get_missing_errors(error_set, test_tree)
			print test_tree.colour_repr(missing=missing)

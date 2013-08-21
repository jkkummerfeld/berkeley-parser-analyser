#!/usr/bin/env python

import sys
import error_tree

'''These functions fix the given error in the given tree. In doing so other
errors may also be fixed. The functions return the full set of errors that are
fixed by the change.
'''

def repair_extra_node(error, tree, to_remove=None):
	'''Remove an extra bracket

	>>> import ptb, error_tree, bracket_errors
	>>> tree = ptb.PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))")
	>>> tree = ptb.apply_collins_rules(tree)
	>>> gold_tree = error_tree.Error_Tree()
	>>> gold_tree.set_by_ptb(tree)
	>>> 
	>>> tree = ptb.PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VP (VBD ate)) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))")
	>>> tree = ptb.apply_collins_rules(tree)
	>>> test_tree = error_tree.Error_Tree()
	>>> test_tree.set_by_ptb(tree)
	>>> 
	>>> error_set = bracket_errors.get_errors(gold_tree, test_tree)[0]
	>>> copy = test_tree.copy()
	>>> print copy
	(ROOT (S (NP (PRP I)) (VP (VP (VBD ate)) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))
	>>> repair_extra_node(error_set['extra'][0], copy)
	>>> print copy
	(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))
	'''
	if to_remove is None:
		to_remove = tree.get_copy(error.node)
		if to_remove is None:
			print "Asked to fix error involving node that could not found"
			return
	parent = to_remove.parent
	if parent is None:
		print "Request to fix extra node without parent"
		return
	for index in xrange(len(parent.subtrees)):
		if parent.subtrees[index] == to_remove:
			parent.subtrees = parent.subtrees[:index] + to_remove.subtrees + parent.subtrees[index+1:]
			for child in to_remove.subtrees:
				child.parent = parent
			break

def repair_extra_missing_pair(merror, eerror, tree):
	'''Takes the case of a missing and extra bracket that have the same span (but
	differnet labels) and fixes both.

	>>> import ptb, error_tree, bracket_errors
	>>> tree = ptb.PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))")
	>>> tree = ptb.apply_collins_rules(tree)
	>>> gold_tree = error_tree.Error_Tree()
	>>> gold_tree.set_by_ptb(tree)
	>>> 
	>>> tree = ptb.PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (NP (IN with) (NP (NNP cutlery))))))")
	>>> tree = ptb.apply_collins_rules(tree)
	>>> test_tree = error_tree.Error_Tree()
	>>> test_tree.set_by_ptb(tree)
	>>> 
	>>> error_set = bracket_errors.get_errors(gold_tree, test_tree)[0]
	>>> copy = test_tree.copy()
	>>> print copy
	(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (NP (IN with) (NP (NNP cutlery))))))
	>>> repair_extra_missing_pair(error_set['miss'][0], error_set['extra'][0], copy)
	>>> print copy
	(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))
	'''
	assert merror.node.span == eerror.node.span
	to_fix = tree.get_copy(eerror.node)
	if to_fix is None:
		print "Could not find the span for the given error"
		return
	if not to_fix.extra:
		print "Node no longer considered extra"
		return
	to_fix.label = merror.node.label
	to_fix.extra = False

def repair_missing_node(error, tree, failure_expected=False):
	'''Creates a new node that was previously missing. Does not handle the
	crossing case.

	>>> import ptb, error_tree, bracket_errors
	>>> tree = ptb.PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))")
	>>> tree = ptb.apply_collins_rules(tree)
	>>> gold_tree = error_tree.Error_Tree()
	>>> gold_tree.set_by_ptb(tree)
	>>> 
	>>> tree = ptb.PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (IN with) (NP (NNP cutlery)))))")
	>>> tree = ptb.apply_collins_rules(tree)
	>>> test_tree = error_tree.Error_Tree()
	>>> test_tree.set_by_ptb(tree)
	>>> 
	>>> error_set = bracket_errors.get_errors(gold_tree, test_tree)[0]
	>>> copy = test_tree.copy()
	>>> print copy
	(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (IN with) (NP (NNP cutlery)))))
	>>> repair_missing_node(error_set['miss'][0], copy)
	True
	>>> print copy
	(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))
	'''
	espan = error.node.span
	# find the set of nodes it covers
	ctree = tree
	ptree = None
	left = -1
	right = -1
	while ptree != ctree: 
		ptree = ctree
		i = 0
		for subtree in ctree.subtrees:
			if subtree.span[0] == espan[0]:
				left = i
			if subtree.span[1] == espan[1]:
				right = i
				if left >= 0:
					break
			if subtree.span[0] <= espan[0] and espan[1] <= subtree.span[1]:
				ctree = subtree
				left, right, = -1, -1
				break
			i += 1

	if -1 < left <= right:
		node = error_tree.Error_Tree()
		node.label = error.node.label
		node.word = error.node.word
		node.parent = ctree
		node.span = (error.node.span[0], error.node.span[1])
		node.subtrees = []
		for i in xrange(left, right+1):
			node.subtrees.append(ctree.subtrees[i])
			ctree.subtrees[i].parent = node
		ctree.subtrees = ctree.subtrees[:left] + [node] + ctree.subtrees[right+1:]
		return True
	else:
		if not failure_expected:
			print "Request to fix missing bracket that crosses"
			print error
			print tree#.__repr__(single_line=False)
			print ctree#.__repr__(single_line=False)
			#print tree.colour_repr()
			print left, right
			print espan
			for subtree in ctree.subtrees:
				print subtree.span
			assert False
		return False

###def repair_crossing_missing_node(merror, tree, target_level, ungrouped):
###	'''Moves nodes and creates a new node to fix the error. Will also detect what
###	other errors have been fixed in the process.
###	
###	>>> import ptb, error_tree, bracket_errors
###	>>> tree = ptb.PTB_Tree()
###	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))")
###	>>> tree = ptb.apply_collins_rules(tree)
###	>>> gold_tree = error_tree.Error_Tree()
###	>>> gold_tree.set_by_ptb(tree)
###	>>> 
###	>>> tree = ptb.PTB_Tree()
###	>>> tree.set_by_text("(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza) (IN with)) (NP (NNP cutlery)))))")
###	>>> tree = ptb.apply_collins_rules(tree)
###	>>> test_tree = error_tree.Error_Tree()
###	>>> test_tree.set_by_ptb(tree)
###	>>> 
###	>>> error_set = bracket_errors.get_errors(gold_tree, test_tree)[0]
###	>>> error_list = []
###	>>> for etype in error_set:
###	...   for error in error_set[etype]:
###	...     error_list.append(error)
###	>>> copy = test_tree.copy()
###	>>> print copy
###	(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza) (IN with)) (NP (NNP cutlery)))))
###	>>> target_parent = copy.subtrees[0].subtrees[1]
###	>>> fixed = repair_crossing_missing_node(error_set['miss'][1], copy, target_parent, error_list)
###	>>> assert len(fixed) == 3
###	>>> print copy
###	(ROOT (S (NP (PRP I)) (VP (VBD ate) (NP (NNP pizza)) (PP (IN with) (NP (NNP cutlery))))))

###	>>> import ptb, error_tree, bracket_errors
###	>>> tree = ptb.PTB_Tree()
###	>>> tree.set_by_text("(ROOT (A (w w0) (B (w w1) (C (w w2) (w w3)))) (w w4) (w w5))")
###	>>> tree = ptb.apply_collins_rules(tree)
###	>>> gold_tree = error_tree.Error_Tree()
###	>>> gold_tree.set_by_ptb(tree)
###	>>> 
###	>>> tree = ptb.PTB_Tree()
###	>>> tree.set_by_text("(ROOT (A (w w0) (B (w w1) (C (w w2) (w w3) (w w4)))) (w w5))")
###	>>> tree = ptb.apply_collins_rules(tree)
###	>>> test_tree = error_tree.Error_Tree()
###	>>> test_tree.set_by_ptb(tree)
###	>>> 
###	>>> error_set = bracket_errors.get_errors(gold_tree, test_tree)[0]
###	>>> print error_set['miss'][0]
###	missing (C (w w2) (w w3))
###	>>> copy = test_tree.copy()
###	>>> fixed = repair_crossing_missing_node(error_set['miss'][0], copy, target_parent, error_list)
###	>>> print copy
###	(ROOT (A (w w0) (B (w w1) (C (w w2) (w w3)))) (w w4) (w w5))

###	>>> import ptb, error_tree, bracket_errors
###	>>> tree = ptb.PTB_Tree()
###	>>> tree.set_by_text("(ROOT (A (w w0) (B (w w1) (C (w w2) (w w3)))))")
###	>>> tree = ptb.apply_collins_rules(tree)
###	>>> gold_tree = error_tree.Error_Tree()
###	>>> gold_tree.set_by_ptb(tree)
###	>>> 
###	>>> tree = ptb.PTB_Tree()
###	>>> tree.set_by_text("(ROOT (A (w w0) (B (w w1) (C (w w3)))) (w w3))")
###	>>> tree = ptb.apply_collins_rules(tree)
###	>>> test_tree = error_tree.Error_Tree()
###	>>> test_tree.set_by_ptb(tree)
###	>>> 
###	>>> error_set = bracket_errors.get_errors(gold_tree, test_tree)[0]
###	>>> print error_set['miss'][0]
###	missing (C (w w2) (w w3))
###	>>> copy = test_tree.copy()
###	>>> fixed = repair_crossing_missing_node(error_set['miss'][0], copy, target_parent, error_list)
###	>>> print copy
###	(ROOT (A (w w0) (B (w w1) (C (w w2) (w w3)))))
###	'''
###	# Find all the spans that have to move
###	# Start from each word, and move up until about to leave the new span
###	to_move = {}
###	espan = merror.node.span
###	for w in xrange(espan[0], espan[1]):
###		# find word
###		wtree = tree
###		while wtree.word is None:
###			for subtree in wtree.subtrees:
###				if subtree.span[0] <= w < subtree.span[1]:
###					wtree = subtree
###					break
###		while True:
###			if wtree.parent.span[0] < espan[0] or espan[1] < wtree.parent.span[1]:
###				break
###			wtree = wtree.parent
###		if wtree.span[0] not in to_move:
###			to_move[wtree.span[0]] = wtree

###	# create new structure
###	node = error_tree.Error_Tree()
###	node.label = merror.node.label
###	node.word = merror.node.word
###	node.span = (merror.node.span[0], merror.node.span[1])
###	
###	# rip out the parts that will combine to form this
###	node.subtrees = []
###	keys = to_move.keys()
###	keys.sort()
###	modified_parents = []
###	for start in keys:
###		mover = to_move[start]
###		mover.parent.subtrees.remove(mover)
###		modified_parents.append(mover.parent)
###		mover.parent = node
###		node.subtrees.append(mover)

###	# place in its new location
###	if len(target_level.subtrees) == 0:
###		target_level.subtrees.append(node)
###		node.parent = target_level
###	elif target_level.span[0] != target_level.subtrees[0].span[0]:
###		target_level.subtrees.insert(0, node)
###		node.parent = target_level
###	elif target_level.span[1] != target_level.subtrees[-1].span[0]:
###		target_level.subtrees.append(node)
###		node.parent = target_level
###	else:
###		for i in xrange(len(target_level.subtrees)):
###			if target_level.subtrees[i].span[0] < node.span[0] < target_level.subtrees[i].span[1]:
###				target_level.subtrees.insert(i + 1, node)
###				break
###	tree.update_span()

###	fixed = [merror]
###	# Check the case of a missing bracket that now exists
###	for error in ungrouped:
###		if error.missing:
###			span = tree.get_span(error.node.span)
###			if span is None:
###				continue
###			found = False
###			for tspan in span:
###				if tspan.extra and tspan.label == error.node.label:
###					for error2 in ungrouped:
###						if error2.node == tspan.basis_tree:
###							fixed.append(error)
###							fixed.append(error2)
###							tspan.extra = False
###							found = True
###							break
###				if found:
###					break
###	# The case of an extra bracket that is now a unary over an equivalent correct
###	# bracket
###	for parent in modified_parents:
###		if parent.extra:
###			for error in ungrouped:
###				if error.missing and error.node.span == parent.span and error.node.label == parent.label:
###					for eerror in ungrouped:
###						if eerror.node == parent.basis_tree:
###							fixed.append(eerror)
###							fixed.append(error)
###							parent.extra = False
###							break
###					break
###		# Should we remove the link to clone parent here? It is no longer really accurate
###	return fixed

if __name__ == '__main__':
	import doctest
	doctest.testmod()

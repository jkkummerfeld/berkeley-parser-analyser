#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

import sys
from nlp_util import pstree, render_tree, init, treebanks, parse_errors, head_finder, tree_transform
from collections import defaultdict
from StringIO import StringIO

def get_label(tree):
	if tree.word is None:
		return tree.label
	if tree.label == 'PU':
		return tree.label + tree.word
	else:
		return tree.label


def get_preterminals(tree, ans=None):
	return_tuple = False
	if ans is None:
		ans = []
		return_tuple = True
	if tree.is_terminal():
		ans.append(tree.label)
	for subtree in tree.subtrees:
		assert subtree != tree
		get_preterminals(subtree, ans)
	if return_tuple:
		return tuple(ans)


def gen_different_label_successor(ctree, span, cur_label, new_label):
	success, response = tree_transform.change_label(ctree, new_label, span, cur_label, False)
	assert success, response

	ntree, nnode = response

	info = {
		'type': 'relabel',
		'change': (cur_label, new_label),
		'subtrees': [get_label(subtree) for subtree in nnode.subtrees],
		'parent': nnode.parent.label,
		'span': nnode.span,
		'family': [get_label(subtree) for subtree in nnode.parent.subtrees],
		'auto preterminals': get_preterminals(nnode),
		'auto preterminal span': nnode.span,
		'over_word': len(nnode.subtrees) == 1 and nnode.subtrees[0].word is not None
	}

	return (True, ntree, info)


def gen_missing_successor(ctree, error):
	success, response = tree_transform.add_node(ctree, error[1], error[2], in_place=False)
	assert success, response

	ntree, nnode = response
	nnode_index = nnode.parent.subtrees.index(nnode)

	info = {
		'type': 'add',
		'label': get_label(nnode),
		'span': nnode.span,
		'subtrees': [get_label(subtree) for subtree in nnode.subtrees],
		'parent': nnode.parent.label,
		'family': [get_label(subtree) for subtree in nnode.parent.subtrees],
		'auto preterminals': get_preterminals(nnode),
		'auto preterminal span': nnode.span,
		'left siblings': nnode.parent.subtrees[:nnode_index],
		'right siblings': nnode.parent.subtrees[nnode_index + 1:],
		'over_word': len(nnode.subtrees) == 1 and nnode.subtrees[0].is_terminal(),
		'over words': reduce(lambda prev, node: prev and node.is_terminal(), nnode.subtrees, True),
	}

	return (True, ntree, info)


def gen_extra_successor(ctree, error, gold):
	success, response = tree_transform.remove_node(ctree, error[1], error[2], in_place=False)
	assert success, response

	parent, dnode, spos, epos  = response
	ntree = parent.root()

	info = {
		'type': 'remove',
		'label': get_label(dnode),
		'span': dnode.span,
		'subtrees': [get_label(subtree) for subtree in dnode.subtrees],
		'parent': parent.label,
		'family': [get_label(subtree) for subtree in parent.subtrees[:spos] + [dnode] + parent.subtrees[epos:]],
		'left siblings': [get_label(subtree) for subtree in parent.subtrees[:spos]],
		'right siblings': [get_label(subtree) for subtree in parent.subtrees[epos:]],
		'over words': reduce(lambda prev, node: prev and node.is_terminal(), dnode.subtrees, True),
		'over_word': len(dnode.subtrees) == 1 and dnode.subtrees[0].is_terminal(),
		'auto preterminals': get_preterminals(parent),
		'auto preterminal span': parent.span
	}

	if len(info['right siblings']) == 1:
		sibling = parent.subtrees[-1]
		for node in sibling:
			if node.word is not None:
				gold_eq = gold.get_nodes('lowest', node.span[0], node.span[1])
				if gold_eq is not None:
					if get_label(node) != gold_eq.label:
						info['POS confusion'] = (get_label(node), get_label(gold_eq))

	return (True, ntree, info)


def gen_move_successor(source_span, left, right, new_parent, cerrors, gold):
	success, response = tree_transform.move_nodes(source_span.subtrees[left:right+1], new_parent, False)
	assert success, response

	ntree, nodes, new_parent = response
	new_left = new_parent.subtrees.index(nodes[0])
	new_right = new_parent.subtrees.index(nodes[-1])

	# Find Lowest Common Ancestor of the new and old parents
	full_span = (min(source_span.span[0], new_parent.span[0]), max(source_span.span[1], new_parent.span[1]))
	lca = new_parent
	while not (lca.span[0] <= full_span[0] and full_span[1] <= lca.span[1]):
		lca = lca.parent

	info = {
		'type': 'move',
		'old_parent': get_label(source_span),
		'new_parent': get_label(new_parent),
		'movers': [get_label(node) for node in nodes],
		'mover info': [(get_label(node), node.span) for node in nodes],
		'new_family': [get_label(subtree) for subtree in new_parent.subtrees],
		'old_family': [get_label(subtree) for subtree in source_span.subtrees],
		'start left siblings': [get_label(node) for node in source_span.subtrees[:left]],
		'start right siblings': [get_label(node) for node in source_span.subtrees[right+1:]],
		'end left siblings': [get_label(node) for node in new_parent.subtrees[:new_left]],
		'end right siblings': [get_label(node) for node in new_parent.subtrees[new_right+1:]],
		'auto preterminals': get_preterminals(lca),
		'auto preterminal span': lca.span
	}

	if left == right and nodes[-1].span[1] - nodes[-1].span[0] == 1:
		preterminal = nodes[-1]
		while preterminal.word is None:
			preterminal = preterminal.subtrees[0]
		gold_eq = gold.get_nodes('lowest', preterminal.span[0], preterminal.span[1])
		if gold_eq is not None:
			info['POS confusion'] = (get_label(preterminal), get_label(gold_eq))

	# Consider fixing a missing node in the new location as well
	nerrors = parse_errors.ParseErrorSet(gold, ntree)
	to_fix = None
	for error in nerrors.missing:
		if error[1][0] <= nodes[0].span[0] and nodes[-1].span[1] <= error[1][1]:
			if error[1] == (nodes[0].span[0], nodes[-1].span[1]):
				continue
			if error[1][0] < new_parent.span[0] or error[1][1] > new_parent.span[1]:
				continue
			if to_fix is None or to_fix[1][0] < error[1][0] or error[1][1] < to_fix[1][1]:
				to_fix = error
	if to_fix is not None:
		info['added and moved'] = True
		info['added label'] = error[2]

		unmoved = []
		for node in new_parent.subtrees:
			if to_fix[1][0] < node.span[0] and node.span[1] < to_fix[1][1]:
				if node not in nodes:
					unmoved.append(node)
		info['adding node already present'] = False
		if len(unmoved) == 1 and unmoved[0].label == to_fix[2]:
			info['adding node already present'] = True

		success, response = tree_transform.add_node(ntree, to_fix[1], to_fix[2], in_place=False)
		assert success, response
		ntree, nnode = response

	return (False, ntree, info)
			

def successors(ctree, cerrors, gold):
	# Change the label of a node
	for merror in cerrors.missing:
		for eerror in cerrors.extra:
			if merror[1] == eerror[1]:
				yield gen_different_label_successor(ctree, eerror[1], eerror[2], merror[2])

	# Add a node
	for error in cerrors.missing:
		yield gen_missing_successor(ctree, error)

	# Remove a node
	for error in cerrors.extra:
		yield gen_extra_successor(ctree, error, gold)

	# Move nodes
	for source_span in ctree:
		# Consider all continuous sets of children
		for left in xrange(len(source_span.subtrees)):
			for right in xrange(left, len(source_span.subtrees)):
				if left == 0 and right == len(source_span.subtrees) - 1:
					# Note, this means in cases like (NP (NN blah)) we can't move the NN
					# out, we have to move the NP level.
					continue
				new_parents = []

				# Consider moving down within this bracket
				if left != 0:
					new_parent = source_span.subtrees[left-1]
					while not new_parent.is_terminal():
						if cerrors.is_extra(new_parent):
							new_parents.append(new_parent)
						new_parent = new_parent.subtrees[-1]
				if right != len(source_span.subtrees) - 1:
					new_parent = source_span.subtrees[right+1]
					while not new_parent.is_terminal():
						if cerrors.is_extra(new_parent):
							new_parents.append(new_parent)
						new_parent = new_parent.subtrees[0]

				# If source_span is extra
				if cerrors.is_extra(source_span) and (left == 0 or right == len(source_span.subtrees) - 1):
					# Consider moving this set out to the left
					if left == 0:
						if source_span.subtrees[left].span[0] > 0:
							for new_parent in ctree.get_nodes('all', end=source_span.subtrees[left].span[0]):
								if cerrors.is_extra(new_parent):
									new_parents.append(new_parent)

					# Consider moving this set out to the right
					if right == len(source_span.subtrees) - 1:
						if source_span.subtrees[right].span[1] < ctree.span[1]:
							for new_parent in ctree.get_nodes('all', start=source_span.subtrees[right].span[1]):
								if cerrors.is_extra(new_parent):
									new_parents.append(new_parent)

					# Consider moving this set of spans up
					if left == 0:
						# Move up while on left
						new_parent = source_span.parent
						while not (new_parent.parent is None):
							new_parents.append(new_parent)
							if new_parent.parent.span[0] < source_span.span[0]:
								break
							new_parent = new_parent.parent
					if right == len(source_span.subtrees) - 1:
						# Move up while on right
						new_parent = source_span.parent
						while not (new_parent.parent is None):
							new_parents.append(new_parent)
							if new_parent.parent.span[1] > source_span.span[1]:
								break
							new_parent = new_parent.parent

				for new_parent in new_parents:
					yield gen_move_successor(source_span, left, right, new_parent, cerrors, gold)


def greedy_search(gold, test, classify):
	# Initialise with the test tree
	cur = (test.clone(), {'type': 'init'}, 0)

	# Search while there is still something in the fringe
	iters = 0
	path = []
	while True:
		path.append(cur)
		if iters > 100:
			return (0, iters), None
		# Check for victory
		ctree = cur[0]
		cerrors = parse_errors.ParseErrorSet(gold, ctree)
		if len(cerrors) == 0:
			final = cur
			break

		best = None
		for fixes, ntree, info in successors(ctree, cerrors, gold):
			if not ntree.check_consistency():
				raise Exception("Inconsistent tree! {}".format(ntree))
			nerrors = parse_errors.get_errors(ntree, gold)
			change = len(cerrors) - len(nerrors)
			if change < 0:
				continue
			if best is None or change > best[2]:
				best = (ntree, info, change)
		cur = best
		iters += 1
	
	for step in path:
		classify(step[1], gold, test)
	
	return (0, iters), path


def compare_trees(gold_tree, test_tree, out_dict, error_counts, classify):
	""" Compares two trees. """
	init_errors = parse_errors.get_errors(test_tree, gold_tree)
	error_count = len(init_errors)
	print >> out_dict['out'], "{} Initial errors".format(error_count)
	iters, path = greedy_search(gold_tree, test_tree, classify)
	print >> out_dict['out'], "{} on fringe, {} iterations".format(*iters)
	if path is not None:
		print >> out_dict['test_trees'], test_tree
		print >> out_dict['gold_trees'], gold_tree
		for tree in path[1:]:
			print >> out_dict['out'], "{} Error:{}".format(str(tree[2]),tree[1]['classified_type'])

		if len(path) > 1:
			for tree in path:
				print >> out_dict['out'], "Step:{}".format(tree[1]['classified_type'])
				error_counts[tree[1]['classified_type']].append(tree[2])
				print >> out_dict['out'], tree[1]
				print >> out_dict['out'], render_tree.text_coloured_errors(tree[0], gold=gold_tree).strip()
	else:
		print >> out_dict['out'], "no path found"
	print >> out_dict['err'], ""
	print >> out_dict['out'], ""


def read_tree(text, out_dict, label):
	fake_file = StringIO(text)
	complete_tree = treebanks.ptb_read_tree(fake_file)
	if complete_tree is None:
		return None
	treebanks.homogenise_tree(complete_tree)
	if not complete_tree.label.strip():
		complete_tree.label = 'ROOT'
	tree = treebanks.apply_collins_rules(complete_tree)
	if tree is None:
		for out in [out_dict['out'], out_dict['err']]:
			print >> out, "Empty {} tree".format(label)
			print >> out, complete_tree
			print >> out, tree
	return tree


def compare(gold_text, test_text, out_dict, error_counts, classify):
	""" Compares two trees in text form.
	This checks for empty trees and mismatched numbers
	of words.
	"""
	gold_text = gold_text.strip()
	test_text = test_text.strip()
	if len(gold_text) == 0:
		print >> out_dict['out'], "No gold tree"
		print >> out_dict['err'], "No gold tree"
		return
	elif len(test_text) == 0:
		print >> out_dict['out'], "Not parsed"
		print >> out_dict['err'], "Not parsed"
		return
	gold_tree = read_tree(gold_text, out_dict, 'gold')
	test_tree = read_tree(test_text, out_dict, 'test')
	if gold_tree is None or test_tree is None:
		print >> out_dict['out'], "Not parsed, but had output"
		print >> out_dict['err'], "Not parsed, but had output"
		print >> out_dict['init_errors'], "Not parsed, but had output"
		return
	print >> out_dict['init_errors'], render_tree.text_coloured_errors(test_tree, gold_tree).strip()

	gold_words = gold_tree.word_yield()
	test_words = test_tree.word_yield()
	if len(test_words.split()) != len(gold_words.split()):
		for out in [out_dict['out'], out_dict['err']]:
			print >> out, "Sentence lengths do not match..."
			print >> out, "Gold: " + gold_words
			print >> out, "Test: " + test_words
		return

	compare_trees(gold_tree, test_tree, out_dict, error_counts, classify)


def main(args, classify):
	init.argcheck(args, 4, 4, 'Identify errors in parser output', '<gold> <test> <prefix_for_output_files>')

	# Output setup
	out_dict = {
		'out': sys.stdout,
		'err': sys.stderr,
		'gold_trees': sys.stdout,
		'test_trees': sys.stdout,
		'error_counts': sys.stdout
	}
	prefix = args[3]
	out_dict['out'] = open(prefix + '.out', 'w')
	out_dict['err'] = open(prefix + '.log', 'w')
	out_dict['gold_trees'] = open(prefix + '.gold_trees', 'w')
	out_dict['test_trees'] = open(prefix + '.test_trees', 'w')
	out_dict['error_counts'] = open(prefix + '.error_counts', 'w')
	out_dict['init_errors'] = open(prefix + '.init_errors', 'w')
	init.header(args, out_dict.values())

	# Classification
	print >> out_dict['out'], "Printing tree transformations"
	print >> out_dict['err'], "Printing tree transformations"
	gold_in = open(args[1])
	test_in = sys.stdin if args[2] == '-' else open(args[2])
	sent_no = 0
	error_counts = defaultdict(lambda: [])
	while True:
		sent_no += 1
		gold_text = gold_in.readline()
		test_text = test_in.readline()
		if gold_text == '' and test_text == '':
			print >> out_dict['err'], "End of both input files"
			break
		elif gold_text == '':
			print >> out_dict['err'], "End of gold input"
			break
		elif test_text == '':
			print >> out_dict['err'], "End of test input"
			break

		print >> out_dict['out'], "Sentence {}:".format(sent_no)
		print >> out_dict['err'], "Sentence {}:".format(sent_no)
		print >> out_dict['init_errors'], "Sentence {}:".format(sent_no)
		compare(gold_text.strip(), test_text.strip(), out_dict, error_counts, classify)
		print >> out_dict['init_errors'], "\n"

	# Results
	counts_to_print = []
	for error in error_counts:
		if error == 'UNSET init':
			continue
		counts_to_print.append((len(error_counts[error]), sum(error_counts[error]), error))
	counts_to_print.sort(reverse=True)
	for error in counts_to_print:
		print >> out_dict['error_counts'], "{} {} {}".format(*error)


if __name__ == '__main__':
	from classify_english import classify
	main(sys.argv, classify)

#!/usr/bin/env python

import sys
import ptb, util

def value_present(info, fields, values):
	for field in fields:
		if field in info:
			for value in values:
				if value in info[field]:
					return True
	return False

phrase_labels = "S SBAR SBARQ SINV SQ ADJP ADVP CONJP FRAG INTJ LST NAC NP NX PP PRN PRT QP RRC UCP VP WHADJP WHAVP WHNP WHPP X".split()
seen_movers = set()
def classify(info):
	global seen_mmovers
	if 'mover info' in info:
		for mover in info['mover info']:
			if mover in seen_movers:
				info["double move"] = True
			seen_movers.add(mover)
	info['classified_type'] = 'UNSET ' + info['type']
	if value_present(info, ['type'], ['move']):
		if 'start left siblings' in info:
			if len(info['start left siblings']) > 0 and info['start left siblings'][-1] == 'CC':
				info['classified_type'] = "Co-ordination"
				return
		if 'start right siblings' in info:
			if len(info['start right siblings']) > 0 and info['start right siblings'][0] == 'CC':
				info['classified_type'] = "Co-ordination"
				return
		if 'end left siblings' in info:
			if len(info['end left siblings']) > 0 and info['end left siblings'][-1] == 'CC':
				info['classified_type'] = "Co-ordination"
				return
		if 'end right siblings' in info:
			if len(info['end right siblings']) > 0 and info['end right siblings'][0] == 'CC':
				info['classified_type'] = "Co-ordination"
				return
		if 'movers' in info:
			if len(info['movers']) > 0 and (info['movers'][-1] == 'CC' or info['movers'][0] == 'CC'):
				info['classified_type'] = "Co-ordination"
				return

		# multi case info is not actually used, but may be useful
		multi_case = False
		if 'movers' in info:
			if len(info['movers']) > 1:
				multi_case = True
				for label in info['movers']:
					if label not in phrase_labels:
						multi_case = False
						break
		if value_present(info, ['movers'], ['PP']):
			info['classified_type'] = "PP Attachment"
			return
		if value_present(info, ['movers'], ['NP']):
			info['classified_type'] = "NP Attachment"
			return
		if value_present(info, ['movers'], ['VP']):
			info['classified_type'] = "VP Attachment"
			return
		if value_present(info, ['movers'], ['S', 'SINV', 'SBAR']):
			info['classified_type'] = "Clause Attachment"
			return
		if value_present(info, ['movers'], ['RB', 'ADVP', 'ADJP']):
			info['classified_type'] = "Modifier Attachment"
			return

		if value_present(info, ['old_parent'], ['NP', 'QP']):
			if value_present(info, ['new_parent'], ['NP', 'QP']):
				info['classified_type'] = "NP Internal Structure"
				return

	if 'over_word' in info:
		info['classified_type'] = "Single Word Phrase"
		return

	if value_present(info, ['type'], ['relabel']):
		info['classified_type'] = "Wrong label, right span"
		return

	if info['type'] == 'add':
		if 'subtrees' in info and len(info['subtrees']) == 1:
			if info['subtrees'][0] == info['label']:
				info['classified_type'] = "XoverX Unary"
				return
			info['classified_type'] = "Unary"
			return

	if info['type'] == 'remove':
		if 'family' in info and len(info['family']) == 1:
			if info['parent'] == info['label']:
				info['classified_type'] = "XoverX Unary"
				return
			info['classified_type'] = "Unary"
			return
		if 'subtrees' in info and len(info['subtrees']) == 1:
			info['classified_type'] = "Unary"
			return

	if value_present(info, ['label'], ['UCP']):
		info['classified_type'] = "Co-ordination"
		return

	if 'right siblings' in info:
		if len(info['right siblings']) > 0 and info['right siblings'][0] == 'CC':
			info['classified_type'] = "Co-ordination"
			return

	if 'subtrees' in info and 'PP' in info['subtrees'][1:]:
		info['classified_type'] = "PP Attachment"
		return

	if 'subtrees' in info:
		if 'S' in info['subtrees'][1:]:
			info['classified_type'] = "Clause Attachment"
			return
		if 'SBAR' in info['subtrees'][1:]:
			info['classified_type'] = "Clause Attachment"
			return
		if 'SINV' in info['subtrees'][1:]:
			info['classified_type'] = "Clause Attachment"
			return
	
	if value_present(info, ['parent'], ['NP']):
		all_words = True
		if 'subtrees' in info:
			# None of the subtrees are internal nodes
			for label in info['subtrees']:
				if label in phrase_labels:
					all_words = False
					break
			if all_words:
				info['classified_type'] = "NP Internal Structure"
				return

	if value_present(info, ['label'], ['ADVP', 'ADJP']):
		info['classified_type'] = "Modifier Attachment"
		return

	if 'subtrees' in info:
		if 'ADVP' in info['subtrees'][1:] or 'ADJP' in info['subtrees'][1:]:
			info['classified_type'] = "Modifier Attachment"
			return

	if 'label' in info:
		label = info['label']
		if 'subtrees' in info:
			all_same = True
			for slabel in info['subtrees']:
				if slabel != label:
					all_same = False
					break
			if all_same:
				if label == 'NP':
					info['classified_type'] = "NP Internal Structure"
					return
				else:
					info['classified_type'] = "Co-ordination"
					return

def gen_different_label_successor(ctree, eerror, merror):
	tree = ctree.clone()
	info = {'type': 'relabel'}
	# find the extra span
	spans = tree.get_spans(eerror[1][0], eerror[1][1])
	extra_span = None
	for span in spans:
		if eerror[2] == span[2].label:
			extra_span = span[2]
	assert extra_span is not None

	# relabel
	extra_span.label = merror[2]
	info['subtrees'] = [subtree.label for subtree in extra_span.subtrees]
	info['parent'] = extra_span.parent.label
	info['span'] = extra_span.span
	info['family'] = [subtree.label for subtree in extra_span.parent.subtrees]
	if len(extra_span.subtrees) == 1 and extra_span.subtrees[0].word is not None:
		info['over_word'] = True
	return (True, tree, info)

def gen_missing_successor(ctree, error):
	tree = ctree.clone()
	info = {'type': 'add'}
	# find the nodes that should be within this missing span

	# first, find the spans the have matching start or end
	starts = tree.get_spans(start=error[1][0])
	ends = tree.get_spans(end=error[1][1])

	# get the start nodes that are within the missing span, not ROOT, and as large as possible
	first = None
	for start in starts:
		if start[1] <= error[1][1]:
			if first is None or start[1] > first[1] and start[2].parent is not None:
				first = start
	firsts = [start[2] for start in starts if start[1] == first[1] and start[2].parent is not None]

	# get the end nodes that are within the missing span, not ROOT, and as large as possible
	last = None
	for end in ends:
		if end[0] >= error[1][0]:
			if last is None or end[0] < last[0] and end[2].parent is not None:
				last = end
	lasts = [end[2] for end in ends if end[0] == last[0] and end[2].parent is not None]

	# find a pair that are within the same node
	match = None
	for first in firsts:
		for last in lasts:
			if first.parent == last.parent:
				match = (first, last)
				break
	assert match is not None

	# create the missing bracket
	first, last = match
	parent = last.parent
	nnode = ptb.PTB_Tree()
	nnode.span = (error[1][0], error[1][1])
	nnode.label = error[2]
	nnode.parent = parent
	# move the subtrees
	for i in xrange(len(parent.subtrees)):
		if parent.subtrees[i] == first:
			while parent.subtrees[i] != last:
				nnode.subtrees.append(parent.subtrees.pop(i))
				nnode.subtrees[-1].parent = nnode
			nnode.subtrees.append(parent.subtrees.pop(i))
			nnode.subtrees[-1].parent = nnode
			parent.subtrees.insert(i, nnode)
			break
	info['label'] = nnode.label
	info['span'] = nnode.span
	info['subtrees'] = [subtree.label for subtree in nnode.subtrees]
	info['parent'] = nnode.parent.label
	info['family'] = [subtree.label for subtree in nnode.parent.subtrees]
	if len(nnode.subtrees) == 1 and nnode.subtrees[0].word is not None:
		info['over_word'] = True
	info['left siblings'] = []
	info['right siblings'] = []
	cur = []
	for span in nnode.parent.subtrees:
		if span == nnode:
			info['left siblings'] = cur
			cur = []
		else:
			cur.append(span.label)
	info['right siblings'] = cur
	return (True, tree, info)

def gen_extra_successor(ctree, error):
	tree = ctree.clone()
	info = {'type': 'remove'}
	# find the extra span
	spans = tree.get_spans(error[1][0], error[1][1])
	extra_span = None
	for span in spans:
		if error[2] == span[2].label:
			extra_span = span[2]
	assert extra_span is not None
	info['label'] = error[2]
	info['span'] = error[1]
	info['subtrees'] = [subtree.label for subtree in extra_span.subtrees]
	info['parent'] = extra_span.parent.label
	info['family'] = [subtree.label for subtree in extra_span.parent.subtrees]
	info['left siblings'] = []
	info['right siblings'] = []
	cur = []
	for span in extra_span.parent.subtrees:
		if span == extra_span:
			info['left siblings'] = cur
			cur = []
		else:
			cur.append(span.label)
	info['right siblings'] = cur

	# remove the span
	parent = extra_span.parent
	for i in xrange(len(parent.subtrees)):
		if parent.subtrees[i] == extra_span:
			parent.subtrees.pop(i)
			for subtree in extra_span.subtrees[::-1]:
				subtree.parent = parent
				parent.subtrees.insert(i, subtree)
			break
	if len(extra_span.subtrees) == 1 and extra_span.subtrees[0].word is not None:
		info['over_word'] = True
	return (True, tree, info)

def gen_move_successors(pos, starting, ctree, source_span, left, right, cerrors):
	new_sibling = None
	if starting:
		new_sibling = ctree.get_lowest_span(start=pos, end=pos+1)
	else:
		new_sibling = ctree.get_lowest_span(start=pos-1, end=pos)
	steps = 0
	# if pos == left, then only consider moving up
	left_pos = source_span.subtrees[left].span[0]
	if starting and pos == left_pos:
		while new_sibling != source_span:
			new_sibling = new_sibling.parent
			steps += 1
	# if pos == right, then only consider moving up
	right_pos = source_span.subtrees[right].span[1]
	if (not starting) and pos == right_pos:
		while new_sibling != source_span:
			new_sibling = new_sibling.parent
			steps += 1
	while new_sibling is not None:
		if new_sibling.parent is None:
			break
		if new_sibling.parent == source_span:
			break
		# Clone the tree and find the equivalent locations
		tree = ctree.clone()
		info = {'type': 'move'}
		spans = tree.get_spans(source_span.span[0], source_span.span[1])
		old_parent = None
		for span in spans:
			if source_span.label == span[2].label:
				if len(span[2].subtrees) == len(source_span.subtrees):
					old_parent = span[2]
		new_parent = None
		if starting:
			new_parent = tree.get_lowest_span(start=pos, end=pos+1)
		else:
			new_parent = tree.get_lowest_span(start=pos-1, end=pos)
		for i in xrange(steps + 1):
			new_parent = new_parent.parent
		assert new_parent is not None and old_parent is not None

		# Only move in to things that are extra (we don't want to create errors)
		use = False
		if cerrors.is_extra(new_parent):
			use = True
		else:
			if starting:
				if left == 0 and pos == left_pos:
					use = True
			else:
				if right == len(source_span.subtrees) - 1 and pos == right_pos:
					use = True

		if use:
			info['old_parent'] = old_parent.label
			info['new_parent'] = new_parent.label
			info['movers'] = []
			info['mover info'] = []
			info['new_family'] = [subtree.label for subtree in new_parent.subtrees]
			info['start left siblings'] = [node.label for node in old_parent.subtrees[:left]]
			info['start right siblings'] = [node.label for node in old_parent.subtrees[right+1:]]

			# Move [left, right] from old_parent to new_parent
			insertion_point = 0
			for subtree in new_parent.subtrees:
				if subtree.span[0] >= old_parent.subtrees[left].span[0]:
					break
				insertion_point += 1
			info['end left siblings'] = [node.label for node in new_parent.subtrees[:insertion_point]]
			info['end right siblings'] = [node.label for node in new_parent.subtrees[insertion_point:]]
			moved = set()
			for i in xrange(left, right + 1):
				mover = old_parent.subtrees.pop(left)
				moved.add(mover)
				new_parent.subtrees.insert(insertion_point, mover)
				mover.parent = new_parent
				insertion_point += 1
				info['movers'].append(mover.label)
				info['mover info'].append((mover.label, mover.span))
			info['old_family'] = [subtree.label for subtree in old_parent.subtrees]
			if len(old_parent.subtrees) == 0:
				while len(old_parent.subtrees) == 0 and old_parent.parent is not None:
					old_parent.parent.subtrees.remove(old_parent)
					old_parent = old_parent.parent
			if len(old_parent.subtrees) == 1:
				if old_parent.label == old_parent.subtrees[0].label:
					if new_parent == old_parent.subtrees[0]:
						new_parent = old_parent
					old_parent.subtrees = old_parent.subtrees[0].subtrees
					for subtree in old_parent.subtrees:
						subtree.parent = old_parent
			tree.calculate_spans()
			
			# if the thing(s) that moved and one other thing should all be under a
			# bracket that is missing, and this would not create a unary, add it
			nspan = None
			move_span = [1000, -1]
			for node in moved:
				if node.span[0] < move_span[0]:
					move_span[0] = node.span[0]
				if node.span[1] > move_span[1]:
					move_span[1] = node.span[1]
			cur = None
			movers_seen = False
			for node in new_parent.subtrees:
				if node not in moved:
					cur = node
					if movers_seen:
						nspan = (move_span[0], cur.span[1])
						break
				else:
					movers_seen = True
					if cur is not None:
						nspan = (cur.span[0], move_span[1])
						break
			to_fix = []
			for error in cerrors.missing + cerrors.crossing:
				if error[1] == nspan and error[0] != 'extra':
					to_fix.append(error)
			nnode = ptb.PTB_Tree()
			if len(to_fix) == 1:
				info['added and moved'] = True
				error = to_fix[0]
				first, last = None, None
				for node in new_parent.subtrees:
					if node.span[0] == nspan[0]:
						first = node
					if node.span[1] == nspan[1]:
						last = node
				if first is not None and last is not None:
					nnode.span = (error[1][0], error[1][1])
					nnode.label = error[2]
					nnode.parent = new_parent
					# move the subtrees
					for i in xrange(len(new_parent.subtrees)):
						if new_parent.subtrees[i] == first:
							while new_parent.subtrees[i] != last:
								mover = new_parent.subtrees.pop(i)
								nnode.subtrees.append(mover)
								mover.parent = nnode
							mover = new_parent.subtrees.pop(i)
							nnode.subtrees.append(mover)
							mover.parent = nnode
							new_parent.subtrees.insert(i, nnode)
							nnode.parent = new_parent
							break

			# return the modified tree
			yield (False, tree, info)
		new_sibling = new_sibling.parent
		steps += 1

def successors(ctree, cerrors, gold):
	# Change the label of a node
	for merror in cerrors.missing:
		for eerror in cerrors.extra:
			if merror[1] == eerror[1]:
				yield gen_different_label_successor(ctree, eerror, merror)

	# Add a node
	for error in cerrors.missing:
		yield gen_missing_successor(ctree, error)

	# Remove a node
	for error in cerrors.extra:
		yield gen_extra_successor(ctree, error)

	# Move nodes
	spans = ctree.get_spans()
	for source_span in spans:
		# Consider all continuous sets of children
		source_span = source_span[2]
		for left in xrange(len(source_span.subtrees)):
			for right in xrange(left, len(source_span.subtrees)):
				if left == 0 and right == len(source_span.subtrees) - 1:
					continue
				# If this series of nodes does not span the entire set of children
				if left != 0:
					# Consider moving down within this bracket
					pos = source_span.subtrees[left].span[0]
					for ans in gen_move_successors(pos, False, ctree, source_span, left, right, cerrors):
						yield ans
				if right != len(source_span.subtrees) - 1:
					# Consider moving down within this bracket
					pos = source_span.subtrees[right].span[1]
					for ans in gen_move_successors(pos, True, ctree, source_span, left, right, cerrors):
						yield ans
		
				# If source_span is extra
				if cerrors.is_extra(source_span):
					if left == 0:
						# Consider moving this set out to the left
						pos = source_span.subtrees[left].span[0]
						if pos > 0:
							for ans in gen_move_successors(pos, False, ctree, source_span, left, right, cerrors):
								yield ans
						# Consider moving this set of spans up
						for ans in gen_move_successors(pos, True, ctree, source_span, left, right, cerrors):
							yield ans
					elif right == len(source_span.subtrees) - 1:
						# Consider moving this set out to the right
						pos = source_span.subtrees[right].span[1]
						if pos < ctree.span[1]:
							for ans in gen_move_successors(pos, True, ctree, source_span, left, right, cerrors):
								yield ans
						# Consider moving this set of spans up
						for ans in gen_move_successors(pos, False, ctree, source_span, left, right, cerrors):
							yield ans

def greedy_search(gold, test):
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
		cerrors = ctree.get_errors(gold)
		if len(cerrors) == 0:
			final = cur
			break

		best = None
		for fixes, ntree, info in successors(ctree, cerrors, gold):
			if not ntree.check_consistency():
				print "Inconsistent tree!"
				print ntree
				sys.exit(0)
			nerrors = ntree.get_errors(gold)
			change = len(cerrors) - len(nerrors)
			if change < 0:
				continue
			if best is None or change > best[2]:
				best = (ntree, info, change)
		cur = best
		iters += 1
	
	global seen_movers
	seen_movers = set()
	for step in path:
		classify(step[1])
	
	return (0, iters), path


#####################################################################
#
# Main (and related functions)
#
#####################################################################

def mprint(text, out_dict, out_name):
	if 'all' in out_name:
		for key in out_dict:
			print >> out_dict[key], text
	else:
		if type(out_name) != type([]):
			out_name = [out_name]
		for name in out_name:
			print >> out_dict[name], text

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:"
		print "   %s <gold> <test> [<output_prefix> stdout by default]" % sys.argv[0]
		print "Running doctest"
		import doctest
		doctest.testmod()
		sys.exit(0)

	out_dict = {
		'out': sys.stdout,
		'summary': sys.stderr,
		'err': sys.stderr,
		'gold_trees': sys.stdout,
		'test_trees': sys.stdout
	}
	if len(sys.argv) == 4:
		out_dict['out'] = open(sys.argv[3] + '.out', 'w')
		out_dict['err'] = open(sys.argv[3] + '.log', 'w')
		out_dict['summary'] = open(sys.argv[3] + '.summary', 'w')
		out_dict['gold_trees'] = open(sys.argv[3] + '.gold_trees', 'w')
		out_dict['test_trees'] = open(sys.argv[3] + '.test_trees', 'w')

	mprint("Printing tree transformations", out_dict, ['out', 'err'])
	gold_in = open(sys.argv[1])
	test_in = open(sys.argv[2])
	sent_no = 0
	while True:
		sent_no += 1
		gold_text = gold_in.readline()
		test_text = test_in.readline()
		if gold_text == '' and test_text == '':
			mprint("End of both input files", out_dict, 'err')
			break
		elif gold_text == '':
			mprint("End of gold input", out_dict, 'err')
			break
		elif test_text == '':
			mprint("End of test input", out_dict, 'err')
			break

		mprint("Sentence %d:" % sent_no, out_dict, ['out', 'err','summary'])

		gold_text = gold_text.strip()
		test_text = test_text.strip()
		if len(gold_text) == 0:
			mprint("No gold tree", out_dict, ['out', 'err','summary'])
			continue
		elif len(test_text) == 0:
			mprint("Not parsed", out_dict, ['out', 'err','summary'])
			continue

		gold_complete_tree = ptb.PTB_Tree()
		gold_complete_tree.set_by_text(gold_text)
		gold_notrace_tree = ptb.remove_traces(gold_complete_tree)
		gold_nofunc_tree = ptb.remove_function_tags(gold_notrace_tree)
		gold_tree = ptb.apply_collins_rules(gold_complete_tree)
		if gold_tree is None:
			mprint("Empty gold tree", out_dict, ['out', 'err','summary'])
			mprint(gold_complete_tree.__repr__(), out_dict, ['out', 'err'])
			mprint(gold_tree.__repr__(), out_dict, ['out', 'err'])
			continue

		test_complete_tree = ptb.PTB_Tree()
		test_complete_tree.set_by_text(test_text)
		test_notrace_tree = ptb.remove_traces(test_complete_tree)
		test_nofunc_tree = ptb.remove_function_tags(test_notrace_tree)
		test_tree = ptb.apply_collins_rules(test_complete_tree)
		if test_tree is None:
			mprint("Empty test tree", out_dict, ['out', 'err','summary'])
			mprint(test_complete_tree.__repr__(), out_dict, ['out', 'err'])
			mprint(test_tree.__repr__(), out_dict, ['out', 'err'])
			continue

		gold_words = gold_tree.word_yield()
		test_words = test_tree.word_yield()
		if len(test_words.split()) != len(gold_words.split()):
			mprint("Sentence lengths do not match...", out_dict, ['out', 'err','summary'])
			mprint("Gold: " + gold_words.__repr__(), out_dict, ['out', 'err'])
			mprint("Test: " + test_words.__repr__(), out_dict, ['out', 'err'])

		init_errors = test_tree.get_errors(gold_tree)
		error_count = len(init_errors)
		mprint("%d Initial errors" % error_count, out_dict, 'out')
		iters, path = greedy_search(gold_tree, test_tree)
		mprint("%d on fringe, %d iterations" % iters, out_dict, 'out')
		if path is not None:
			mprint(test_tree.__repr__(), out_dict, 'test_trees')
			mprint(gold_tree.__repr__(), out_dict, 'gold_trees')
			for tree in path[1:]:
				mprint(str(tree[2]) + " Error:" + tree[1]['classified_type'], out_dict, ['out','summary'])

			if len(path) > 1:
				for tree in path:
					mprint("Step:" + tree[1]['classified_type'], out_dict, 'out')
					mprint(tree[1].__repr__(), out_dict, 'out')
					mprint(tree[0].colour_repr(gold=gold_tree).strip(), out_dict, 'out')
		else:
			mprint("no path found", out_dict, 'out')

		mprint("", out_dict, ['out', 'err','summary'])


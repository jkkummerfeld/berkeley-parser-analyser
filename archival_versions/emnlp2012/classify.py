#!/usr/bin/env python

import sys
import ptb, error_tree, repair_tree, bracket_errors, error_group
import s_single_word, s_unary, s_attachment

# Other ideas:
# NP internal structure:
#  - a collection of extra NP brackets inside an NP, with only NPs below
#  - a collection of missing NP brackets inside an NP, with only NPs below

def check_for_matching_errors(ungrouped, group, gold, test):
	spans, span_set = test.get_spans()
	to_remove = []
	for merror in ungrouped:
		if merror.missing:
			span = merror.node.span
			if span in span_set:
				if merror.node.label in span_set[span]:
					trees = span_set[span][merror.node.label]
					found = False
					for tree in trees:
						if tree.extra:
							for eerror in ungrouped:
								if eerror.extra and eerror.node == tree.basis_tree:
									to_remove.append(merror)
									to_remove.append(eerror)
									tree.extra = False
									found = True
									break
						if found:
							break
	for error in to_remove:
		ungrouped.remove(error)
		group.errors.append(error)
	return test

def detect_error_types(error_set, gold_tree, test_tree):
	init_error_count = len(error_set['miss']) + len(error_set['extra'])
	ungrouped = []
	for etype in error_set:
		for error in error_set[etype]:
			ungrouped.append(error)
	bracket_errors.sort_by_depth(ungrouped)
	init_ungrouped_length = len(ungrouped)
	assert init_ungrouped_length == init_error_count

	grouped = []
	mutable_test = test_tree.copy()

	# iterate through the errors until there is no change after an iteration
	# Note - order of these is intentional
	aggregators = [
		s_unary.unary_error,
		s_single_word.single_word_error,
		s_attachment.attachment_error,
	]
	changed = True
	while changed:
		changed = False
###		print mutable_test.colour_repr()
###		for error in ungrouped:
###			print error
###		print
		for func in aggregators:
			plen = len(ungrouped), len(grouped)
			tchanged, mutable_test = func(ungrouped, grouped, gold_tree, mutable_test)
			if tchanged:
				mutable_test = check_for_matching_errors(ungrouped, grouped[-1], gold_tree, mutable_test)
				changed = True

	remaining_errors = bracket_errors.get_errors(gold_tree, mutable_test)
	return grouped, mutable_test, remaining_errors, ungrouped

def aggregate_error_types(groups):
# Further grouping the errors detected in the function above
	counts = {'new Other': [0, 0, []]}
	print "Aggregated errors"
	for group in groups:
		if group.classification is None:
			group.determine_type()
		if group.classification not in counts:
			counts[group.classification] = [0, 0, []]
		counts[group.classification][0] += 1
		counts[group.classification][1] += len(group.errors)
		counts[group.classification][2].append(group)
		if 'new' not in group.classification:
			counts['new Other'][0] += 1
			counts['new Other'][1] += len(group.errors)
			counts['new Other'][2].append(group)

	stats = []
	for count in counts:
		stats.append((counts[count][0], count))
	stats.sort()
	for stat in stats:
		print 'Aggregated Errors:',
		print stat[0],
		print stat[1], 
		print ' | ',
		print counts[stat[1]][1] / float(stat[0]),
		print counts[stat[1]][1]

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:\n%s <gold> <test>" % sys.argv[0]
		print "The files should contain one parse per line, with a 1-1 mapping (use blank lines where there is a missing parse)."
		print "Running doctest"
		import doctest
		doctest.testmod()
	else:
		gold_in = open(sys.argv[1])
		test_in = open(sys.argv[2])
		VERBOSE = len(sys.argv) > 3 and ('-v' in sys.argv[3] or '-V' in sys.argv[3])
		error_groups = []
		while True:
			gold_text = gold_in.readline()
			test_text = test_in.readline()
			if gold_text == '' or test_text == '':
				break

			gold_text = gold_text.strip()
			test_text = test_text.strip()
			if len(gold_text) == 0 or len(test_text) == 0:
				continue

			if VERBOSE:
				print gold_text
			tree = ptb.PTB_Tree()
			tree.set_by_text(gold_text)
			if VERBOSE:
				print tree
			simple_tree = ptb.apply_collins_rules(tree)
			if VERBOSE:
				print simple_tree
			if simple_tree is None:
				continue
			gold_tree = error_tree.Error_Tree()
			gold_tree.set_by_ptb(simple_tree, tree)
			if VERBOSE:
				print gold_tree

			if VERBOSE:
				print test_text
			tree = ptb.PTB_Tree()
			tree.set_by_text(test_text)
			if VERBOSE:
				print tree
			simple_tree = ptb.apply_collins_rules(tree)
			if VERBOSE:
				print simple_tree
			test_tree = error_tree.Error_Tree()
			test_tree.set_by_ptb(simple_tree, tree)
			if VERBOSE:
				print test_tree

			gold_words = gold_tree.word_yield()
			test_words = test_tree.word_yield()
			if len(test_words.split()) != len(gold_words.split()):
				print "Sentence lengths do not maych..."
				print "Gold:", gold_words
				print "Test:", test_words

			error_set = bracket_errors.get_errors(gold_tree, test_tree)[0]
			missing = bracket_errors.get_missing_errors(error_set, test_tree)
			print test_tree.colour_repr(missing=missing).strip()
			if len(error_set['miss']) > 0 or len(error_set['extra']) > 0:
				print 'initial errors:', len(error_set['miss']), len(error_set['extra'])
				aggregated_errors = detect_error_types(error_set, gold_tree, test_tree)
				for group in aggregated_errors[0]:
					group.determine_type()
					print 'Class:', group.classification
					print 'Fixes:',
					for error in group.errors:
						print error
					error_groups.append(group)
				error_set = bracket_errors.get_errors(gold_tree, aggregated_errors[1])[0]
				missing = bracket_errors.get_missing_errors(error_set, aggregated_errors[1])
				print 'remaining errors:', len(error_set['miss']), len(error_set['extra'])
				for etype in error_set:
					for error in error_set[etype]:
						print "Error:", etype, error.node.label
						group = error_group.Error_Group()
						group.fields = {}
					 	group.fields['old desc'] = "%s %s" % (etype, error.node.label)
						group.desc = group.fields['old desc']
						group.errors.append(error)
						error_groups.append(group)
				print aggregated_errors[1].colour_repr(missing=missing).strip()
			print
		aggregate_error_types(error_groups)

# Tricky sentence:
# The move leaves United Illuminating Co. and Northeast Utilities...
#
# TODO: It would be interesting to have a list of the phrases that form errors,
# in particular the missing constituents.  The question is, why is this a
# constituent?  Is it something you need world knowledge for?

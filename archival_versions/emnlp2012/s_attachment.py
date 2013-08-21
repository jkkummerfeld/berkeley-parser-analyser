#!/usr/bin/env python

import sys
import ptb, error_tree, repair_tree, bracket_errors, error_group, classify

###############################################################################
#
# The first set of functions fix specific types of errors, often by moving bits
# of the tree around.
#
###############################################################################

global_gold = None

def missing_with_matching_extra(error, test_tree, to_group, to_add, left, right, parent, ungrouped):
	'''Missing, then if there is an equivalent extra above it, then the next
	chunk of sentence is attaching too low.  This one attachment mistake could
	actually be causing a stack of errors, so we pull out the incorrectly
	attached bits and see what else is fixed.'''
	if left == 0:
		# our missing bracket covers nodes starting on the left
		end = error.node.span[1]

		# take the rest out, and move them up to be beneath the next layer that is
		# correct (not extra)
		to_group.append(error)
		eerror = bracket_errors.get_extra_error(ungrouped, parent)
		if eerror is None:
			print "Couldn't find match!"
			for terror in ungrouped:
				print terror
		else:
			to_group.append(eerror)
		parent.extra = False
		clevel = parent
		parent = parent.parent
		prev = clevel
###		while parent.extra and parent.parent is not None:
###			# check for crossing spans
###			for oerror in ungrouped:
###				if oerror.missing and oerror != error:
###					if parent.parent.span[0] < oerror.node.span[0] < parent.parent.span[1]:
###						break
###					if parent.parent.span[0] < oerror.node.span[1] < parent.parent.span[1]:
###						break
###			if clevel.span[1] < parent.span[1]:
###				break
###			prev = parent
###			parent = parent.parent

		# pull out the node(s) down the bottom on the right
		# move them up to the discovered level
		group_fields = {}
		group_fields['type'] = 'attachment'
		group_fields['height'] = 'too low'
		group_fields['from parent'] = clevel.label
		group_fields['from left siblings'] = ''
		for child in parent.subtrees:
			if child == prev:
				break
			group_fields['from left siblings'] += ' ' + child.label
		group_fields['to parent'] = parent.label
		group_desc = 'attachment too_low %s_instead_of_%s' % (clevel.label, parent.label)
		addendum = []
		for pos in xrange(len(parent.subtrees)):
			if clevel.span[1] <= parent.subtrees[pos].span[1]:
				if clevel.span[1] == parent.subtrees[pos].span[1]:
					pos = pos + 1
				while len(clevel.subtrees) > right + 1:
					node = clevel.subtrees.pop()
					parent.subtrees.insert(pos, node)
					node.parent = parent
					addendum.insert(0, node.label)
				break
		group_fields['nodes moving'] = ' '.join(addendum)
		group_desc += ' ' + '_'.join(addendum)
		test_tree.update_span()
		group_fields['ID'] = '|mwme1'
		group_desc += ' |mwme1'
		group_fields['old desc'] = group_desc
		test_tree.check_consistency()
		return group_fields, test_tree
	elif right == len(parent.subtrees) - 1:
		# our missing bracket is to the right

		# if the extra is an NP and everthing under it is a word, NP internal structure
		if parent.label == 'NP':
			if parent.parent is not None:
				if  parent.parent.label == 'NP' and not parent.parent.extra:
					all_words = True
					for subtree in parent.subtrees:
						if subtree.word is None:
							all_words = False
							break
					if all_words:
						group_fields = {}
						group_fields['type'] = 'NP structure'
						eerror = bracket_errors.get_extra_error(ungrouped, parent)
						for merror in ungrouped:
							if merror.node.span[0] >= parent.span[0]:
								if merror.node.span[1] <= parent.span[1]:
									if merror.missing:
										to_group.append(merror)
										repair_tree.repair_missing_node(merror, test_tree)
						to_group.append(eerror)
						repair_tree.repair_extra_node(eerror, test_tree)
						test_tree.update_span()
						group_fields['ID'] = '|mwme2'
						group_fields['old desc'] = 'missing error NP structure |mwme2'
						return group_fields, test_tree

		# no other missing or extra brackets under this extra span
		# attachment, give info
		no_others = True
###		print "Available:"
###		for terror in ungrouped:
###			print terror
		eerror = bracket_errors.get_extra_error(ungrouped, parent)
		for oerror in ungrouped:
			if oerror.node.span[0] >= parent.span[0]:
				if oerror.node.span[1] <= parent.span[1]:
					if oerror != error and oerror != eerror:
						no_others = False
						break
		if no_others:
			group_fields = {}
			group_fields['type'] = 'extra under bracket on right'
			group_fields['parent'] = parent.label
			group_fields['extra nodes'] = ''
			group_fields['children'] = ''
			for subtree in parent.subtrees:
				if subtree.span[0] < error.node.span[0]:
					group_fields['extra nodes'] += ' ' + subtree.label
				elif subtree.span[1] < error.node.span[1]:
					group_fields['children'] += ' ' + subtree.label
			group_fields['ID'] = '|mwme3'
			group_fields['old desc'] = 'extra under bracket on right |mwme3'
			if error is not None:
				to_group.append(error)
				repair_tree.repair_missing_node(error, test_tree)
			if eerror is not None:
				to_group.append(eerror)
				repair_tree.repair_extra_node(eerror, test_tree)
			test_tree.update_span()
			return group_fields, test_tree
	else:
		# our missing bracket is somewhere in the middle
		pass
	return None, test_tree

def missing_with_nothing_nearby(error, test_tree, to_group, clevel, left, right, ungrouped):
	'''Missing, with no crossing or other bracket error directly above, so
	something that should be in this bracket attached too high.'''
	if left == right:
		# This is actually a unary case
		return None, test_tree
	group_fields = {}
	group_fields['type'] = 'missing'
	group_fields['parent'] = clevel.label
	group_fields['left siblings'] = []
	group_fields['children'] = []
	group_fields['right siblings'] = []
	group_desc = 'attachment too_high %s_instead_of_%s' % (clevel.label, error.node.label)
	for i in xrange(len(clevel.subtrees)):
		if i < left:
			group_fields['left siblings'].append(clevel.subtrees[i].label)
		elif i > right:
			group_fields['right siblings'].append(clevel.subtrees[i].label)
		else:
			group_desc += ' ' + clevel.subtrees[i].label
			group_fields['children'].append(clevel.subtrees[i].label)
	group_fields['left siblings'] = ' '.join(group_fields['left siblings'])
	group_fields['right siblings'] = ' '.join(group_fields['right siblings'])
	group_fields['children not first'] = ' '.join(group_fields['children'][1:])
	group_fields['children'] = ' '.join(group_fields['children'])
	group_desc += ' ' + error.node.word_yield()
	group_fields['new spans'] = ''
	for merror in ungrouped:
		if merror.missing and error.node.span == merror.node.span:
			group_fields['new spans'] += ' ' + merror.node.label
			to_group.append(merror)
			repair_tree.repair_missing_node(merror, test_tree)
	group_fields['ID'] = 'mwnn1'
	group_desc += ' |mwnn1'
	group_fields['old desc'] = group_desc
	return group_fields, test_tree

def extra_crossing_ending(error, test_tree, to_group, ending, ungrouped, ctree):
	'''Extra, then if there is a crossing bracket that ends in the middle of
	here, the other thing under this bracket is attaching too low.  This could
	explain a bunch of other errors.  In particular, consider if the wrongly
	attached thing was collapsed to 0, what would that fix (note that the extra
	bracket may still be extra at this point, or may now be equivalent to a
	msising bracket).'''
###	print error
	# work out what needs to move
	end = ending.keys()[0]
	crossing_errors = ending[end]
###	for cerror in crossing_errors:
###		print cerror

	# Check the case of a matching missing bracket
###	print error
###	print ending
	if len(ending[end]) == 1:
		for merror in ungrouped:
			if merror.missing and merror.node.label == error.node.label:
				if merror.node.span[1] == error.node.span[1]:
					if ending[end][0].node.span[0] == merror.node.span[0]:
						# the other things should be moving under here!
###						print merror
###						print error
						moving = []
						target = bracket_errors.get_extra_tree(error, test_tree)
						mspan = merror.node.span
						cend = target.span[0]
						while cend > mspan[0]:
							brac = test_tree
							done = False
							while not done:
								for subtree in brac.subtrees:
									if cend == subtree.span[1] and subtree.span[0] >= mspan[0]:
										moving.append(subtree)
										done = True
										cend = subtree.span[0]
										break
									if subtree.span[0] < cend <= subtree.span[1]:
										brac = subtree
										break
###						print "Moving"
###						for node in moving:
###							print node
###						print "To:"
###						print target
						# move them across
						group_fields = {}
						group_fields['type'] = 'attachment'
						group_fields['height'] = 'incorrect'
						group_fields['from parents'] = ''
						for node in moving:
							group_fields['from parents'] += ' ' + node.parent.label
						addendum = []
						group_desc = 'attachment incorrect %s_instead_of_%s' % (moving[0].parent.label, target.label)
						group_fields['to parent'] = target.label
						single_child_parents = []
						for node in moving:
							parent = node.parent
							parent.subtrees.remove(node)
							# if the parent now has only one child, look into whether it should be deleted
							if len(parent.subtrees) == 1:
								if parent.label == parent.subtrees[0].label:
									single_child_parents.append(parent)
							target.subtrees.insert(0, node)
							node.parent = target
							addendum.insert(0, node.label)
						group_fields['nodes moving'] = ' '.join(addendum)
						group_desc += ' ' + '_'.join(addendum)
						test_tree.update_span()

						for parent in single_child_parents:
							if len(parent.subtrees) == 1:
								if parent.subtrees[0].extra and parent.label == parent.subtrees[0].label:
									eerror = bracket_errors.get_extra_error(ungrouped, parent.subtrees[0])
									repair_tree.repair_extra_node(eerror, test_tree)
									to_group.append(eerror)

						target.extra = False
						if error not in to_group:
							to_group.append(error)
						to_group.append(merror)
						group_desc += ' |ece2'
						group_fields['ID'] = 'ece2'
						group_fields['old desc'] = group_desc
						test_tree.check_consistency()
						return group_fields, test_tree

	# work out where it is going to move to
	# first find the longest crossing error
	longest_error = None
	for merror in crossing_errors:
		if longest_error is None or merror.node.span[0] < longest_error.node.span[0]:
			longest_error = merror
	end = longest_error.node.span[1]
###	print "getting movers from:", ctree
###	print "after:", end, ctree.span
	cend = end
	moving = []
	while cend < ctree.span[1]:
		brac = test_tree
		done = False
		while not done:
			for subtree in brac.subtrees:
				if cend == subtree.span[0] and subtree.span[0] <= ctree.span[1]:
					moving.append(subtree)
					done = True
					cend = subtree.span[1]
					break
				if subtree.span[0] <= cend < subtree.span[1]:
					brac = subtree
					break
###	print "Moving:"
###	for mover in moving:
###		print mover
	# then see how far up we can go to it
	parent = ctree
	while parent.span[1] == ctree.span[1]:
		if parent.span[0] <= longest_error.node.span[0]:
			break
		parent = parent.parent

###	print parent
	# move the things up to this level
	group_fields = {}
	group_fields['type'] = 'attachment'
	group_fields['height'] = 'too low'
	group_fields['from parent'] = ctree.label
	group_fields['to parent'] = parent.label
	group_fields['nodes moving'] = []
	group_desc = 'attachment too_low %s_instead_of_%s' % (ctree.label, parent.label)
	for pos in xrange(len(parent.subtrees)):
		if parent.subtrees[pos].span[1] == ctree.span[1]:
			for subtree in moving:
				subtree.parent.subtrees.remove(subtree)
				parent.subtrees.insert(pos + 1, subtree)
				pos += 1
				subtree.parent = parent
				group_desc += ' ' + subtree.label
				group_fields['nodes moving'].append(subtree.label)
			break
	group_fields['nodes moving'] = ' '.join(group_fields['nodes moving'])

	# if only one thing is left behind, and its parent is extra, fix that
	if len(ctree.subtrees) == 1:
		for pos in xrange(len(ctree.parent.subtrees)):
			if ctree.parent.subtrees[pos] == ctree:
				for subtree in ctree.subtrees[::-1]:
					ctree.parent.subtrees.insert(pos+1, subtree)
					subtree.parent = ctree.parent
				break
		ctree.parent.subtrees.remove(ctree)
		to_group.append(error)
	test_tree.update_span()

	# if possible, fix longest_error
	left, right = -1, -1
	for pos in xrange(len(parent.subtrees)):
		if longest_error.node.span[0] == parent.subtrees[pos].span[0]:
			left = pos
		if longest_error.node.span[1] == parent.subtrees[pos].span[1]:
			right = pos
	if -1 < left < right:
		repair_tree.repair_missing_node(longest_error, test_tree)
		to_group.append(longest_error)

	# other errors that are fixed as a side effect will be found by the cleanup stuff

	group_desc += ' |ece1'
	group_fields['ID'] = 'ece1'
	group_fields['old desc'] = group_desc
	return group_fields, test_tree

def extra_crossing_starting(error, test_tree, to_group, starting, ungrouped, ctree):
	'''Extra, then if there is a crossing bracket that starts here, and no
	crossing bracket that ends at the same spot, the other thing under this
	bracket has something that should have attached to it, but attached too high.
	Consider what would happen if it had attached here and see what other errors
	it fixes (ie this extra may now match with a missing bracket above)'''
	
	# find the longest crossing missing bracket that starts here
	start = starting.keys()[0]
	cend = ctree.span[1]
	crossing_errors = starting[start]
	longest_error = None
	text = error.node.word_yield()
	for merror in crossing_errors:
		if longest_error is None or longest_error.node.span[1] < merror.node.span[1]:
			longest_error = merror
	mspan = (cend, longest_error.node.span[1])

	# find all the parts that start in the missing bracket to be here
	moving = []
	while cend < mspan[1]:
		brac = test_tree
		done = False
		while not done:
			for subtree in brac.subtrees:
				if cend == subtree.span[0]:
					moving.append(subtree)
					done = True
					cend = subtree.span[1]
					break
				if subtree.span[0] < cend < subtree.span[1]:
					brac = subtree
					break
	# move them across
	group_fields = {}
	group_fields['type'] = 'attachment'
	group_fields['height'] = 'too high'
	group_fields['from parent'] = moving[0].parent.label
	group_fields['to parent'] = longest_error.node.label
	group_desc = 'attachment too_high %s_instead_of_%s' % (moving[0].parent.label, longest_error.node.label)
	addendum = []
	target = ctree
	if ctree.subtrees[-1].extra:
		if ctree.subtrees[-1].label == longest_error.node.label:
			if ctree.subtrees[-1].span[0] == longest_error.node.span[0]:
				target = ctree.subtrees[-1]
	single_child_parents = []
	for node in moving:
		parent = node.parent
		parent.subtrees.remove(node)
		# if the parent now has only one child, look into whether it should be deleted
		if len(parent.subtrees) == 1:
			if parent.label == parent.subtrees[0].label:
				single_child_parents.append(parent)
		target.subtrees.append(node)
		node.parent = target
		addendum.append(node.label)
	group_desc += ' ' + '_'.join(addendum)
	group_fields['nodes moving'] = ' '.join(addendum)
	test_tree.update_span()

	for parent in single_child_parents:
		if len(parent.subtrees) == 1:
			if parent.subtrees[0].extra and parent.label == parent.subtrees[0].label:
				eerror = bracket_errors.get_extra_error(ungrouped, parent.subtrees[0])
				repair_tree.repair_extra_node(eerror, test_tree)
				to_group.append(eerror)

	# attempt to repair the longest crossing error
	if target == ctree:
		if repair_tree.repair_missing_node(longest_error, test_tree, failure_expected=True):
			to_group.append(longest_error)
	if error not in to_group:
		to_group.append(error)
	target.extra = False
	group_desc += ' ' + text + ' |ecs1'
	group_fields['ID'] = 'ecs1'
	group_fields['old desc'] = group_desc
	return group_fields, test_tree


def extra_multicrossing_starting(error, test_tree, to_group, starting, ungrouped, ctree):
	'''Extra, then if there are crossing brackets that start here, and no
	crossing bracket that ends at the same spot, the other thing under this
	bracket has something that should have attached to it, but attached too high.
	Consider what would happen if it had attached here and see what other errors
	it fixes (ie this extra may now match with a missing bracket above)'''
	
###	print error
###	print ctree

	# find the longest crossing missing bracket that starts here
	start = starting.keys()[0]
	cend = ctree.span[1]
	crossing_errors = starting[start]
	longest_error = None
	for merror in crossing_errors:
		if longest_error is None or longest_error.node.span[1] < merror.node.span[1]:
			longest_error = merror
	mspan = (cend, longest_error.node.span[1])
###	print mspan

	# find the set of missing brackets that end where that one ends
###	print "Related missing:"
	related_missing = []
	for merror in ungrouped:
		if merror.missing:
			if merror.node.span[1] == longest_error.node.span[1]:
				related_missing.append((merror.node.span, merror))
###				print merror
	related_missing.sort()
	
	# find the set of extra brackets that end where this one ends
###	print "Related extra:"
	related_extra = []
	for eerror in ungrouped:
		if eerror.extra:
			current_node = bracket_errors.get_extra_tree(eerror, test_tree)
			if current_node.span[1] == ctree.span[1]:
				related_extra.append((current_node.span, eerror))
###				print current_node
###				print eerror
	related_extra.sort()
	
	# find the lowest pairing
	lowest = None
	for pair in related_extra:
		for mpair in related_missing:
			if mpair[1].node.label == pair[1].node.label:
				if mpair[1].node.span[0] == pair[1].node.span[0]:
					lowest = pair[1]
					break
	if lowest is None:
		return None, test_tree
###	print lowest

	# find all the parts that start in the missing bracket to be here
	moving = []
	while cend < mspan[1]:
		brac = test_tree
		done = False
		while not done:
			for subtree in brac.subtrees:
				if cend == subtree.span[0]:
					moving.append(subtree)
					done = True
					cend = subtree.span[1]
					break
				if subtree.span[0] < cend < subtree.span[1]:
					brac = subtree
					break
	# move them across
	group_fields = {}
	group_fields['type'] = 'attachment'
	group_fields['height'] = 'too high'
	group_fields['from parent'] = moving[0].parent.label
	addendum = []
	target = bracket_errors.get_extra_tree(lowest, test_tree)
	group_desc = 'attachment too_high %s_instead_of_%s' % (moving[0].parent.label, target.label)
	group_fields['to parent'] = target.label
	single_child_parents = []
	for node in moving:
		parent = node.parent
		parent.subtrees.remove(node)
		# if the parent now has only one child, look into whether it should be deleted
		if len(parent.subtrees) == 1:
			if parent.label == parent.subtrees[0].label:
				single_child_parents.append(parent)
		target.subtrees.append(node)
		node.parent = target
		addendum.append(node.label)
	group_fields['nodes moving'] = ' '.join(addendum)
	group_desc += ' ' + '_'.join(addendum)
	test_tree.update_span()

	for parent in single_child_parents:
		if len(parent.subtrees) == 1:
			if parent.subtrees[0].extra and parent.label == parent.subtrees[0].label:
				eerror = bracket_errors.get_extra_error(ungrouped, parent.subtrees[0])
				repair_tree.repair_extra_node(eerror, test_tree)
				to_group.append(eerror)

	# attempt to repair the longest crossing error
	if target == ctree:
		if repair_tree.repair_missing_node(longest_error, test_tree, failure_expected=True):
			to_group.append(longest_error)
	group_desc += ' |emcs1'
	group_fields['ID'] = 'emcs1'
	group_fields['old desc'] = group_desc
	return group_fields, test_tree

def extra_matching_crossing_miss(error, test_tree, shortest_error, ungrouped, to_group):
	if shortest_error.node.span[1] == error.node.span[1]:
		moving = []
		mspan = shortest_error.node.span
		cend = error.node.span[0]
		while cend > mspan[0]:
			brac = test_tree
			done = False
			while not done:
				for subtree in brac.subtrees:
					if cend == subtree.span[1] and subtree.span[0] >= mspan[0]:
						moving.append(subtree)
						done = True
						cend = subtree.span[0]
						break
					if subtree.span[0] < cend <= subtree.span[1]:
						brac = subtree
						break
		# move them across
		group_fields = {}
		group_fields['type'] = 'attachment'
		group_fields['height'] = 'incorrect'
		group_fields['from parents'] = ''
###		print
###		print "Moving"
		for node in moving:
			group_fields['from parents'] += ' ' + node.parent.label
###			print node
		addendum = []
		target = bracket_errors.get_extra_tree(error, test_tree)
		target.extra = False
###		print "To:", target
###		print 'error is:', error
		group_desc = 'attachment incorrect %s_instead_of_%s' % (moving[0].parent.label, target.label)
		group_fields['to parent'] = target.label
		single_child_parents = []
		for node in moving:
			parent = node.parent
			node.parent.subtrees.remove(node)
			# if the parent now has only one child, look into whether it should be deleted
			if len(parent.subtrees) == 1:
				if parent.label == parent.subtrees[0].label:
					single_child_parents.append(parent)
			target.subtrees.insert(0, node)
			node.parent = target
			addendum.append(node.label)
		group_fields['nodes moving'] = ' '.join(addendum)
		group_desc += ' ' + '_'.join(addendum)
		test_tree.update_span()

		for parent in single_child_parents:
			if len(parent.subtrees) == 1:
				if parent.subtrees[0].extra and parent.label == parent.subtrees[0].label:
					eerror = bracket_errors.get_extra_error(ungrouped, parent.subtrees[0])
					if eerror is not None:
						repair_tree.repair_extra_node(eerror, test_tree)
						to_group.append(eerror)

		to_group.append(error)
		to_group.append(shortest_error)
		group_desc += ' |emcm1'
		group_fields['ID'] = 'emcm1'
		group_fields['old desc'] = group_desc
		test_tree.check_consistency()
		return group_fields, test_tree
	return None, test_tree

def check_spans(merror, node):
	left = merror.node.span[0]
	right = merror.node.span[1]
	satisfied = 0
	for subtree in node.subtrees:
		if subtree.span[0] == left:
			satisfied += 1
		if subtree.span[1] == right:
			satisfied += 1
	return satisfied == 2

def extra_matching_miss(error, test_tree, merror, ctree, to_group):
	'''Extra, then if there is no crossing bracket that ends here, and there is a
	matching missing bracket above, then the thing missing from the above bracket
	is attaching too high and should attach to this instead.  Or, if this is not
	the first thing in the above bracket, then it is attaching too low.'''
	parent = ctree.parent
	if parent.extra:
		return None, test_tree
	if merror.node.span[0] == error.node.span[0]:
###		print 'left'
###		print "Fixing:"
###		print merror
###		print error
		# there are spans to the right that should be under here
		group_fields = {}
		group_fields['type'] = 'attachment'
		group_fields['height'] = 'too high'
		group_fields['from parent'] = parent.label
		group_fields['to parent'] = ctree.label
		group_desc = 'attachment too_high %s_instead_of_%s' % (parent.label, ctree.label)
		to_group.append(error)
		to_group.append(merror)
		ctree.extra = False
		move = []
		for subtree in parent.subtrees:
			if ctree.span[1] <= subtree.span[0] and subtree.span[1] <= merror.node.span[1]:
				move.append(subtree)
		addendum = []
		for node in move:
			node.parent.subtrees.remove(node)
			ctree.subtrees.append(node)
			node.parent = ctree
			addendum.append(node.label)
		group_desc += ' ' + '_'.join(addendum)
		group_fields['nodes moving'] = ' '.join(addendum)
		test_tree.update_span()
		group_desc += ' |emm1'
		group_fields['ID'] = 'emm1'
		group_fields['old desc'] = group_desc
		return group_fields, test_tree
	elif merror.node.span[1] == error.node.span[1]:
###		print 'right'
		# there are spans to the left that should be under here
		# find them
		move = []
		cend = error.node.span[0]
		while cend > merror.node.span[0]:
			brac = test_tree
			done = False
			while not done:
				for subtree in brac.subtrees:
					if cend == subtree.span[1]:
						move.insert(0, subtree)
						done = True
						cend = subtree.span[0]
						break
					if subtree.span[0] < cend <= subtree.span[1]:
						brac = subtree
						break
		group_fields = {}
		group_desc = ''
		if move[0] == parent.subtrees[0]:
			group_desc = 'fencepost_error'
			group_fields['type'] = 'fencepost'
		else:
			group_desc = 'attachment incorrect '
			group_fields['type'] = 'attachment'
			labels = []
			for subtree in parent.subtrees:
				if subtree != move[0]:
					labels.append(subtree.label)
				else:
					break
			group_desc += '_'.join(labels)
			group_fields['siblings'] = ' '.join(labels)
			group_fields['from parent'] = parent.label
			group_fields['to parent'] = merror.node.label
			group_desc += '_instead_of_' + ctree.label
		group_fields['nodes moving'] = ' '.join([node.label for node in move])
		group_desc += ' ' + '_'.join([node.label for node in move])

		# move them
		ctree.extra = False
		for mover in move[::-1]:
			mover.parent.subtrees.remove(mover)
			ctree.subtrees.insert(0, mover)
			mover.parent = ctree

		test_tree.update_span()
		to_group.append(error)
		to_group.append(merror)
		group_desc += ' |emm2'
		group_fields['ID'] = 'emm2'
		group_fields['old desc'] = group_desc
		return group_fields, test_tree
	else:
		# there are spns on both sides that should be under here
		pass
	return None, test_tree

def extra_no_matching(error, test_tree, ctree, to_group):
	'''Extra, then if there is no crossing bracket that ends here, and there is
	no matching missing bracket above, the stuff under this bracket is attaching
	too low.'''
	if len(ctree.subtrees) == 1:
		return None, test_tree
	parent = ctree.parent
	group_fields = {}
	group_fields['to left siblings'] = ''
	group_fields['to right siblings'] = ''
	left = True
	for node in parent.subtrees:
		if node == ctree:
			left = False
		elif left:
			group_fields['to left siblings'] += ' ' + node.label
		else:
			group_fields['to right siblings'] += ' ' + node.label
	group_desc = 'attachment too_low %s_instead_of' % (ctree.subtrees[0].label)
	if parent.subtrees[0] == ctree:
		group_desc = 'extra incorrect %s' % (ctree.subtrees[0].label)
		group_fields['type'] = 'extra'
	else:
		group_fields['type'] = 'attachment'
		group_fields['height'] = 'too low'
		group_fields['from sibling'] = ''
	group_fields['from parent'] = ctree.label
	group_fields['to parent'] = parent.label
	text = ctree.word_yield()
	addendum = []
	for pos in xrange(len(parent.subtrees)):
		if parent.subtrees[pos] != ctree:
			group_fields['from sibling'] += ' ' + parent.subtrees[pos].label
			group_desc += '_' + parent.subtrees[pos].label
		else:
			parent.subtrees = parent.subtrees[:pos] + ctree.subtrees + parent.subtrees[pos+1:]
			for child in ctree.subtrees:
				child.parent = parent
				addendum.append(child.label)
			break
	group_fields['nodes moving'] = ' '.join(addendum[1:])
	to_group.append(error)
	group_fields['ID'] = 'enm1'
	group_desc += ' ' + '_'.join(addendum[1:]) + ' ' + text
	group_desc += ' |enm1'
	group_fields['old desc'] = group_desc
	return group_fields, test_tree


###############################################################################
#
# The next set of functions identify properties of the error and call the
# appropriate function above.
#
###############################################################################

def missing_not_crossing(error, test_tree, to_group, to_add, ungrouped):
	clevel, left, right = bracket_errors.get_constituents_for_span(error.node.span, test_tree)
	# Couldn't find a suitable level
	if clevel is None:
		return None, test_tree

	parent = clevel
###	print error
###	print parent
	if parent.extra:
		if parent.label == error.node.label:
			# This extra node matches with the missing node in the error - something
			# extra was incorrectly included
			return missing_with_matching_extra(error, test_tree, to_group, to_add, left, right, parent, ungrouped)
		else:
			# missing here, extra above, but they are different labels
			pass
	else:
		# First check that there are no 'extra' errors directly beneath here
		for subtree in clevel.subtrees:
			if error.node.span[0] <= subtree.span[0] and subtree.span[1] <= error.node.span[1]:
				if subtree.extra:
					return None, test_tree
				for subsubtree in subtree.subtrees:
					if subsubtree.extra:
						return None, test_tree

		return missing_with_nothing_nearby(error, test_tree, to_group, clevel, left, right, ungrouped)
	return None, test_tree

def missing_crossing(error, test, to_group, to_add):
#     . Missing, then if there is a crossing bracket ending here, and there is
#       an extra bracket above, then the thing the extra bracket contains has
#       attached too low.  Collapse it to 0 and see what else it fixes.

#     . Missing, then if there is a crossing bracket ending here, and there is
#       a mising bracket above...

#     . Missing, then if there is a crossing bracket ending here, and there is
#       no clear error above...

#     . Missing, then if there is a crossing bracket starting here...
	return None, test

def extra(error, test_tree, to_group, to_add, ungrouped):
	# Get the bracket in the tree that corresponds to this error
	ctree = bracket_errors.get_extra_tree(error, test_tree)
	if ctree is None:
		print 'Did not find the matching extra bracket'
		print >> sys.stderr, 'Did not find the matching extra bracket'
		print error
		print test_tree

	# Find all errors that cross this bracket
	crossing_errors = []
	for merror in ungrouped:
		if merror.missing and bracket_errors.error_crosses_bracket(merror, ctree):
			crossing_errors.append(merror)

	if len(crossing_errors) > 0:
		# sort them into those that start here and those that end here
		ending = {}
		starting = {}
		other = []
		for merror in crossing_errors:
			if ctree.span[0] < merror.node.span[0] < ctree.span[1] < merror.node.span[1]:
				start = merror.node.span[0]
				if start not in starting:
					starting[start] = []
				starting[start].append(merror)
			elif merror.node.span[0] < ctree.span[0] < merror.node.span[1] < ctree.span[1]:
				end = merror.node.span[1]
				if end not in ending:
					ending[end] = []
				ending[end].append(merror)
			else:
				other.append(merror)

		if len(starting) == 0 and len(ending) == 1 and len(other) == 0:
			return extra_crossing_ending(error, test_tree, to_group, ending, ungrouped, ctree)
		elif len(starting) == 1 and len(ending) == 0 and len(other) == 0:
			return extra_crossing_starting(error, test_tree, to_group, starting, ungrouped, ctree)
		elif len(starting) > 1 and len(ending) == 0:
			return extra_multicrossing_starting(error, test_tree, to_group, starting, ungrouped, ctree)
		else:
			# there could be a mixture of starting and ending
			# of multiple starting points, and multiple ending points
			pass
	else:
		# no crossing errors
		# find the smallest missing error that covers this extra error
		shortest_error = None
		snode = None
		for merror in ungrouped:
			if merror.missing:
				mnode = merror.node
				if mnode.span[0] <= error.node.span[0] and error.node.span[1] <= mnode.span[1]:
					if snode is None or (snode.span[0] <= mnode.span[0] and mnode.span[1] <= snode.span[1]):
						shortest_error = merror
						snode = merror.node
		# Check that there are no spans that are over the extra and under the missing
		intermediate_spans = False
		shortest_error is None
		if shortest_error is not None:
			if shortest_error.node.span[0] < ctree.parent.span[0] and ctree.parent.span[1] <= shortest_error.node.span[1]:
				if not ctree.parent.extra:
					intermediate_spans = True
			elif shortest_error.node.span[0] <= ctree.parent.span[0] and ctree.parent.span[1] < shortest_error.node.span[1]:
				if not ctree.parent.extra:
					intermediate_spans = True

###		print 'considering'
###		print error
###		print shortest_error
		if shortest_error is None:
			intermediate_spans = True
		if not intermediate_spans and shortest_error.node.label == ctree.label:
			# we have a matching missing error
###			print test_tree
###			print shortest_error
			if bracket_errors.error_crosses_bracket(shortest_error, test_tree):
###				print 'crossing'
				return extra_matching_crossing_miss(error, test_tree, shortest_error, ungrouped, to_group)
			else:
###				print 'not crossing'
				return extra_matching_miss(error, test_tree, shortest_error, ctree, to_group)
		else:
###			if shortest_error.node.label == ctree.label:
###				if ctree.parent.extra
			return extra_no_matching(error, test_tree, ctree, to_group)
	return None, test_tree

# Attachment:
# Look at the lowest error (though if it has a unary application going to
# something wrong too, consider them together)
# I think these also generally apply regardless of order of constituents (is
# the error earlier or later in the sentence)
def attachment_error(ungrouped, grouped, gold, test):
	changed = False
	global global_gold
	global_gold = gold
	while True:
		test.check_consistency()
		# fix errors one at a time
		to_group = []
		to_add = []
		group_fields = None
		for error in ungrouped:
			if error.missing:
###				print 'missing'
				if not bracket_errors.error_crosses_bracket(error, test):
###					print 'not crossing'
					group_fields, test = missing_not_crossing(error, test, to_group, to_add, ungrouped)
				else:
###					print 'crossing'
					group_fields, test = missing_crossing(error, test, to_group, to_add)
			elif error.extra:
###				print 'extra'
				group_fields, test = extra(error, test, to_group, to_add, ungrouped)
			if group_fields is not None:
###				print 'resolved!'
				break

		if group_fields is not None:
			group = error_group.Error_Group()
			group.fields = group_fields
			group.desc = group.fields['old desc']
###			print group.desc
###			print group.fields
			group.determine_type()
###			print 'Class:', group.classification
###			print 'Fixes:',
###			for error in to_group:
###				print error
###				print '%s (%d %d)' % (error.node.label, error.node.span[0], error.node.span[1]),
###			print
			for error in to_group:
				ungrouped.remove(error)
				group.errors.append(error)
			for error in to_add:
				ungrouped.append(error)
			test = classify.check_for_matching_errors(ungrouped, group, gold, test)
			grouped.append(group)
			changed = True
###			nerror_set = bracket_errors.get_errors(gold, test)[0]
###			missing = bracket_errors.get_missing_errors(nerror_set, test)
###			print test.colour_repr(missing=missing).strip()
		else:
			break
	return changed, test


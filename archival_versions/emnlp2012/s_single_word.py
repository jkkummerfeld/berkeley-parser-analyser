#!/usr/bin/env python

import sys
import repair_tree
import error_group

def single_word_error(ungrouped, grouped, gold, test):
	'''An extra/missing bracket at any depth that has a span of 1
	'''
	singles = {}
	for error in ungrouped:
		span = error.node.span
		if span[0] + 1 == span[1]:
			if span not in singles:
				singles[span] = []
			singles[span].append(error)

	changed = False
	to_fix = []
	for span in singles:
		errors = singles[span]
		# First check for cases where there is a matching bracket (so it is in fact
		# just the wrong label)
		if len(errors) == 2 and errors[0].extra != errors[1].extra:
			group = error_group.Error_Group()
			group.errors += errors
			group.fields['type'] = 'wrong label, right span'
			group.desc = 'single_word diff '
			if errors[0].extra:
				group.desc += errors[0].node.label + '_' + errors[1].node.label
			else:
				group.desc += errors[1].node.label + '_' + errors[0].node.label
			grouped.append(group)
			to_fix += errors
		else:
			# this includes cases of multiple brackets (so we don't know which to
			# link as above), and a single bracket error
			for error in errors:
				# check to see if a matching bracket type starts here and matches type
				use = True
				for uerror in ungrouped:
					if uerror.node.span[0] == error.node.span[0]:
						if uerror.node.label == error.node.label:
							if uerror.missing and error.extra:
								use = False
								break
							if uerror.extra and error.missing:
								use = False
								break
				if not use:
					continue
				group = error_group.Error_Group()
				group.errors.append(error)
				group.desc = 'single_word '
				if error.missing:
					group.desc += 'miss'
				else:
					group.desc += 'extra'
				group.desc += ' ' + error.node.label
###				print group.desc
				group.fields['type'] = 'single word phrase'
				group.fields['old desc'] = group.desc
				grouped.append(group)
				to_fix.append(error)
	for error in to_fix:
		ungrouped.remove(error)
		if error.extra:
			repair_tree.repair_extra_node(error, test)
		else:
			repair_tree.repair_missing_node(error, test)
	return changed, test


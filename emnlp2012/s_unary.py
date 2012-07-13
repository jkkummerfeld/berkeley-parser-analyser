#!/usr/bin/env python

import sys
import ptb, error_tree, repair_tree, bracket_errors, error_group

# Unary errors:
# Generally, didn't realise what kind of thing this was
# IF there is something of this span that is right
#  - Missing
#  - Extra
#  - Wrong label
# If there is nothing right, but we have one extra and one missing, then it is
# a case of misundertanding what this was
# Also, want to group these by the pairing (error label and label below)
def unary_error(ungrouped, grouped, gold, test):
	nodes, span_set = test.get_spans()
	gold_nodes, gold_span_set = gold.get_spans()
	relevant_errors = {}
	for error in ungrouped:
		span = error.node.span
		if span[1] - span[0] > 1 and span in span_set and span in gold_span_set:
			if span not in relevant_errors:
				relevant_errors[span] = (len(span_set[span].values()), len(gold_span_set[span].values()), [])
			relevant_errors[span][2].append(error)
	
	changed = False
	for span in relevant_errors:
		test_count, gold_count, errors = relevant_errors[span]
		missing_errors = 0
		extra_errors = 0
		for error in errors:
			if error.missing:
				missing_errors += 1
			else:
				extra_errors += 1
		if test_count > 0 and extra_errors == 0:
			# there is/are missing unary production(s) here
			group = error_group.Error_Group()
			current_labels = []
			for node_set_label in span_set[span]:
				for node in span_set[span][node_set_label]:
					current_labels.append(node.label)
			current_labels.sort()
			missing_labels = [error.node.label for error in errors]
			missing_labels.sort()
			for error in errors:
				ungrouped.remove(error)
				group.errors.append(error)
				repair_tree.repair_missing_node(error, test)
			group.fields['type'] = 'unary'
			group.fields['subtype'] = 'missing'
			group.desc = 'unary miss %s over %s' % ('_'.join(missing_labels), '_'.join(current_labels))
			group.fields['nodes'] = ' '.join(missing_labels)
			group.fields['old desc'] = group.desc
			grouped.append(group)
###			print group.desc
			changed = True
		elif gold_count > 0 and missing_errors == 0:

			# there is/are extra unary production(s) here
			group = error_group.Error_Group()
			current_labels = []
			for node_set_label in span_set[span]:
				for node in span_set[span][node_set_label]:
					if not node.extra:
						current_labels.append(node.label)
			current_labels.sort()
			extra_labels = [error.node.label for error in errors]
			extra_labels.sort()
			# only use it if there isn't a matching missing error directly above
			skip = False
			if len(extra_labels) == 1:
				error = errors[0]
				for merror in ungrouped:
					if merror.node.label == extra_labels[0]:
						if merror.node.span[0] == error.node.span[0]:
							if error.node.parent.span[1] >= merror.node.span[1]:
								skip = True
								break
						elif merror.node.span[1] == error.node.span[1]:
							if error.node.parent.span[0] <= merror.node.span[0]:
								skip = True
								break
			if not skip:
				for error in errors:
					ungrouped.remove(error)
					group.errors.append(error)
					repair_tree.repair_extra_node(error, test)
				group.fields['type'] = 'unary'
				group.fields['subtype'] = 'extra'
				group.fields['nodes'] = ' '.join(extra_labels)
				group.desc = 'unary extra %s over %s' % ('_'.join(extra_labels), '_'.join(current_labels))
				group.fields['old desc'] = group.desc
				grouped.append(group)
				changed = True
		elif missing_errors == 1 and extra_errors == 1:
			# We have a mislabelled node
			extra = relevant_errors[span][2][0]
			missing = relevant_errors[span][2][1]
			if not extra.extra:
				extra = relevant_errors[span][2][1]
				missing = relevant_errors[span][2][0]

			group = error_group.Error_Group()
			group.fields['type'] = 'wrong label, right span'
			if test_count == 1 and gold_count == 1:
				group.desc = 'diff %s should_be %s' % (extra.node.label, missing.node.label)
###				print  'wrong label, right span %s should be %s' % (extra.node.label, missing.node.label)
			else:
				group.desc = 'unary diff %s should_be %s' % (extra.node.label, missing.node.label)
			group.fields['old desc'] = group.desc
			group.errors.append(extra)
			ungrouped.remove(extra)
			group.errors.append(missing)
			ungrouped.remove(missing)
			repair_tree.repair_extra_missing_pair(missing, extra, test)
			grouped.append(group)
			changed = True
		else:
			# Most of the other cases are either just an incorrect node labelling, or less clear
			# TODO:  One case to consider is when there is a correct node with all
			# the missing nodes above and all the extra nodes below (or vice versa)
			pass

	return changed, test


#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

phrase_labels =  [
	'S', 'SBAR', 'SBARQ', 'SINV', 'SQ', 'ADJP', 'ADVP', 'CONJP', 'FRAG', 'INTJ',
	'LST', 'NAC', 'NP', 'NX', 'PP', 'PRN', 'PRT', 'QP', 'RRC', 'UCP', 'VP', 'WHADJP',
	'WHAVP', 'WHNP', 'WHPP', 'X'
]

seen_movers = set()


def value_present(info, fields, values):
	for field in fields:
		if field in info:
			for value in values:
				if value in info[field]:
					return True
	return False


def classify(info, gold, test):
	coord_tags = ['CC']

	# Classification
	info['classified_type'] = 'UNSET ' + info['type']
	if value_present(info, ['type'], ['move']):
		if 'start left siblings' in info:
			if len(info['start left siblings']) > 0 and info['start left siblings'][-1] in coord_tags:
				info['classified_type'] = "Co-ordination"
				return
		if 'start right siblings' in info:
			if len(info['start right siblings']) > 0 and info['start right siblings'][0] in coord_tags:
				info['classified_type'] = "Co-ordination"
				return
		if 'end left siblings' in info:
			if len(info['end left siblings']) > 0 and info['end left siblings'][-1] in coord_tags:
				info['classified_type'] = "Co-ordination"
				return
		if 'end right siblings' in info:
			if len(info['end right siblings']) > 0 and info['end right siblings'][0] in coord_tags:
				info['classified_type'] = "Co-ordination"
				return
		if 'movers' in info:
			if len(info['movers']) > 0 and (info['movers'][-1] in coord_tags or info['movers'][0] in coord_tags):
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

	if 'over_word' in info and info['over_word']:
		info['classified_type'] = "Single Word Phrase"
		return

	if value_present(info, ['type'], ['relabel']):
		info['classified_type'] = "Different label"
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
		if len(info['right siblings']) > 0 and info['right siblings'][0] in coord_tags:
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


if __name__ == '__main__':
	from transform_search import main
	import sys
	main(sys.argv, classify)

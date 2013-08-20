#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

phrase_labels = [
	'ADJP', 'ADVP', 'CLP', 'CP', 'DNP', 'DP', 'DVP', 'FRAG', 'IP', 'LCP', 'LST',
	'NP', 'PP', 'PRN', 'QP', 'UCP', 'VP', 'VCD', 'VCP', 'VNV', 'VPT', 'VRD', 'VSB'
]

seen_movers = set()

unicode_punctuation = {
	"PU·": (":", ""),
	"PU—": ("-", ""),
	"PU‘": ("'", ""),
	"PU’": ("'", ""),
	"PU“": ('"', ""),
	"PU”": ('"', ""),
	"PU…": ("_", ""),
	"PU━": ("", ""),
	"PU、": (",", "CC"),
	"PU。": (".", "CC"),
	"PU〈": ("(", ""),
	"PU〉": (")", ""),
	"PU《": ("(", ""),
	"PU》": (")", ""),
	"PU「": ("", ""),
	"PU」": ("", ""),
	"PU『": ("", ""),
	"PU』": ("", ""),
	"PU【": ("[", ""),
	"PU】": ("]", ""),
	"PU！": ("!", ""),
	"PU＂": ("'", ""),
	"PU＆": ("&", "CC"),
	"PU＇": ("'", ""),
	"PU（": ("(", ""),
	"PU）": (")", ""),
	"PU＊": ("*", ""),
	"PU，": (".", "CC"),
	"PU－": ("-", ""),
	"PU．": (".", "CC"),
	"PU／": ("/", ""),
	"PU：": (":", ""),
	"PU；": (";", ""),
	"PU＜": ("<", ""),
	"PU＞": (">", ""),
	"PU？": ("?", ""),
	"PU～": ("~", ""),
	"PU——": ("--", ""),
	"PU—－": ("--", ""),
	"PU……": ("--", ""),
	"PU──": ("--", ""),
	"PU━━": ("--", ""),
	"PU－－": ("--", ""),
	"PU———": ("---", ""),
	"PU．．．": ("...", ""),
}

def value_present(info, fields, values):
	for field in fields:
		if field in info:
			for value in values:
				if value in info[field]:
					return True
	return False


def classify(info, gold, test):
	coord_tags = ['CC', 'PU']
	NP_tags = ['CC', 'NN', 'JJ', 'CD', 'OD', 'ETC', 'NT', 'NR', 'DEG']

	info['classified_type'] = ''

	incorrect_tags = []
	if 'auto preterminal span' in info:
		span = info['auto preterminal span']
		all_NP = True
		cur = 0
		for node in gold:
			if node.word is not None:
				if span[0] <= node.span[0] < span[1]:
					if node.label != info['auto preterminals'][cur]:
						incorrect_tags.append((node.label, info['auto preterminals'][cur]))
						cur += 1
					if node.label not in NP_tags and 'PU' not in node.label:
						all_NP = False
		if all_NP:
			info['classified_type'] = 'NP Internal - '

	# Single word phrase
	if 'over_word' in info and info['over_word']:
		info['classified_type'] += "Single Word Phrase"
		info['classified_type'] += " - " + info['type']
		this_seen = False
		all_phrasal = True
		all_non_phrasal = True
		for label in info['family']:
			if 'label' in info and label == info['label'] and not this_seen:
				this_seen = True
				continue
			if label in phrase_labels:
				all_non_phrasal = False
			else:
				all_phrasal = False
		if all_non_phrasal and info['type'] == 'remove':
			info['classified_type'] += " - for guidelines"
		elif all_phrasal and info['type'] == 'add':
			info['classified_type'] += " - for guidelines"
		return

	# Different label
	if info['type'] == 'relabel':
		info['classified_type'] += "Different label"
		return

	if info['type'] == 'move':
		# Note, we are missing one issue, going from VP PU VP to IP PU VP to IP PU
		# IP involves two steps (second is a unary), but could be considered one
		# mistake.

		# Check start
		label_series = []
		if 'start left siblings' in info:
			if len(info['movers']) == 1 and len(info['start left siblings']) > 1:
				series = info['start left siblings'][-2:] + info['movers']
				label_series.append(series)
			elif len(info['movers']) > 1 and len(info['start left siblings']) > 0:
				series = info['start left siblings'][-1:] + info['movers']
				label_series.append(series)
		if 'start right siblings' in info:
			if len(info['movers']) == 1 and len(info['start right siblings']) > 1:
				series = info['movers'] + info['start right siblings'][:2]
				label_series.append(series)
			elif len(info['movers']) > 1 and len(info['start right siblings']) > 0:
				series = info['movers'] + info['start right siblings'][:1]
				label_series.append(series)

		start_matches = [False, False, False]
		for series in label_series:
			indicator = series[1]
			if indicator in unicode_punctuation:
				indicator = unicode_punctuation[indicator][1]
			if indicator == 'CC':
				start_matches[0] = True
			if series[0] == series[2]:
				start_matches[1] = True
			if series[0] == info['old_parent']:
				start_matches[2] = True
		
		label_series = []
		if 'end left siblings' in info:
			if len(info['movers']) == 1 and len(info['end left siblings']) > 1:
				series = info['end left siblings'][-2:] + info['movers']
				label_series.append(series)
			elif len(info['movers']) > 1 and len(info['end left siblings']) > 0:
				series = info['end left siblings'][-1:] + info['movers']
				label_series.append(series)
		if 'end right siblings' in info:
			if len(info['movers']) == 1 and len(info['end right siblings']) > 1:
				series = info['movers'] + info['end right siblings'][:2]
				label_series.append(series)
			elif len(info['movers']) > 1 and len(info['end right siblings']) > 0:
				series = info['movers'] + info['end right siblings'][:1]
				label_series.append(series)

		end_matches = [False, False, False]
		for series in label_series:
			indicator = series[1]
			if indicator in unicode_punctuation:
				indicator = unicode_punctuation[indicator][1]
			if indicator == 'CC':
				end_matches[0] = True
			if series[0] == series[2]:
				end_matches[1] = True
			if series[0] == info['new_parent']:
				end_matches[2] = True

		# Check this
		if start_matches[0] and start_matches[1]:
			if end_matches[0] and end_matches[1]:
				info['classified_type'] += "Co-ordination - Wrong pair"
				return
		if start_matches[0] and start_matches[1] and start_matches[2]:
			info['classified_type'] += "Co-ordination - Incorrectly present"
			return
		if end_matches[0] and end_matches[1] and end_matches[2]:
			info['classified_type'] += "Co-ordination - Incorrectly missing"
			return

	if info['type'] == 'move':
		if value_present(info, ['movers'], ['PP']):
			info['classified_type'] += "PP Attachment"
			return
		if value_present(info, ['movers'], ['ADV', 'ADVP', 'ADJP']):
			info['classified_type'] += "Modifier Attachment"
			return
		if value_present(info, ["added label"], ["VRD", "VPT", "VCP", "VRD", "VCD", "VSB", "VPT", "VNV", "VCP"]):
			info['classified_type'] += "Split Verb Compound"
			return
		# Note, ordering here is important
		end_siblings = []
		if len(info['end right siblings']) > 0:
			end_siblings += info['end right siblings']
		if len(info['end left siblings']) > 0:
			end_siblings += info['end left siblings']
		# Restrict to phrase, (all leaves are out)
		all_non_phrase = True
		for label in info['movers']:
			if label in phrase_labels:
				all_non_phrase = False
		if not all_non_phrase:
			if 'adding node already present' not in info or not info['adding node already present']:
				if len(end_siblings) > 0:
					for label in end_siblings:
						if label in ['VP', 'VV']:
							info['classified_type'] += "Verb taking wrong arguments"
							return
		if len(end_siblings) > 0:
			all_NP = True
			for label in end_siblings:
				if label not in NP_tags:
					all_NP = False
					break
			if all_NP:
				info['classified_type'] += "Noun boundary error"
				return
		if value_present(info, ['movers'], ['NP']):
			info['classified_type'] += "Modifier Attachment"
			return
		if value_present(info, ['movers'], ['VP']):
			info['classified_type'] += "VP Attachment"
			return
		if value_present(info, ['movers'], ['VV']):
			info['classified_type'] += "Verb taking wrong arguments"
			return
		if value_present(info, ['movers'], ['CP', 'IP']):
			info['classified_type'] += "Clause Attachment"
			return

	if info['type'] == 'add':
		# Adjust to capture addition just for the annotation rules on combination
		if 'subtrees' in info:
			if len(info['subtrees']) == 1:
				info['classified_type'] = "Unary - {} over {}".format(info['label'], info['subtrees'][0])
				return
			for label in info['subtrees']:
				indicator = label
				if indicator in unicode_punctuation:
					indicator = unicode_punctuation[indicator][1]
				if indicator == 'CC' and len(info['subtrees']) == 3:
					info['classified_type'] += "Co-ordination"
					return

	if info['type'] == 'remove':
		if 'family' in info and len(info['family']) == 1:
			info['classified_type'] = "Unary - {} over {}".format(info['parent'], info['label'])
			return
		if 'subtrees' in info and len(info['subtrees']) == 1:
			info['classified_type'] = "Unary - {} over {}".format(info['label'], info['subtrees'][0])
			return

		if len(info['right siblings']) == 1:
			if 'POS confusion' in info:
				if info['POS confusion'][0] != info['POS confusion'][1]:
					info['classified_type'] += "Sense Confusion, causing mis-attachment - {} and {}".format(*info['POS confusion'])
					return
			elif 'VV' in info['subtrees']:
				info['classified_type'] += "Verb taking wrong arguments"
				return
			else:
				info['classified_type'] += "{} Attachment".format(info['right siblings'][0])
				return

	if value_present(info, ['label'], ['UCP']):
		info['classified_type'] += "Co-ordination - UCP related"
		return

	if 'right siblings' in info:
		if len(info['right siblings']) > 0:
			indicator = info['right siblings'][0]
			if indicator in unicode_punctuation:
				indicator = unicode_punctuation[indicator][1]
			if indicator == 'CC':
				info['classified_type'] += "Co-ordination"
				return

	if 'subtrees' in info and 'PP' in info['subtrees'][1:]:
		info['classified_type'] += "PP Attachment"
		return

	if 'subtrees' in info:
		for label in info['subtrees'][1:]:
			if label in ['CP', 'IP']:
				info['classified_type'] += "Clause Attachment"
				return
	
	if value_present(info, ['label'], ['ADVP', 'ADJP']):
		info['classified_type'] += "Modifier Attachment"
		return

	if 'subtrees' in info:
		if 'ADVP' in info['subtrees'][1:] or 'ADJP' in info['subtrees'][1:]:
			info['classified_type'] += "Modifier Attachment"
			return
	
	if 'end left siblings' in info and len(info['end left siblings']) > 0:
		if info['end left siblings'][-1] in ['ADJP', 'ADVP']:
			info['classified_type'] += "Modifier Attachment"
			return

	# We have (X (X) (X))
	if 'label' in info:
		label = info['label']
		if 'subtrees' in info:
			all_same = True
			for slabel in info['subtrees']:
				if slabel != label:
					all_same = False
					break
			if all_same:
				info['classified_type'] += "Modifier Attachment"
				return

	if info['type'] == 'move':
		if 'POS confusion' in info:
			if info['POS confusion'][0] != info['POS confusion'][1]:
				info['classified_type'] += "Sense Confusion, causing mis-attachment - {} and {}".format(*info['POS confusion'])
				return
		all_noun = True
		for field in ['end left siblings', 'new_parent', 'movers', 'old_family', 'old_parent', 'new_family', 'start left siblings', 'end right siblings', 'start right siblings']:
			vals = info[field]
			if type(vals) != type([]):
				vals = [vals]
			for label in vals:
				if label not in NP_tags and label != 'NP' and 'PU' not in label:
					all_noun = False
					break
		if all_noun:
			info['classified_type'] += "Noun boundary error"
			return

	if info['type'] == 'remove':
		NP_internal = True
		for label in info['subtrees'] + [info['parent']] + info['family'] + [info['label']] + info['right siblings']:
			if label not in ['NP', 'QP']:
				NP_internal = False
		if NP_internal:
			info['classified_type'] = "NP Internal - other"
			return

	if info['type'] == 'add':
		if info['subtrees'][0] in ['ADVP', 'ADJP', 'PP'] and len(info['right siblings']) > 0:
			info['classified_type'] = "Scope error - {}".format(info['subtrees'][0])
			return

	info['classified_type'] += 'UNSET ' + info['type']


if __name__ == '__main__':
	from transform_search import main
	import sys
	main(sys.argv, classify)

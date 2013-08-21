#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import error_set
import ptb, render_tree
from collections import defaultdict
from StringIO import StringIO
import codecs

def value_present(info, fields, values):
	for field in fields:
		if field in info:
			for value in values:
				if value in info[field]:
					return True
	return False

phrase_labels =  [
	'S', 'SBAR', 'SBARQ', 'SINV', 'SQ', 'ADJP', 'ADVP', 'CONJP', 'FRAG', 'INTJ',
	'LST', 'NAC', 'NP', 'NX', 'PP', 'PRN', 'PRT', 'QP', 'RRC', 'UCP', 'VP', 'WHADJP',
	'WHAVP', 'WHNP', 'WHPP', 'X'
]
chinese_phrase_labels = [
	'ADJP', 'ADVP', 'CLP', 'CP', 'DNP', 'DP', 'DVP', 'FRAG', 'IP', 'LCP', 'LST',
	'NP', 'PP', 'PRN', 'QP', 'UCP', 'VP', 'VCD', 'VCP', 'VNV', 'VPT', 'VRD', 'VSB'
]

seen_movers = set()
def classify(info, language='english', gold=None, test=None):
	# Avoid double-counting
	global seen_mmovers
	if 'mover info' in info:
		for mover in info['mover info']:
			if mover in seen_movers:
				info["double move"] = True
			seen_movers.add(mover)

	# Language specific adjustments
	if language == 'chinese':
		return chinese_classify(info, gold, test)
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

	if 'over_word' in info:
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
def chinese_classify(info, gold, test):
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
	if 'over_word' in info:
		info['classified_type'] += "Single Word Phrase"
		info['classified_type'] += " - " + info['type']
		this_seen = False
		all_phrasal = True
		all_non_phrasal = True
		for label in info['family']:
			if 'label' in info and label == info['label'] and not this_seen:
				this_seen = True
				continue
			if label in chinese_phrase_labels:
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
			if label in chinese_phrase_labels:
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
				info['classified_type'] = "Unary - %s over %s" % (info['label'], info['subtrees'][0])
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
			info['classified_type'] = "Unary - %s over %s" % (info['parent'], info['label'])
			return
		if 'subtrees' in info and len(info['subtrees']) == 1:
			info['classified_type'] = "Unary - %s over %s" % (info['label'], info['subtrees'][0])
			return

		if len(info['right siblings']) == 1:
			if 'POS confusion' in info:
				if info['POS confusion'][0] != info['POS confusion'][1]:
					info['classified_type'] += "Sense Confusion, causing mis-attachment - %s and %s" % info['POS confusion']
					return
			elif 'VV' in info['subtrees']:
				info['classified_type'] += "Verb taking wrong arguments"
				return
			else:
				info['classified_type'] += "%s Attachment" % info['right siblings'][0]
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
				info['classified_type'] += "Sense Confusion, causing mis-attachment - %s and %s" % info['POS confusion']
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
			info['classified_type'] = "Scope error - %s" % info['subtrees'][0]
			return

	info['classified_type'] += 'UNSET ' + info['type']

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
	if tree.word is not None:
		ans.append(tree.label)
	for subtree in tree.subtrees:
		get_preterminals(subtree, ans)
	if return_tuple:
		return tuple(ans)

def gen_different_label_successor(ctree, eerror, merror):
	tree = ctree.clone()
	info = {'type': 'relabel', 'change': (eerror[2], merror[2])}
	# find the extra span
	spans = tree.get_spans(eerror[1][0], eerror[1][1])
	extra_span = None
	for span in spans:
		if eerror[2] == span[2].label:
			extra_span = span[2]
	assert extra_span is not None

	# relabel
	extra_span.label = merror[2]
	info['subtrees'] = [get_label(subtree) for subtree in extra_span.subtrees]
	info['parent'] = extra_span.parent.label
	info['span'] = extra_span.span
	info['family'] = [get_label(subtree) for subtree in extra_span.parent.subtrees]
	info['auto preterminals'] = get_preterminals(extra_span)
	info['auto preterminal span'] = extra_span.span
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
	info['over words'] = True
	# move the subtrees
	for i in xrange(len(parent.subtrees)):
		if parent.subtrees[i] == first:
			while parent.subtrees[i] != last:
				if parent.subtrees[i].word is None:
					info['over words'] = False
				nnode.subtrees.append(parent.subtrees.pop(i))
				nnode.subtrees[-1].parent = nnode
			nnode.subtrees.append(parent.subtrees.pop(i))
			nnode.subtrees[-1].parent = nnode
			parent.subtrees.insert(i, nnode)
			break
	info['label'] = get_label(nnode)
	info['span'] = nnode.span
	info['subtrees'] = [get_label(subtree) for subtree in nnode.subtrees]
	info['parent'] = nnode.parent.label
	info['family'] = [get_label(subtree) for subtree in nnode.parent.subtrees]
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
	info['auto preterminals'] = get_preterminals(nnode)
	info['auto preterminal span'] = nnode.span
	return (True, tree, info)

def gen_extra_successor(ctree, error, gold):
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
	info['subtrees'] = [get_label(subtree) for subtree in extra_span.subtrees]
	info['parent'] = extra_span.parent.label
	info['family'] = [get_label(subtree) for subtree in extra_span.parent.subtrees]
	info['left siblings'] = []
	info['right siblings'] = []
	cur = []
	for span in extra_span.parent.subtrees:
		if span != extra_span:
			cur.append(span.label)
		else:
			info['left siblings'] = cur
			cur = []
	info['right siblings'] = cur
	if len(cur) == 1:
		sibling = extra_span.parent.subtrees[-1]
		for node in sibling:
			if node.word is not None:
				gold_eq = gold.get_lowest_span(node.span[0], node.span[1])
				if gold_eq is not None:
					if get_label(node) != gold_eq.label:
						info['POS confusion'] = (get_label(node), get_label(gold_eq))

	# remove the span
	info['over words'] = True
	parent = extra_span.parent
	for i in xrange(len(parent.subtrees)):
		if parent.subtrees[i] == extra_span:
			parent.subtrees.pop(i)
			for subtree in extra_span.subtrees[::-1]:
				subtree.parent = parent
				parent.subtrees.insert(i, subtree)
				if subtree.word is None:
					info['over words'] = False
			break
	if len(extra_span.subtrees) == 1 and extra_span.subtrees[0].word is not None:
		info['over_word'] = True
	info['auto preterminals'] = get_preterminals(parent)
	info['auto preterminal span'] = parent.span
	return (True, tree, info)

def gen_move_successors(pos, starting, ctree, source_span, left, right, cerrors, gold, verbose=False):
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

		match_found = False
		for subtree in new_parent.subtrees:
			if pos in subtree.span:
				match_found = True
		
		if use and match_found:
			info['old_parent'] = get_label(old_parent)
			info['new_parent'] = get_label(new_parent)
			info['movers'] = []
			info['mover info'] = []
			info['new_family'] = [get_label(subtree) for subtree in new_parent.subtrees]
			info['start left siblings'] = [get_label(node) for node in old_parent.subtrees[:left]]
			info['start right siblings'] = [get_label(node) for node in old_parent.subtrees[right+1:]]

			# Find LCS
			options = []
			cur_node = old_parent
			while cur_node is not None:
				options.append(cur_node)
				cur_node = cur_node.parent
			cur_node = new_parent
			while cur_node is not None:
				if cur_node in options:
					options = [cur_node]
					break
				cur_node = cur_node.parent
			if len(options) == 1:
				info['auto preterminals'] = get_preterminals(options[0])
				info['auto preterminal span'] = options[0].span

			# Move [left, right] from old_parent to new_parent
			insertion_point = 0
			for subtree in new_parent.subtrees:
				if subtree.span[0] >= old_parent.subtrees[left].span[0]:
					break
				insertion_point += 1
			info['end left siblings'] = [get_label(node) for node in new_parent.subtrees[:insertion_point]]
			info['end right siblings'] = [get_label(node) for node in new_parent.subtrees[insertion_point:]]
			moved = set()
			for i in xrange(left, right + 1):
				mover = old_parent.subtrees.pop(left)
				moved.add(mover)
				new_parent.subtrees.insert(insertion_point, mover)
				mover.parent = new_parent
				insertion_point += 1
				info['movers'].append(get_label(mover))
				# Look for POS confusion
				if left == right and mover.span[1] - mover.span[0] == 1:
					preterminal = mover
					while preterminal.word is None:
						preterminal = preterminal.subtrees[0]
					gold_eq = gold.get_lowest_span(preterminal.span[0], preterminal.span[1])
					if gold_eq is not None:
						info['POS confusion'] = (get_label(preterminal), get_label(gold_eq))
				info['mover info'].append((get_label(mover), mover.span))
			info['old_family'] = [get_label(subtree) for subtree in old_parent.subtrees]
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
			nerrors = error_set.Error_Set()
			for error in tree.get_errors(gold):
				nerrors.add_error(error[0], error[1], error[2], error[3])
			for error in nerrors.missing + nerrors.crossing:
				if error[1] == nspan and error[0] != 'extra':
					to_fix.append(error)
			nnode = ptb.PTB_Tree()
			if len(to_fix) == 1:
				error = to_fix[0]
				info['added and moved'] = True
				info['added label'] = error[2]
				first, last = None, None
				already_here = []
				for node in new_parent.subtrees:
					if node.span[0] == nspan[0]:
						first = node
					if first is not None and last is None:
						if node.span[1] <= move_span[0]:
							already_here.append(node)
						if move_span[1] <= node.span[0]:
							already_here.append(node)
					if node.span[1] == nspan[1]:
						last = node
				info['adding node already present'] = False
				info['already here length'] = len(already_here)
				if len(already_here) == 1:
					if already_here[0].label == error[2]:
						info['adding node already present'] = True
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
				else:
					print "Unexpected..."

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
		yield gen_extra_successor(ctree, error, gold)

	# Move nodes
	spans = ctree.get_spans()
	for source_span in spans:
		# Consider all continuous sets of children
		source_span = source_span[2]
		for left in xrange(len(source_span.subtrees)):
			for right in xrange(left, len(source_span.subtrees)):
				if left == 0 and right == len(source_span.subtrees) - 1:
					# Note, this means in cases like (NP (NN blah)) we can't move the NN
					# out, we have to move the NP level.
					continue
				# If this series of nodes does not span the entire set of children
				if left != 0:
					# Consider moving down within this bracket
					pos = source_span.subtrees[left].span[0]
					for ans in gen_move_successors(pos, False, ctree, source_span, left, right, cerrors, gold):
						yield ans
				if right != len(source_span.subtrees) - 1:
					# Consider moving down within this bracket
					pos = source_span.subtrees[right].span[1]
					for ans in gen_move_successors(pos, True, ctree, source_span, left, right, cerrors, gold, True):
						yield ans
		
				# If source_span is extra
				if cerrors.is_extra(source_span):
					if left == 0:
						# Consider moving this set out to the left
						pos = source_span.subtrees[left].span[0]
						if pos > 0:
							for ans in gen_move_successors(pos, False, ctree, source_span, left, right, cerrors, gold):
								yield ans
						# Consider moving this set of spans up
						for ans in gen_move_successors(pos, True, ctree, source_span, left, right, cerrors, gold):
							yield ans
					elif right == len(source_span.subtrees) - 1:
						# Consider moving this set out to the right
						pos = source_span.subtrees[right].span[1]
						if pos < ctree.span[1]:
							for ans in gen_move_successors(pos, True, ctree, source_span, left, right, cerrors, gold):
								yield ans
						# Consider moving this set of spans up
						for ans in gen_move_successors(pos, False, ctree, source_span, left, right, cerrors, gold):
							yield ans

def greedy_search(gold, test, language='english'):
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
		cerrors = error_set.Error_Set()
		for error in ctree.get_errors(gold):
			cerrors.add_error(error[0], error[1], error[2], error[3])
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
		classify(step[1], language, gold, test)
	
	return (0, iters), path

def compare_trees(gold_tree, test_tree, out_dict, error_counts, language='english'):
	""" Compares two trees. """
	init_errors = test_tree.get_errors(gold_tree)
	error_count = len(init_errors)
	mprint("%d Initial errors" % error_count, out_dict, 'out')
	iters, path = greedy_search(gold_tree, test_tree, language)
	mprint("%d on fringe, %d iterations" % iters, out_dict, 'out')
	if path is not None:
		mprint(test_tree.__repr__(), out_dict, 'test_trees')
		mprint(gold_tree.__repr__(), out_dict, 'gold_trees')
		for tree in path[1:]:
			mprint(str(tree[2]) + " Error:" + tree[1]['classified_type'], out_dict, 'out')

		if len(path) > 1:
			for tree in path:
				mprint("Step:" + tree[1]['classified_type'], out_dict, 'out')
				error_counts[tree[1]['classified_type']].append(tree[2])
				mprint(tree[1].__repr__(), out_dict, 'out')
				mprint(render_tree.text_coloured_errors(tree[0], gold=gold_tree).strip(), out_dict, 'out')
	else:
		mprint("no path found", out_dict, 'out')

	mprint("", out_dict, ['out', 'err'])

def compare(gold_text, test_text, out_dict, error_counts, language='english'):
	""" Compares two trees in text form.
	This checks for empty trees and mismatched numbers
	of words.
	"""
	gold_text = gold_text.strip()
	test_text = test_text.strip()
	if len(gold_text) == 0:
		mprint("No gold tree", out_dict, ['out', 'err'])
		return
	elif len(test_text) == 0:
		mprint("Not parsed", out_dict, ['out', 'err'])
		return
	gold_tree = read_tree(gold_text, out_dict, 'gold')
	test_tree = read_tree(test_text, out_dict, 'test')
	if gold_tree is None or test_tree is None:
		mprint("Not parsed, but had output", out_dict, ['out', 'err', 'init_errors'])
		return
	mprint(render_tree.text_coloured_errors(test_tree, gold_tree).strip(), out_dict, 'init_errors')

	gold_words = gold_tree.word_yield()
	test_words = test_tree.word_yield()
	if len(test_words.split()) != len(gold_words.split()):
		mprint("Sentence lengths do not match...", out_dict, ['out', 'err'])
		mprint("Gold: " + gold_words.__repr__(), out_dict, ['out', 'err'])
		mprint("Test: " + test_words.__repr__(), out_dict, ['out', 'err'])
		return

	return compare_trees(gold_tree, test_tree, out_dict, error_counts, language)

def read_tree(text, out_dict, label):
	fake_file = StringIO(text)
	complete_tree = ptb.read_tree(fake_file)
	if complete_tree is None:
		return None
	ptb.homogenise_tree(complete_tree)
	if not complete_tree.label.strip():
		complete_tree.label = 'ROOT'
	tree = ptb.apply_collins_rules(complete_tree)
	if tree is None:
		mprint("Empty {} tree".format(label), out_dict, ['out', 'err'])
		mprint(complete_tree.__repr__(), out_dict, ['out', 'err'])
		mprint(tree.__repr__(), out_dict, ['out', 'err'])
	return tree

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

def get_out_dict():
	return {
		'out': sys.stdout,
		'err': sys.stderr,
		'gold_trees': sys.stdout,
		'test_trees': sys.stdout,
		'error_counts': sys.stdout
	}

if __name__ == '__main__':
	if len(sys.argv) < 3:
		print "Usage:"
		print "   %s <gold> <test> [-pre=<output_prefix> stdout by default] [-lang=ENG|CHI]" % sys.argv[0]
		print "Running doctest"
		import doctest
		doctest.testmod()
		sys.exit(0)

	out_dict = get_out_dict()
	if len(sys.argv) >= 4:
		for arg in sys.argv[3:]:
			if '-pre=' in arg:
				prefix = arg[5:]
				out_dict['out'] = open(prefix + '.out', 'w')
				out_dict['err'] = open(prefix + '.log', 'w')
				out_dict['gold_trees'] = open(prefix + '.gold_trees', 'w')
				out_dict['test_trees'] = open(prefix + '.test_trees', 'w')
				out_dict['error_counts'] = open(prefix + '.error_counts', 'w')
				out_dict['init_errors'] = open(prefix + '.init_errors', 'w')
				break
	
	language = 'english'
	if len(sys.argv) >= 4:
		for arg in sys.argv[3:]:
			if '-lang=' in arg:
				if 'CHI' in arg:
					language = 'chinese'
				elif 'ENG' in arg:
					language = 'english'
				else:
					raise Exception("Unknown Language")
				break

	mprint("Printing tree transformations", out_dict, ['out', 'err'])
	gold_in = open(sys.argv[1])
	test_in = open(sys.argv[2])
	sent_no = 0
	error_counts = defaultdict(lambda: [])
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

		mprint("Sentence %d:" % sent_no, out_dict, ['out', 'err', 'init_errors'])
		compare(gold_text.strip(), test_text.strip(), out_dict, error_counts, language)
		mprint("\n", out_dict, 'init_errors')
	counts_to_print = []
	for error in error_counts:
		if error == 'UNSET init':
			continue
		counts_to_print.append((len(error_counts[error]), sum(error_counts[error]), error))
	counts_to_print.sort(reverse=True)
	for error in counts_to_print:
		mprint("%d %d %s" % error, out_dict, ['error_counts'])


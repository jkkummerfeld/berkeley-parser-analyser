#!/usr/bin/env python

import ptb

def text_words(tree, span=None, pos=0, return_tuple=False):
	ans = ''
	if tree.word is not None:
		if span is None or span[0] <= pos < span[1]:
			ans = tree.word
		if return_tuple:
			ans = (pos + 1, ans)
	else:
		text = []
		for subtree in tree.subtrees:
			pos, words = text_words(subtree, span, pos, True)
			if words != '':
				text.append(words)
		ans = ' '.join(text)
		if return_tuple:
			ans = (pos, ans)
	return ans

def text_POS_tagged(tree, span=None, pos=0, return_tuple=False):
	ans = ''
	if tree.word is not None:
		if span is None or span[0] <= pos < span[1]:
			ans = tree.word + '|' + tree.label
		if return_tuple:
			ans = (pos + 1, ans)
	else:
		text = []
		for subtree in tree.subtrees:
			pos, words = text_POS_tagged(subtree, span, pos, True)
			if words != '':
				text.append(words)
		ans = ' '.join(text)
		if return_tuple:
			ans = (pos, ans)
	return ans

def text_tree(tree, single_line=True, depth=0):
	ans = ''
	if not single_line and depth > 0:
		ans = '\n' + depth * '\t'
	ans += '(' + tree.label
	if tree.word is not None:
		ans += ' ' + tree.word
	for subtree in tree.subtrees:
		if single_line:
			ans += ' '
		ans += text_tree(subtree, single_line, depth + 1)
	ans += ')'
	return ans

def text_ontonotes(tree, filename='filename', words=None, tree_text=None, depth=0):
	resolve = False
	if words is None:
		resolve = True
		words = []
		tree_text = ''

	if tree.word is None:
		tree_text += '(' + tree.label + '_'
	else:
		words.append((tree.word, tree.label))
		tree_text += '*'

	for subtree in tree.subtrees:
		tree_text = text_ontonotes(subtree, filename, words, tree_text, depth)

	if tree.word is None:
		tree_text += ')'

	if resolve:
		ans = ''
		cpos = 0
		cword = 0
		while cpos < len(tree_text):
			ctext = ''
			while cpos < len(tree_text) and tree_text[cpos] != '*':
				ctext += tree_text[cpos]
				cpos += 1
			ctext += tree_text[cpos]
			cpos += 1
			while cpos < len(tree_text) and tree_text[cpos] == ')':
				ctext += tree_text[cpos]
				cpos += 1
			ans += '%s %9s %9d %9s %9s %9s' % (filename, 0, cword, words[cword][0], words[cword][1], ctext)
			for val in ['-', '-', '-', '-', '*', '*', '*', '*', '*', '*', '-']:
				ans += ' %9s' % val
			ans += '\n'
			cword += 1
		return ans
	else:
		return tree_text

def tex_synttree(tree, other_spans=None, depth=0, compressed=True, span=None):
	if tree.label == '.':
		return ''
	if span is not None and (tree.span[1] <= span[0] or tree.span[0] >= span[1]):
		return ''
	correct = True
	if other_spans is not None:
		correct = (tree.label, tree.span[0], tree.span[1]) in other_spans
	else:
		compressed = False
	all_in_subtree = False
	if span is not None:
		for subtree in tree.subtrees:
			if subtree.span[0] <= span[0] and span[1] <= subtree.span[1]:
				all_in_subtree = True

	# Clean the label and word
	label = tree.label
	if '$' in label:
		label = '\$'.join(label.split('$'))
	word = tree.word
	if word is not None:
		word = ''.join(word.split('.'))
		word = '\&'.join(word.split('&'))
		word = '\$'.join(word.split('$'))

	# Make the text
	ans = ''
	if tree.parent is None:
		ans += '\synttree'
		if not all_in_subtree:
			ans += '\n'
	elif not all_in_subtree:
		ans += '\n' + '  ' * depth
	if len(tree.subtrees) == 0:
		ans += '[%s [%s]]' % (label, word)
	else:
		if not all_in_subtree:
			if correct:
				ans += '[%s' % (label)
			else:
				ans += '[\wrongnode{%s}' % (label)
		for subtree in tree.subtrees:
			ans += tex_synttree(subtree, other_spans, depth + 1, compressed, span)
		if not all_in_subtree:
			ans += ']'

	# When compressing we only want errors visible
	if compressed and 'wrongnode' not in ans and tree.word is None:
		words = ''.join(tree.word_yield().split('.'))
		words = '\&'.join(words.split('&'))
		words = '\$'.join(words.split('$'))
		if tree.parent is None:
			ans = '\synttree\n'
		else:
			ans = '\n' + '  ' * depth
		ans += '[%s [.t %s]]' % (label, words)
	return ans

def text_coloured_errors(tree, gold=None, depth=0, single_line=False, missing=None, extra=None, compressed=True, POS=True):
	'''Pretty print, with errors marked using colour.
	
	'missing' should contain tuples (or be None):
		(start, end, label, crossing-T/F)
	'''
	ans = ''
	if missing is None or extra is None:
		if gold is None:
			return "Error - no gold tree and no missing list for colour repr"
		# look at gold and work out what missing should be
		errors = tree.get_errors(gold, POS is not None)
		extra = [e[3] for e in errors if e[0] == 'extra' and e[3].word is None]
		extra = set(extra)
		missing = [(e[1][0], e[1][1], e[2], False) for e in errors if e[0] == 'missing' and e[3].word is None]
		missing += [(e[1][0], e[1][1], e[2], True) for e in errors if e[0] == 'crossing' and e[3].word is None]
		POS = [e for e in errors if e[0] == 'diff POS']
	start_missing = "\033[01;36m"
	start_extra = "\033[01;31m"
	start_crossing = "\033[01;33m"
	end_colour = "\033[00m"
	
	if not single_line:
		ans += '\n' + depth * '\t'

	# start of this
	if tree in extra:
		ans += start_extra + '(' + tree.label + end_colour
	elif tree.word is not None and POS is not None:
		found = False
		for error in POS:
			if error[3] == tree:
				found = True
				ans += '(' + start_missing + error[4] + end_colour
				ans += ' ' + start_extra + tree.label + end_colour
				break
		if not found:
			ans += '(' + tree.label
	else:
		ans += '(' + tree.label
	
	# If we are compressing, check for correctness and then just print words
	sub_done = False
	if compressed and tree not in extra and tree.word is None:
		all_right = True
		for error in extra:
			if tree.span[0] <= error.span[0] and error.span[1] <= tree.span[1]:
				all_right = False
				break
		for error in missing:
			if error[3]:
				if tree.span[0] < error[0] < tree.span[1]:
					all_right = False
					break
				if tree.span[0] < error[1] < tree.span[1]:
					all_right = False
					break
			elif tree.span[0] <= error[0] and error[1] <= tree.span[1]:
				all_right = False
				break
		if POS is not None:
			for error in POS:
				if tree.span[0] <= error[1][0] and error[1][1] <= tree.span[1]:
					all_right = False
					break
		if all_right:
			ans += ' ' + text_words(tree) + ')'
			sub_done = True

	# crossing brackets starting
	if tree.parent is None or tree.parent.subtrees[0] != tree:
		# these are marked as high as possible
		labels = []
		for error in missing:
			if error[0] == tree.span[0] and error[3]:
				labels.append((error[1], error[2]))
		labels.sort(reverse=True)
		if len(labels) > 0:
			to_add = start_crossing + ' '.join(['(' + label[1] for label in labels]) + end_colour
			if sub_done:
				nans = ''
				for char in ans:
					if char in '\t\n':
						nans += char
				clen = len(nans)
				nans += to_add
				nans += ' ' + ans[clen:]
				ans = nans
			else:
				ans += ' ' + to_add

	if not sub_done:
		# word
		if tree.word is not None:
			ans += ' ' + tree.word

		# subtrees
		below = []
		for subtree in tree.subtrees:
			text = text_coloured_errors(subtree, gold, depth + 1, single_line, missing, extra, compressed, POS)
			if single_line:
				text = ' ' + text
			below.append([subtree.span[0], subtree.span[1], text])
		# add missing brackets that surround subtrees
		for length in xrange(1, len(below)):
			for i in xrange(len(below)):
				j = i + length
				if i == 0 and j == len(below) - 1:
					continue
				if j >= len(below):
					break
				for error in missing:
					if below[i][0] == error[0] and below[j][1] == error[1] and not error[3]:
						start = ''
						for char in below[i][2]:
							if char not in '\n\t':
								break
							start += char
						for k in xrange(i, j+1):
							below[k][2] = '\n\t'.join(below[k][2].split('\n'))
						below[i][2] = start + start_missing + '(' + error[2] + end_colour + below[i][2]
						below[j][2] += start_missing + ')' + end_colour
		ans += ''.join([part[2] for part in below])

		# end of this
		if tree in extra:
			ans += start_extra + ')' + end_colour
		else:
			ans += ')'

	if tree.parent is None or tree.parent.subtrees[-1] != tree:
		# if there are crossing brackets that end here, mark that
		labels = []
		for error in missing:
			if error[1] == tree.span[1] and error[3]:
				labels.append((-error[0], error[2]))
		labels.sort()
		if len(labels) > 0:
			ans += ' ' + start_crossing + ' '.join([label[1] + ')' for label in labels]) + end_colour

	if tree.parent is None or len(tree.parent.subtrees) > 1:
		# check for missing brackets that go around this node
		for error in missing:
			if error[0] == tree.span[0] and error[1] == tree.span[1] and not error[3]:
				if not tree in extra:
					# Put them on a new level
					extra_text = ''
					if not single_line:
						ans = '\n\t'.join(ans.split('\n'))
						extra_text = '\n' + depth * '\t'
					extra_text += start_missing + '(' + error[2] + end_colour
					if single_line:
						ans = ' ' + ans
					ans = extra_text + ans
					ans += start_missing + ')' + end_colour
				else:
					# Put them on the same line
					start = 0
					for char in ans:
						if char not in '\n\t':
							break
						start += 1
					pretext = ans[:start]
					ans = ans[start:]
					extra_text = start_missing + '(' + error[2] + end_colour + ' '
					ans = pretext + extra_text + ans
					ans += start_missing + ')' + end_colour
	return ans

def cut_text_below(text, depth):
	'''Simplify text to only show the top parts of a tree
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 1)
	(ROOT)
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 2)
	(ROOT (NP) (VP))
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 3)
	(ROOT (NP (PRP I)) (VP (VBD ran) (NP)))
	>>> print cut_text_below("(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))", 20)
	(ROOT (NP (PRP I)) (VP (VBD ran) (NP (NN home))))
	'''

	# Cut lower content
	cdepth = 0
	ntext = ''
	for char in text:
		if char == '(':
			cdepth += 1
		if cdepth <= depth:
			ntext += char
		if char == ')':
			cdepth -= 1

	# Walk back and remove extra whitespace
	text = ntext
	ntext = ''
	ignore = False
	for char in text[::-1]:
		if char == ')':
			ignore = True
			ntext += char
		elif ignore:
			if char != ' ':
				ntext += char
				ignore = False
		else:
			ntext += char
	return ntext[::-1]

if __name__ == '__main__':
	print "Running doctest"
	import doctest
	doctest.testmod()


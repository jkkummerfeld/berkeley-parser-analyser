#!/usr/bin/env python

import sys
from collections import defaultdict

word_to_word_mapping = {
	'{': '-LCB-',
	'}': '-RCB-'
}
word_to_POS_mapping = {
	'--': ':',
	'-': ':',
	';': ':',
	':': ':',
	'-LRB-': '-LRB-',
	'-RRB-': '-RRB-',
	'-LCB-': '-LRB-',
	'-RCB-': '-RRB-',
	'{': '-LRB-',
	'}': '-RRB-',
	'Wa': 'NNP'
}
tag_set = set(['S', 'SBAR', 'SBARQ', 'SINV', 'SQ', 'ADJP', 'ADVP', 'CONJP',
'FRAG', 'INTJ', 'LST', 'NAC', 'NP', 'NX', 'PP', 'PRN', 'PRT', 'QP', 'RRC',
'UCP', 'VP', 'WHADJP', 'WHADVP', 'WHNP', 'WHPP', 'X'])
def standardise_node(tree):
	if tree.word in word_to_word_mapping:
		tree.word = word_to_word_mapping[tree.word]
	if tree.word in word_to_POS_mapping:
		tree.label = word_to_POS_mapping[tree.word]

class TreeIterator:
	'''Iterator for post-order traversal of a tree'''

	def __init__(self, tree):
		self.tree = tree
		self.pos = [0]
	
	def next(self):
		if len(self.pos) == 0:
			raise StopIteration
		if self.pos[-1] < len(self.tree.subtrees):
			self.tree = self.tree.subtrees[self.pos[-1]]
			self.pos[-1] += 1
			self.pos.append(0)
			return self.next()
		else:
			ans = self.tree
			self.tree = self.tree.parent
			self.pos.pop()
			return ans

class PTB_Tree:
	'''Tree for PTB format

	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (NP (NNP Newspaper)))")
	>>> print tree
	(ROOT (NP (NNP Newspaper)))
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))")
	>>> print tree
	(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti))) (. .)))
	>>> print tree.word_yield()
	Ms. Haag plays Elianti .
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (NFP ...))")
	>>> print tree
	(ROOT (NFP ...))
	>>> tree.word_yield()
	'...'
	'''
# Convert text from the PTB to a tree. For example:
# ( (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))
# This is a compressed form of:
# ( (S 
#     (NP-SBJ (NNP Ms.) (NNP Haag))
#     (VP (VBZ plays) 
#       (NP (NNP Elianti)))
#     (. .)))
	def __init__(self):
		self.subtrees = []
		self.word = None
		self.label = ''
		self.parent = None
		self.span = (-1, -1)
	
	def __iter__(self):
		return TreeIterator(self)

	def set_by_spans(self, spans, words):
		spans = [(span[1] - span[0], span) for span in spans]
		spans.sort(reverse=True)
		cspan = spans[0]
		for span in spans:
			if span[0] != cspan[0]:
				break
			if span[1][2] == 'ROOT':
				cspan = span
			elif span[1][2] in tag_set:
				cspan = span
		spans.remove(cspan)
		self.span = (cspan[1][0], cspan[1][1])
		self.label = cspan[1][2]
		if len(spans) == 0:
			# terminal
			self.word = words[self.span[0]]
		else:
			# non-terminal
			subspans = []
			cur = self.span[0]
			while cur != self.span[1]:
				# Find the longest starting at cur
				largest = (-1, None)
				for span in spans:
					if span[1][0] == cur and span[0] > largest[0]:
						largest = span

				# Find all spans that fit within this
				largest = largest[1]
				new_set = []
				for span in spans:
					if largest[0] <= span[1][0] and span[1][1] <= largest[1]:
						new_set.append(span[1])
				subtree = PTB_Tree()
				subtree.parent = self
				subtree.set_by_spans(new_set, words)
				self.subtrees.append(subtree)
				cur = largest[1]

	def set_by_text(self, text, pos=0, left=0):
		depth = 0
		right = left
		for i in xrange(pos + 1, len(text)):
			char = text[i]
			# we've reached the end of the category that is the root of this subtree
			if depth == 0 and char in ' (' and self.label == '':
				self.label = text[pos + 1:i]
				if '|' in self.label:
					if 'ADVP' in self.label:
						self.label = 'ADVP'
					else:
						self.label = self.label.split('|')[0]

			# update the depth
			if char == '(':
				depth += 1
				if depth == 1:
					subtree = PTB_Tree()
					subtree.parent = self
					subtree.set_by_text(text, i, right)
					right = subtree.span[1]
					self.span = (left, right)
					self.subtrees.append(subtree)
			elif char == ')':
				depth -= 1
				if len(self.subtrees) == 0:
					pos = i
					for j in xrange(i, 0, -1):
						if text[j] == ' ':
							pos = j
							break
					self.word = text[pos + 1:i]
					self.span = (left, left + 1)
			
			# we've reached the end of the scope for this bracket
			if depth < 0:
				break

		# Fix some issues with variation in output, and one error in the treebank
		# for a word with a punctuation POS
		standardise_node(self)
	
	def clone(self):
		ans = PTB_Tree()
		ans.word = self.word
		ans.label = self.label
		ans.parent = None
		ans.span = self.span
		ans.subtrees = []
		for subtree in self.subtrees:
			ans.subtrees.append(subtree.clone())
			ans.subtrees[-1].parent = ans
		return ans

	def get_root(self):
		if self.parent is not None:
			return self.parent.get_root()
		else:
			return self

	def production_list(self, ans=None):
		if ans is None:
			ans = []
		if len(self.subtrees) > 0:
			cur = (self.label, (self.span[0], self.span[1]),
			       tuple([(sub.label, sub.span[1]) for sub in self.subtrees]))
			ans.append(cur)
			for sub in self.subtrees:
				sub.production_list(ans)
		return ans

	def word_yield(self, span=None, pos=-1, as_list=False):
		return_tuple = True
		if pos < 0:
			pos = 0
			return_tuple = False
		ans = None
		if self.word is not None:
			if span is None or span[0] <= pos < span[1]:
				ans = (pos + 1, self.word)
			else:
				ans = (pos + 1, '')
			if as_list:
				ans = (ans[0], [ans[1]])
		else:
			text = []
			for subtree in self.subtrees:
				pos, words = subtree.word_yield(span, pos, as_list)
				if words != '' and len(words) > 0:
					if as_list:
						text += words
					else:
						text.append(words)
			ans = (pos, ' '.join(text))
			if as_list:
				ans = (pos, text)
		if return_tuple:
			return ans
		else:
			return ans[1]

	def __repr__(self, single_line=True, depth=0, include_POS=True):
		ans = ''
		if not single_line and depth > 0:
			ans = '\n' + depth * '\t'
		if self.word is None:
			ans += '(' + self.label
		else:
			ans += '('
			if include_POS:
				ans += self.label + ' '
			ans += self.word
		for subtree in self.subtrees:
			if single_line:
				ans += ' '
			ans += subtree.__repr__(single_line, depth + 1, include_POS)
		ans += ')'
		return ans

	def calculate_spans(self, left=0):
		right = left
		if self.word is not None:
			right += 1
		else:
			for subtree in self.subtrees:
				right = subtree.calculate_spans(right)
		self.span = (left, right)
		return right

	def check_consistency(self):
		if len(self.subtrees) > 0:
			for subtree in self.subtrees:
				if subtree.parent != self:
					print "bad parent link"
					print id(self), id(subtree.parent), id(subtree)
					print subtree
					return False
				if not subtree.check_consistency():
					return False
			if self.span[0] != self.subtrees[0].span[0]:
				print "incorrect span"
				return False
			if self.span[1] != self.subtrees[-1].span[1]:
				print "incorrect span"
				return False
		return True
	
	def span_list(self, span_list=None):
		'''Get a list of spans.  In general try to use the iterator instead.'''
		if span_list is None:
			span_list = []
		for subtree in self.subtrees:
			subtree.span_list(span_list)
		span_list.append((self.span[0], self.span[1], self))
		return span_list

	def span_dict(self, span_dict=None):
		'''Get a dictionary of labelled spans. Note that we use a dictionary to
		take into consideration unaries like (NP (NP ...))'''
		if span_dict is None:
			span_dict = defaultdict(lambda: 0)
		for subtree in self.subtrees:
			subtree.span_dict(span_dict)
		span_dict[(self.label, self.span[0], self.span[1])] += 1
		return span_dict

	def get_lowest_span(self, start=-1, end=-1):
		if start <= end < 0:
			return None
		for subtree in self.subtrees:
			if end != -1 and end <= subtree.span[0]:
				break
			if end <= subtree.span[1] or end < 0:
				if subtree.span[0] <= start or start < 0:
					ans = subtree.get_lowest_span(start, end)
					if ans is not None:
						return ans
		if self.span[1] == end or end < 0:
			if self.span[0] == start or start < 0:
				return self
		return None

	def get_highest_span(self, start=-1, end=-1):
		if start <= end < 0:
			return None
		if self.span[1] == end or end < 0:
			if self.span[0] == start or start < 0:
				return self
		for subtree in self.subtrees:
			if end != -1 and end <= subtree.span[0]:
				break
			if end <= subtree.span[1] or end < 0:
				if subtree.span[0] <= start or start < 0:
					ans = subtree.get_highest_span(start, end)
					if ans is not None:
						return ans
		return None

	def get_spans(self, start=-1, end=-1, span_list=None):
		if start <= end < 0:
			return self.span_list()
		if span_list is None:
			span_list = []
		for subtree in self.subtrees:
			if end != -1 and end <= subtree.span[0]:
				break
			if end <= subtree.span[1] or end < 0:
				if subtree.span[0] <= start or start < 0:
					subtree.get_spans(start, end, span_list)
		if self.span[1] == end or end < 0:
			if self.span[0] == start or start < 0:
				span_list.append((self.span[0], self.span[1], self))
		return span_list

	def get_matching_node(self, node):
		'''Find a node with the same span, label and number of children.'''
		if node.span == self.span:
			if node.label == self.label:
				if len(self.subtrees) == len(node.subtrees):
					return self
			return self.subtrees[0].get_matching_node(node)
		else:
			for subtree in self.subtrees:
				if subtree.span[0] <= node.span[0] and node.span[1] <= subtree.span[1]:
					return subtree.get_matching_node(node)
			return None

	def get_errors(self, gold, include_POS=False):
		ans = []
		gold_spans = gold.span_list()
		test_spans = self.span_list()
		gold_spans.sort()
		test_spans.sort()
		test_span_set = {}
		for span in test_spans:
			key = (span[0], span[1], span[2].label) 
			if key not in test_span_set:
				test_span_set[key] = 0
			test_span_set[key] += 1
		gold_span_set = {}
		for span in gold_spans:
			key = (span[0], span[1], span[2].label) 
			if key not in gold_span_set:
				gold_span_set[key] = 0
			gold_span_set[key] += 1

		# Different POS
		if include_POS:
			for tnode in self:
				if tnode.word is not None:
					for gnode in gold:
						if gnode.word is not None and gnode.span == tnode.span:
							if gnode.label != tnode.label:
								ans.append(('diff POS', tnode.span, tnode.label, tnode, gnode.label))

		# Extra
		for span in test_spans:
			key = (span[0], span[1], span[2].label)
			if key not in gold_span_set or gold_span_set[key] < 1:
				if span[2].word is None:
					ans.append(('extra', (span[0], span[1]), span[2].label, span[2]))
			else:
				gold_span_set[key] -= 1

		# Missing and crossing
		for span in gold_spans:
			key = (span[0], span[1], span[2].label)
			if key not in test_span_set or test_span_set[key] < 1:
				if span[2].word is not None:
					continue
				is_crossing = False
				for tspan in test_span_set:
					if tspan[0] < span[0] < tspan[1] < span[1]:
						is_crossing = True
						break
					if span[0] < tspan[0] < span[1] < tspan[1]:
						is_crossing = True
						break
				name = 'crossing' if is_crossing else 'missing'
				ans.append((name, (span[0], span[1]), span[2].label, span[2]))
			else:
				test_span_set[key] -= 1
		return ans

def remove_trivial_unaries(tree, left=-1):
	if left < 0:
		left = tree.span[0]
	if len(tree.subtrees) == 1 and tree.label == tree.subtrees[0].label:
		return remove_trivial_unaries(tree.subtrees[0], left)
	right = left
	if tree.word is not None:
		right = left + 1
	subtrees = []
	for subtree in tree.subtrees:
		nsubtree = remove_trivial_unaries(subtree, right)
		if nsubtree != None:
			subtrees.append(nsubtree)
			right = nsubtree.span[1]
	if tree.word is None and len(subtrees) == 0:
		return None
	ans = PTB_Tree()
	ans.word = tree.word
	ans.label = tree.label
	ans.span = (left, right)
	ans.subtrees = subtrees
	for subtree in subtrees:
		subtree.parent = ans
	return ans

def remove_traces(tree, left=0):
	'''Adjust the tree to remove traces
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (PP (IN By) (NP (CD 1997))) (, ,) (NP (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed) (NP (-NONE- *-6))))) (. .)))")
	>>> ctree = remove_traces(tree)
	>>> print ctree
	(ROOT (S (PP (IN By) (NP (CD 1997))) (, ,) (NP (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed)))) (. .)))
	'''
	if tree.label == '-NONE-':
		return None
	right = left
	if tree.word is not None:
		right = left + 1
	subtrees = []
	for subtree in tree.subtrees:
		nsubtree = remove_traces(subtree, right)
		if nsubtree != None:
			subtrees.append(nsubtree)
			right = nsubtree.span[1]
	if tree.word is None and len(subtrees) == 0:
		return None
	ans = PTB_Tree()
	ans.word = tree.word
	ans.label = tree.label
	ans.span = (left, right)
	ans.subtrees = subtrees
	for subtree in subtrees:
		subtree.parent = ans
	return ans

def remove_function_tags(tree):
	'''Adjust the tree to remove function tags on labels
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti))) (. .)))")
	>>> ctree = remove_function_tags(tree)
	>>> print ctree
	(ROOT (S (NP (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti))) (. .)))

	# don't remove brackets
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP-SBJ (`` ``) (NP-TTL (NNP Funny) (NNP Business)) ('' '') (PRN (-LRB- -LRB-) (NP (NNP Soho)) (, ,) (NP (CD 228) (NNS pages)) (, ,) (NP ($ $) (CD 17.95)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP-PRD (NP (NN anything)) (PP (RB but)))) (. .)))")
	>>> ctree = remove_function_tags(tree)
	>>> print ctree
	(ROOT (S (NP (`` ``) (NP (NNP Funny) (NNP Business)) ('' '') (PRN (-LRB- -LRB-) (NP (NNP Soho)) (, ,) (NP (CD 228) (NNS pages)) (, ,) (NP ($ $) (CD 17.95)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP (NP (NN anything)) (PP (RB but)))) (. .)))
	'''
	ans = PTB_Tree()
	ans.word = tree.word
	ans.label = tree.label
	if len(ans.label) > 0 and ans.label[0] != '-':
		ans.label = ans.label.split('-')[0]
	ans.label = ans.label.split('=')[0]
	ans.span = (tree.span[0], tree.span[1])
	ans.subtrees = []
	for subtree in tree.subtrees:
		nsubtree = remove_function_tags(subtree)
		ans.subtrees.append(nsubtree)
		nsubtree.parent = ans
	return ans

# Applies rules to strip out the parts of the tree that are not used in the
# standard evalb evaluation
labels_to_ignore = set(["-NONE-",",",":","``","''","."])
words_to_ignore = set([])
#words_to_ignore = set(["'","`","''","``","--",":",";","-",",",".","...",".","?","!"])
POS_to_convert = {'PRT': 'ADVP'}
def apply_collins_rules(tree, left=0):
	'''Adjust the tree to remove parts not evaluated by the standard evalb
	config.

	# cutting punctuation and -X parts of labels
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))")
	>>> ctree = apply_collins_rules(tree)
	>>> print ctree
	(ROOT (S (NP (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti)))))
	>>> print ctree.word_yield()
	Ms. Haag plays Elianti

	# cutting nulls
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (PP-TMP (IN By) (NP (CD 1997))) (, ,) (NP-SBJ-6 (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed) (NP (-NONE- *-6))))) (. .)))")
	>>> ctree = apply_collins_rules(tree)
	>>> print ctree
	(ROOT (S (PP (IN By) (NP (CD 1997))) (NP (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed))))))

	# changing PRT to ADVP
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP-SBJ-41 (DT That) (NN fund)) (VP (VBD was) (VP (VBN put) (NP (-NONE- *-41)) (PRT (RP together)) (PP (IN by) (NP-LGS (NP (NNP Blackstone) (NNP Group)) (, ,) (NP (DT a) (NNP New) (NNP York) (NN investment) (NN bank)))))) (. .)))")
	>>> ctree = apply_collins_rules(tree)
	>>> print ctree
	(ROOT (S (NP (DT That) (NN fund)) (VP (VBD was) (VP (VBN put) (ADVP (RP together)) (PP (IN by) (NP (NP (NNP Blackstone) (NNP Group)) (NP (DT a) (NNP New) (NNP York) (NN investment) (NN bank))))))))

	# not removing brackets
	>>> tree = PTB_Tree()
	>>> tree.set_by_text("(ROOT (S (NP-SBJ (`` ``) (NP-TTL (NNP Funny) (NNP Business)) ('' '') (PRN (-LRB- -LRB-) (NP (NNP Soho)) (, ,) (NP (CD 228) (NNS pages)) (, ,) (NP ($ $) (CD 17.95) (-NONE- *U*)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP-PRD (NP (NN anything)) (PP (RB but) (NP (-NONE- *?*))))) (. .)))")
	>>> ctree = apply_collins_rules(tree)
	>>> print ctree
	(ROOT (S (NP (NP (NNP Funny) (NNP Business)) (PRN (-LRB- -LRB-) (NP (NNP Soho)) (NP (CD 228) (NNS pages)) (NP ($ $) (CD 17.95)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP (NP (NN anything)) (PP (RB but))))))
	'''
	if tree.label in labels_to_ignore:
		return None
	if tree.word in words_to_ignore:
		return None
	ans = PTB_Tree()
	ans.word = tree.word
	ans.label = tree.label
	ans.span = (left, -1)
	right = left
	if ans.word is not None:
		right = left + 1
		ans.span = (left, right)
	subtrees = []
	ans.subtrees = subtrees
	for subtree in tree.subtrees:
		nsubtree = apply_collins_rules(subtree, right)
		if nsubtree != None:
			subtrees.append(nsubtree)
			nsubtree.parent = ans
			right = nsubtree.span[1]
	ans.span = (left, right)
	if ans.word is None and len(ans.subtrees) == 0:
		return None
	if ans.label in POS_to_convert:
		ans.label = POS_to_convert[ans.label]
	try:
		if not ans.label[0] == '-':
			ans.label = ans.label.split('-')[0]
	except:
		raise Exception("Collins rule application issue:" + str(tree.get_root()))
	ans.label = ans.label.split('=')[0]
	return ans

def homogenise_tree(tree):
	if tree.label != 'ROOT':
		while tree.label not in tag_set:
			if len(tree.subtrees) > 1:
				break
			elif len(tree.subtrees) == 0:
				tree.label = 'ROOT'
				return tree
			tree = tree.subtrees[0]
		if tree.label not in tag_set:
			tree.label = 'ROOT'
		else:
			root = PTB_Tree()
			root.subtrees.append(tree)
			root.label = 'ROOT'
			root.span = tree.span
			tree.parent = root
			tree = root
	return tree

def read_tree(source, return_empty=False, input_format='ptb', homogenise=True):
	'''Read a single tree from the given file.
	
	>>> from StringIO import StringIO
	>>> file_text = """(ROOT (S
	...   (NP-SBJ (NNP Scotty) )
	...   (VP (VBD did) (RB not)
	...     (VP (VB go)
	...       (ADVP (RB back) )
	...       (PP (TO to)
	...         (NP (NN school) ))))
	...   (. .) ))"""
	>>> in_file = StringIO(file_text)
	>>> tree = read_tree(in_file)
	>>> print tree
	(ROOT (S (NP-SBJ (NNP Scotty)) (VP (VBD did) (RB not) (VP (VB go) (ADVP (RB back)) (PP (TO to) (NP (NN school))))) (. .)))'''
	cur_text = []
	depth = 0 if input_format == 'ptb' else -1
	while True:
		line = source.readline()
		# Check if we are out of input
		if line == '':
			return None
		# strip whitespace and only use if this contains something
		line = line.strip()
		if line == '':
			# Check for OntoNotes style input
			if input_format == 'ontonotes':
				text = ''
				for line in cur_text:
					if len(line) == 0 or line[0] == '#':
						continue
					line = line.split()
					word = line[3]
					pos = line[4]
					tree = line[5]
					tree = tree.split('*')
					text += '%s(%s %s)%s' % (tree[0], pos, word, tree[1])
				text = ' '.join(text.split('_')).strip()
				tree = PTB_Tree()
				tree.set_by_text(text)
				tree.label = 'ROOT'
				if homogenise:
					tree = homogenise_tree(tree)
				return tree
			elif return_empty:
				return "Empty"
			continue
		cur_text.append(line)

		# Update depth
		if depth >= 0:
			for char in line:
				if char == '(':
					depth += 1
				elif char == ')':
					depth -= 1

		# PTB style - At depth 0 we have a complete tree
		if depth == 0:
			cur_text = ' '.join(cur_text)
			if '()' in cur_text:
				cur_text = []
				if return_empty:
					return "Empty"
				continue
			tree = PTB_Tree()
			tree.set_by_text(cur_text)
			if homogenise:
				tree = homogenise_tree(tree)
			return tree
	return None

def generate_trees(source, max_sents=-1, return_empty=False, input_format='ptb', homogenise=True):
	'''Read trees from the given file (opening the file if only a string is given).

	This version is a generator, yielding one tree at a time.
	
	>>> from StringIO import StringIO
	>>> file_text = """(ROOT (S
	...   (NP-SBJ (NNP Scotty) )
	...   (VP (VBD did) (RB not)
	...     (VP (VB go)
	...       (ADVP (RB back) )
	...       (PP (TO to)
	...         (NP (NN school) ))))
	...   (. .) ))
	...
	... (ROOT (S 
	... 		(NP-SBJ (DT The) (NN bandit) )
	... 		(VP (VBZ laughs) 
	... 			(PP (IN in) 
	... 				(NP (PRP$ his) (NN face) )))
	... 		(. .) ))"""
	>>> in_file = StringIO(file_text)
	>>> for tree in generate_trees(in_file):
	...   print tree
	(ROOT (S (NP-SBJ (NNP Scotty)) (VP (VBD did) (RB not) (VP (VB go) (ADVP (RB back)) (PP (TO to) (NP (NN school))))) (. .)))
	(ROOT (S (NP-SBJ (DT The) (NN bandit)) (VP (VBZ laughs) (PP (IN in) (NP (PRP$ his) (NN face)))) (. .)))'''
	if type(source) == type(''):
		source = open(source)
	count = 0
	while True:
		tree = read_tree(source, return_empty, input_format, homogenise)
		if tree == "Empty":
			yield None
			continue
		if tree is None:
			return
		yield tree
		count += 1
		if count >= max_sents > 0:
			return

def read_trees(source, max_sents=-1, return_empty=False, input_format='ptb'):
	return [tree for tree in generate_trees(source, max_sents, return_empty, input_format)]

def counts_for_prf(test, gold):
	test_spans = [span for span in test.span_list() if span[2].word is None]
	gold_spans = [span for span in gold.span_list() if span[2].word is None]
	# -1 for the top node
	test_count = len(test_spans) - 1
	gold_count = len(gold_spans) - 1
	errors = test.get_errors(gold)
	tmatch = test_count
	gmatch = gold_count
	for error in errors:
		if error[0] == 'extra':
			tmatch -= 1
		else:
			gmatch -= 1
	return tmatch, gold_count, test_count

if __name__ == '__main__':
	print "Running doctest"
	import doctest
	doctest.testmod()


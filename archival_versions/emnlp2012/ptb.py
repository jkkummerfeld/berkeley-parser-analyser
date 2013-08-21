#!/usr/bin/env python

import sys

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
def standardise_node(tree):
	if tree.word in word_to_word_mapping:
		tree.word = word_to_word_mapping[tree.word]
	if tree.word in word_to_POS_mapping:
		tree.label = word_to_POS_mapping[tree.word]
	
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
	
	def set_by_text(self, text, pos=0):
		depth = 0
		for i in xrange(pos + 1, len(text)):
			char = text[i]
			# update the depth
			if char == '(':
				depth += 1
				if depth == 1:
					subtree = PTB_Tree()
					subtree.set_by_text(text, i)
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
			
			# we've reached the end of the category that is the root of this subtree
			if depth == 0 and char == ' ' and self.label == '':
				self.label = text[pos + 1:i]
			# we've reached the end of the scope for this bracket
			if depth < 0:
				break

		# Fix some issues with variation in output, and one error in the treebank
		# for a word with a punctuation POS
		standardise_node(self)
	
	def word_yield(self, span=None, pos=-1):
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
		else:
			text = []
			for subtree in self.subtrees:
				pos, words = subtree.word_yield(span, pos)
				if words != '':
					text.append(words)
			ans = (pos, ' '.join(text))
		if return_tuple:
			return ans
		else:
			return ans[1]

	def __repr__(self, single_line=True, depth=0):
		ans = ''
		if not single_line and depth > 0:
			ans = '\n' + depth * '\t'
		ans += '(' + self.label
		if self.word is not None:
			ans += ' ' + self.word
		for subtree in self.subtrees:
			if single_line:
				ans += ' '
			ans += subtree.__repr__(single_line, depth + 1)
		ans += ')'
		return ans

# Applies rules to strip out the parts of the tree that are not used in the
# standard evalb evaluation
labels_to_ignore = set(["-NONE-", "TOP"])
words_to_ignore = set(["'","`","''","``","--",":",";","-",",",".","...",".","?","!"])
POS_to_convert = {'PRT': 'ADVP'}
def apply_collins_rules(tree):
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
	subtrees = []
	for subtree in tree.subtrees:
		nsubtree = apply_collins_rules(subtree)
		if nsubtree != None:
			subtrees.append(nsubtree)
	if tree.word is None and len(subtrees) == 0:
		return None
	ans = PTB_Tree()
	ans.word = tree.word
	ans.label = tree.label
	ans.subtrees = subtrees
	if ans.label in labels_to_ignore:
		return None
	if ans.word in words_to_ignore:
		return None
	if ans.label in POS_to_convert:
		ans.label = POS_to_convert[ans.label]
	if not ans.label[0] == '-':
		ans.label = ans.label.split('-')[0]
	ans.label = ans.label.split('=')[0]
	return ans

def read_tree(source):
	cur_text = []
	depth = 0
	while True:
		line = source.readline()
		# Check if we are out of input
		if line == '':
			return None
		# strip whitespace and only use if this contains something
		line = line.strip()
		if line == '':
			continue
		cur_text.append(line)
		# Update depth
		for char in line:
			if char == '(':
				depth += 1
			elif char == ')':
				depth -= 1
		# At depth 0 we have a complete tree
		if depth == 0:
			tree = PTB_Tree()
			tree.set_by_text(' '.join(cur_text))
			return tree
	return None

def read_trees(source, max_sents=-1):
	if type(source) == type(''):
		source = open(source)
	trees = []
	while True:
		tree = read_tree(source)
		if tree is None:
			break
		trees.append(tree)
		if len(trees) >= max_sents > 0:
			break
	return trees

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print "Usage:\n%s <filename>" % sys.argv[0]
		print "Running doctest"
		import doctest
		doctest.testmod()
	else:
		filename = sys.argv[1]
		trees = read_PTB_trees(filename)
		print len(trees), "trees read from", filename
		for tree in trees:
			print tree

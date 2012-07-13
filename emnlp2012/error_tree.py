#!/usr/bin/env python

import sys
import ptb

class Error_Tree:
	'''A tree that can track errors and supports modifications to fix errors
	'''

	def __init__(self):
		'''Main constructor, sets all fields.

		>>> etree = Error_Tree()
		>>> print etree
		()
		'''
		self.label = ''
		self.word = None
		self.subtrees = []
		self.parent = None
		self.span = (-1, -1)

		self.basis_tree = None
		self.pre_collins_tree = None

		# if this is an extra node, include a list of gold spans that start or end
		# within it
		self.extra = False
		self.crossing_starts = []
		self.crossing_ends = []

	def set_by_ptb(self, ptb, pre_collins, init=0, parent=None):
		'''Use a PTB_Tree to set fields for this node and construct subtrees.

		>>> tree = ptb.PTB_Tree()
		>>> tree.set_by_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))")
		>>> pcollins = tree
		>>> tree = ptb.apply_collins_rules(tree)
		>>> etree = Error_Tree()
		>>> etree.set_by_ptb(tree, pcollins)
		>>> print etree
		(ROOT (S (NP (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti)))))
		>>> etree.check_consistency()
		'''
		self.pre_collins_tree = pre_collins
		self.label = None
		self.word = ptb.word
		self.subtrees = []
		self.parent = parent
		self.label = ptb.label
		self.basis_tree = ptb
		final = init
		for tree in ptb.subtrees:
			sub = Error_Tree()
			sub.set_by_ptb(tree, pre_collins, final, self)
			self.subtrees.append(sub)
			final = sub.span[1]
		if self.word is not None:
			final += 1
		self.span = (init, final)

	def copy(self, parent=None):
		'''Construct a copy, including subtrees.

		>>> tree = ptb.PTB_Tree()
		>>> tree.set_by_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))")
		>>> pcollins = tree
		>>> tree = ptb.apply_collins_rules(tree)
		>>> etree = Error_Tree()
		>>> etree.set_by_ptb(tree, pcollins)
		>>> etree.check_consistency()
		>>> copy = etree.copy()
		>>> assert copy != etree
		>>> for subtree in copy.subtrees:
		...   assert subtree not in etree.subtrees
		...   for subsubtree in subtree.subtrees:
		...     for other in etree.subtrees:
		...       assert subsubtree not in other.subtrees
		'''
		copy = Error_Tree()
		copy.label = self.label
		copy.word = self.word
		copy.parent = parent
		copy.span = (self.span[0], self.span[1])
		copy.extra = self.extra
		copy.crossing_starts = self.crossing_starts[:]
		copy.crossing_ends = self.crossing_ends[:]
		copy.basis_tree = self

		copy.subtrees = []
		for subtree in self.subtrees:
			copy.subtrees.append(subtree.copy(copy))
		return copy

	def update_span(self, init=0):
		'''Update span values to match the size of subtrees.'''
		if self.word is not None:
			self.span = (init, init + 1)
		else:
			pos = init
			for subtree in self.subtrees:
				subtree.update_span(pos)
				pos = subtree.span[1]
			self.span = (init, pos)

	def check_parent(self):
		'''Check that the children of this node consider it their parent (and so on
		for subtrees).'''
		for subtree in self.subtrees:
			if subtree.parent != self:
				print "Parent error"
				print self
				print subtree
				print subtree.parent
			subtree.check_parent()
	def check_span(self, init=0):
		'''Check that the current span values for this node match the size of the
		subtree beneath it (and so on for subtrees).'''
		if self.word is not None:
			span = (init, init + 1)
		else:
			pos = init
			for subtree in self.subtrees:
				subtree.update_span(pos)
				pos = subtree.span[1]
			span = (init, pos)
		if self.span != span:
			print "Span error", self.span, "instead of", span
			print self
	def check_consistency(self):
		'''Since we will be messing around with these trees, creating and removing
		nodes, it is useful to have quick checks of consistency.

		>>> tree = ptb.PTB_Tree()
		>>> tree.set_by_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))")
		>>> pcollins = tree
		>>> tree = ptb.apply_collins_rules(tree)
		>>> etree = Error_Tree()
		>>> etree.set_by_ptb(tree, pcollins)
		>>> etree.check_consistency()
		>>> copy = etree.copy()
		>>> a = copy.subtrees[0].subtrees.pop(0)
		>>> print copy
		(ROOT (S (VP (VBZ plays) (NP (NNP Elianti)))))
		>>> copy.check_consistency()
		Span error (0, 4) instead of (0, 2)
		(ROOT (S (VP (VBZ plays) (NP (NNP Elianti)))))
		>>> copy.update_span()
		>>> copy.check_consistency()
		'''
		self.check_parent()
		self.check_span()
	
	def get_span(self, span):
		'''Get a list of nodes that match the given span.'''
		if span[0] == self.span[0] and span[1] == self.span[1]:
			ans = []
			if len(self.subtrees) == 1:
				ans = self.subtrees[0].get_span(span)
			ans.insert(0, self)
			return ans
		for subtree in self.subtrees:
			if subtree.span[0] <= span[0] and span[1] <= subtree.span[1]:
				return subtree.get_span(span)
		return None
	
	def get_copy(self, original):
		'''Find the subtree that was constructed based on the argument.

		>>> tree = ptb.PTB_Tree()
		>>> tree.set_by_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))")
		>>> pcollins = tree
		>>> tree = ptb.apply_collins_rules(tree)
		>>> etree = Error_Tree()
		>>> etree.set_by_ptb(tree, pcollins)
		>>> etree.check_consistency()

		>>> copy = etree.copy()
		>>> a = copy.subtrees[0].subtrees.pop(0)
		>>> copy.update_span()
		>>> subcopy = copy.get_copy(etree.subtrees[0].subtrees[1])
		>>> print etree.subtrees[0].subtrees[1]
		(VP (VBZ plays) (NP (NNP Elianti)))
		>>> print subcopy
		(VP (VBZ plays) (NP (NNP Elianti)))
		'''
		if self.basis_tree == original:
			return self
		for subtree in self.subtrees:
			ans = subtree.get_copy(original)
			if ans is not None:
				return ans
		return None

	def word_yield(self, span=None):
		'''Print the word yield of a span, default being all words.'''
		text = []
		if self.word is not None:
			if span is None or span[0] <= self.span[0] < span[1]:
				text.append(self.word)
		else:
			for subtree in self.subtrees:
				words = subtree.word_yield(span)
				if words != '':
					text.append(words)
		return ' '.join(text)

	def __repr__(self, depth=0, single_line=True):
		ans = ''
		if not single_line:
			if depth > 0:
				ans = '\n' + depth * '\t'
		ans += '(' + self.label
		if self.word is not None:
			ans += ' ' + self.word
		for subtree in self.subtrees:
			if single_line:
				ans += ' '
			ans += subtree.__repr__(depth + 1, single_line)
		ans += ')'
		return ans

	def colour_repr(self, depth=0, single_line=False, missing=[]):
		'''Pretty print, with errors marked using colour.
		
		'missing' should contain tuples:
			(start, end, label, crossing-T/F)
		'''
		start_missing = "\033[01;36m"
		start_extra = "\033[01;31m"
		start_crossing = "\033[01;33m"
		end_colour = "\033[00m"
		ans = ''
		if not single_line:
			ans += '\n' + depth * '\t'

		# start of this
		if self.extra:
			ans += start_extra + '(' + self.label + end_colour
		else:
			ans += '(' + self.label

		# crossing brackets starting
		if self.parent is None or self.parent.subtrees[0] != self:
			# these are marked as high as possible
			labels = []
			for error in missing:
				if error[0] == self.span[0] and error[3]:
					labels.append(error[2])
			if len(labels) > 0:
				ans += ' ' + start_crossing + ' '.join(labels) + end_colour

		# word
		if self.word is not None:
			ans += ' ' + self.word

		# subtrees
		below = []
		for subtree in self.subtrees:
			text = subtree.colour_repr(depth + 1, single_line, missing)
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
					continue
				for error in missing:
					if below[i][0] == error[0] and below[j][1] == error[1] and not error[3]:
						start = below[i][2].split('(')[0]
						for k in xrange(i, j+1):
							below[k][2] = '\n\t'.join(below[k][2].split('\n'))
						below[i][2] = start + start_missing + '(' + error[2] + end_colour + below[i][2]
						below[j][2] += start_missing + ')' + end_colour
		ans += ''.join([part[2] for part in below])

		# end of this
		if self.extra:
			ans += start_extra + ')' + end_colour
		else:
			ans += ')'

		if self.parent is None or self.parent.subtrees[-1] != self:
			# if there are crossing brackets that end here, mark that
			labels = []
			for error in missing:
				if error[1] == self.span[1] and error[3]:
					labels.append(error[2])
			if len(labels) > 0:
				ans += ' ' + start_crossing + ' '.join(labels) + end_colour

		if self.parent is None or len(self.parent.subtrees) > 1:
			# check for missing brackets that go around this node
			for error in missing:
				if error[0] == self.span[0] and error[1] == self.span[1] and not error[3]:
					if not self.extra:
						# Put them on a new level
						ans = '\n\t'.join(ans.split('\n'))
						extra_text = '\n' + depth * '\t'
						extra_text += start_missing + '(' + error[2] + end_colour
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

	def get_spans(self, nodes=None):
		'''Get a list of nodes and a dictionary of:
		key: span tuple
		value: dictionary with:
		  key: label
		  value: list of nodes
		'''
		return_set = False
		if nodes is None:
			return_set = True
			nodes = []
		if self.word is None:
			for subtree in self.subtrees:
				subtree.get_spans(nodes)
			nodes.append(self)
			if type(self.span) != type(()):
				print self
				print self.span
		if return_set:
			span_set = {}
			for node in nodes:
				key = node.span
				if key not in span_set:
					span_set[key] = {}
				if node.label not in span_set[key]:
					span_set[key][node.label] = []
				span_set[key][node.label].append(node)
			return nodes, span_set

	def span_repr(self, span):
		'''String representation for a particular span.  Handles spans not present
		in this tree.'''
		if self.word is not None:
			if span[0] <= self.span[0] and self.span[1] <= span[1]:
				return '(%s %s)' % (self.label, self.word)
			return ''
		below = []
		for subtree in self.subtrees:
			sub = subtree.span_repr(span)
			if sub != '':
				below.append(sub)
		middle = ' '.join(below)
		if span[0] <= self.span[0] and self.span[1] <= span[1]:
			return '(%s %s)' % (self.label, middle)
		#crossing brackets cases
		if span[0] < self.span[0] < span[1] < self.span[1]:
			if '...' not in middle:
				return '(%s %s ...)' % (self.label, middle)
		if self.span[0] < span[0] < self.span[1] < span[1]:
			if '...' not in middle:
				return '(%s ... %s)' % (self.label, middle)
		return middle

if __name__ == '__main__':
	import doctest
	doctest.testmod()

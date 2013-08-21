#!/usr/bin/env python

class Error_Set:
	def __init__(self):
		self.missing = []
		self.crossing = []
		self.extra = []
		self.spans = {}
	
	def add_error(self, etype, span, label, node):
		error = (etype, span, label, node)
		if span not in self.spans:
			self.spans[span] = {}
		if label not in self.spans[span]:
			self.spans[span][label] = []
		self.spans[span][label].append(error)
		if etype == 'missing':
			self.missing.append(error)
		elif etype == 'crossing':
			self.crossing.append(error)
		elif etype == 'extra':
			self.extra.append(error)

	def is_extra(self, node):
		if node.span in self.spans:
			if node.label in self.spans[node.span]:
				for error in self.spans[node.span][node.label]:
					if error[0] == 'extra':
						return True
		return False

	def __len__(self):
		return len(self.missing) + len(self.extra) + len(self.crossing)

if __name__ == '__main__':
	print "No unit testing implemented for Error_Set"

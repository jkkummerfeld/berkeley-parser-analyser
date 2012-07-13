#!/usr/bin/env python

import sys

###########################################################
#
# Error aggregation by heuristics
#
# Each error function has the same structure. They take 4 arguments:
#   - ungrouped, a list of errors (tuple of error type and a node in a tree)
#   - grouped, a list of Error_Groups
#   - gold, the root of the gold tree
#   - test, the root of the mutable test tree
# They do their processing, forming new Error_Groups and moving the errors
# across. They return:
#   - True/False if any errors were moved across
#   - The fixed test tree
#
###########################################################

class Error_Group:
	def __init__(self):
		self.errors = []
		self.desc = ''
		self.fields = {}
		self.classification = None

	def __repr__(self):
		return self.desc

	def field_is(self, fieldname, text):
		if fieldname not in self.fields:
			return False
		if type(text) == type(''):
			if text == self.fields[fieldname]:
				return True
		if type(text) == type([]):
			for part in text:
				if part == self.fields[fieldname]:
					return True
		return False

	def field_contains(self, fieldname, text):
		if type(fieldname) == type(''):
			fieldname = [fieldname]
		if type(text) == type(''):
			text = [text]
		for name in fieldname:
			if name in self.fields:
				for part in text:
					if part in self.fields[name].split(' '):
						return True
		return False

	def field_endswith(self, fieldname, text):
		if fieldname not in self.fields:
			return False
		if not self.fields[fieldname].endswith(text):
			return False
		return True

	def field_startswith(self, fieldname, text):
		if fieldname not in self.fields:
			return False
		if not self.fields[fieldname].startswith(text):
			return False
		return True

	def determine_type(self):
		for field in self.fields:
			self.fields[field] = self.fields[field].strip()
		self.classification = self.internal_determine_type()
	
	def internal_determine_type(self):
		internal_NP_POS = ['DT', 'NP', 'JJ', 'NNP', 'NNS', 'NNPS', 'FW', 'NN', 'IN','CC','-RRB-','-LRB-','NX']
		if self.field_is('type', 'NP structure'):
			return 'new NP Internal Structure'
		elif self.field_is('type', 'unary'):
			nodes = self.fields['nodes']
			if 'S' in nodes or 'FRAG' in nodes:
				return 'new Unary clause labelling'
			else:
				return 'new Unary'

		elif self.field_is('type', 'single word phrase'):
			return 'new Single word phrase'

		elif self.field_is('type', 'wrong label, right span'):
			return 'new Wrong label, right span'

		elif self.field_is('type', 'attachment'):

			if 'nodes moving' in self.fields:
				text = self.fields['nodes moving']
				if text.startswith('CC') or text.endswith('CC'):
					return 'new Co-ordination'
			if 'siblings' in self.fields:
				text = self.fields['siblings']
				if text.endswith('CC') or text.endswith('CC'):
					return 'new Co-ordination'
			if self.field_endswith('from left siblings', 'CC'):
				return 'new Co-ordination'
			if self.field_endswith('from sibling', 'CC'):
				return 'new Co-ordination'
			if self.field_endswith('left siblings', 'CC'):
				return 'new Co-ordination'
			if self.field_startswith('right siblings', 'CC'):
				return 'new Co-ordination'

			if self.field_contains('nodes moving', 'PP'):
				return 'new PP Attachment'

			if self.field_endswith('nodes moving', 'NP'):
				return 'new NP Attachment'

			if self.field_contains('nodes moving', ['S','SBAR','SINV','RRC']):
				return 'new Clause Attachment'

			if self.field_contains('nodes moving', ['RB', 'JJ', 'JJR', 'ADVP', 'ADJP']):
				return 'new Modifier Attachment'

			if self.field_contains('nodes moving', 'VP'):
				return 'new VP Attachment'

			if self.field_contains('nodes moving', 'PRN'):
				return 'new PRN Attachment'

			if self.field_contains('nodes moving', 'FRAG'):
				return 'new Other Attachment'

			NP_structure = False
			if self.field_contains('old desc', ['NX', 'NAC']):
				NP_structure = True
			if self.field_contains('from parent', 'NP') or self.field_contains('parent', 'NP') or self.field_contains('to parent', 'NP'):
				if 'nodes moving' in self.fields:
					NP_structure = True
					for tag in self.fields['nodes moving'].strip().split():
						if tag not in internal_NP_POS:
							NP_structure = False
							break
			if NP_structure:
				return 'new NP Internal Structure'

			if self.field_contains('to parent', ['ADVP', 'ADJP']):
				return 'new Modifier Attachment'

			if self.field_endswith('nodes moving', 'QP'):
				return 'new QP Attachment'

			if self.field_contains('to parent', 'NP'):
				if 'nodes moving' in self.fields:
					NP_structure = True
					for tag in self.fields['nodes moving'].strip().split():
						if tag not in internal_NP_POS + ['PRN', 'CD']:
							NP_structure = False
							break
					if NP_structure:
						return 'new NP Internal Structure'

			if self.field_contains('to parent', 'QP'):
				if 'nodes moving' in self.fields:
					NP_structure = True
					for tag in self.fields['nodes moving'].strip().split():
						if tag not in internal_NP_POS + ['PRN', 'CD']:
							NP_structure = False
							break
					if NP_structure:
						return 'new QP Internal Structure'

		elif self.field_is('type', 'missing'):
			if self.field_contains('children not first', 'PP'):
				return 'new PP Attachment'
			if 'nodes moving' in self.fields:
				text = self.fields['nodes moving']
				if text.startswith('CC') or text.endswith('CC'):
					return 'new Co-ordination'
			if 'siblings' in self.fields:
				text = self.fields['siblings']
				if text.endswith('CC') or text.endswith('CC'):
					return 'new Co-ordination'
			if self.field_endswith('left siblings', 'CC'):
				return 'new Co-ordination'
			if self.field_startswith('right siblings', 'CC'):
				return 'new Co-ordination'

			if self.field_contains('children', ['RB', 'JJ', 'JJR', 'ADVP', 'ADJP','RBS','JJS']):
				return 'new Modifier Attachment'
			if self.field_contains('children not first', 'S'):
				return 'new Clause Attachment'
			if self.field_contains('new spans', 'PRN'):
				return 'new PRN missing'
			if self.field_contains('new spans', 'QP'):
				if self.field_contains('parent', 'NP'):
					return 'new NP Internal Structure'

			if self.field_contains('new spans', 'NP'):
				if self.field_contains('left siblings', 'NP'):
					if 'right siblings' in self.fields:
						if self.fields['right siblings'] == '':
							if self.field_contains('parent', 'NP'):
								return 'new Appositive'

			if self.field_contains('right siblings', 'ADVP'):
				return 'new Modifier Attachment'

			NP_structure = False
			if self.field_contains('old desc', ['NX', 'NAC']):
				NP_structure = True
			if self.field_contains(['new spans','parent'], 'NP'):
				if 'children' in self.fields:
					NP_structure = True
					for tag in self.fields['children'].strip().split():
						if tag not in internal_NP_POS + ['CD']:
							NP_structure = False
							break
			if NP_structure:
				return 'new NP Internal Structure'

			appos = False
			if self.field_contains(['new spans', 'parent'], 'NP'):
				if 'children' in self.fields:
					appos = True
					for tag in self.fields['children'].strip().split():
						if tag not in ['NP', 'PRN']:
							appos = False
							break
			if appos:
				return 'new Appositive'

			if self.field_contains(['new spans', 'parent'], ['ADVP', 'ADJP']):
				return 'new Modifier Internal Structure'

			if self.field_contains('new spans', 'VP'):
				NP_attach = False
				if 'children' in self.fields:
					NP_attach = True
					for tag in self.fields['children'].strip().split():
						if tag not in internal_NP_POS + ['PRN','NP']:
							NP_attach = False
							break
				if NP_attach:
					return 'new NP Attachment'

			if self.field_contains('children', 'NP'):
				return 'new NP Attachment'
		elif self.field_is('type', 'extra'):
			if self.field_contains('nodes moving', 'PP'):
				return 'new PP Attachment'

			NP_structure = False
			if self.field_contains('old desc', ['NX', 'NAC']):
				NP_structure = True
			if self.field_contains('from parent', 'NP'):
				if 'nodes moving' in self.fields:
					NP_structure = True
					for tag in self.fields['nodes moving'].strip().split():
						if tag not in internal_NP_POS:
							NP_structure = False
							break
			if NP_structure:
				return 'new NP Internal Structure'

			if self.field_contains('nodes moving', ['RB', 'JJ', 'JJR', 'ADVP', 'ADJP']):
				return 'new Modifier Attachment'

			if self.field_contains(['to parent', 'from parent'], 'NP'):
				return 'new NP Internal Structure'

			if self.field_contains('to parent', 'PRN'):
				return 'new NP Internal Structure'

			if self.field_contains('to parent', ['S','SBAR','RRC','SINV']):
				if self.field_contains('from parent', ['S','SBAR','RRC','SINV']):
					return 'new Unary clause labelling'

		elif self.field_is('type', 'extra under bracket on right'):
			if self.field_contains('extra nodes', 'PP'):
				return 'new PP Attachment'
			if self.field_contains('extra nodes', ['JJ','ADVP','RB','JJR','ADJP']):
				return 'new Modifier Attachment'
			if self.field_contains('parent', 'QP'):
				return 'new QP Internal Structure'
			if self.field_contains('extra nodes', 'NP'):
				return 'new NP Internal Structure'

		elif self.field_is('type', 'fencepost'):
			if self.field_contains('nodes moving', ['DT','NP']):
				return 'new NP Internal Structure'
			if self.field_contains('nodes moving', ['JJR','ADVP','JJ','ADVP','RB']):
				return 'new Modifier Attachment'
			if self.field_contains('nodes moving', ['S','SBAR','SINV','RRC']):
				return 'new Clause Attachment'

		return 'new Other'


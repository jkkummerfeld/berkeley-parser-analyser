#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

import sys
from nlp_util import pstree, render_tree, nlp_eval, treebanks, parse_errors

def mprint(text, out_dict, out_name):
	all_stdout = True
	for key in out_dict:
		if out_dict[key] != sys.stdout:
			all_stdout = False
	
	if all_stdout:
		print text
	elif out_name == 'all':
		for key in out_dict:
			print >> out_dict[key], text
	else:
		print >> out_dict[out_name], text


if __name__ == '__main__':
	if len(sys.argv) != 4:
		print "Print trees with colours to indicate errors (red for extra, blue for missing, yellow for crossing missing)"
		print "   %s <gold> <test> <output_prefix>" % sys.argv[0]
		print "Running doctest"
		import doctest
		doctest.testmod()
		sys.exit(0)

	out = {
		'err': sys.stdout,
		'out': sys.stdout,
		'tex': sys.stdout
	}
	if len(sys.argv) > 3:
		prefix = sys.argv[3]
		for key in out:
			out[key] = open(prefix + '.' + key, 'w')
	gold_in = open(sys.argv[1])
	test_in = open(sys.argv[2])
	sent_no = 0
	stats = {
		'out': [0, 0, 0]
	}
	
	tex_start = '''\\documentclass[11pt]{article}
\\usepackage{times}
\\usepackage{ulem}
\\usepackage{amsmath}
\\usepackage{multirow}
\\usepackage{graphicx}
\\usepackage[landscape, top=0.2cm, bottom=0.2cm, left=0.2cm, right=0.2cm]{geometry}
\\usepackage{enumerate}
\\usepackage{multirow}
\\usepackage{synttree}

\\newcommand{\\wrongnode}[1]{\\textbf{\\fbox{#1}}}
\\branchheight{0.33in}
\\trianglebalance{50}
\\childsidesep{1em}
\\childattachsep{0.5in}
\\newcommand{\\derivscale}{0.8}
\\newcommand{\\derivspace}{\\vspace{-4mm}}
\\newcommand{\\derivaftercompress}{\\vspace{-2mm}}

\\title{Parser errors}
\\author{}

\\date{}

\\begin{document}
\\maketitle'''
	mprint(tex_start, out, 'tex')

	while True:
		sent_no += 1
		gold_text = gold_in.readline()
		test_text = test_in.readline()
		if gold_text == '' and test_text == '':
			mprint("End of both input files", out, 'err')
			break
		elif gold_text == '':
			mprint("End of gold input", out, 'err')
			break
		elif test_text == '':
			mprint("End of test input", out, 'err')
			break

		mprint("Sentence %d:" % sent_no, out, 'all')

		gold_text = gold_text.strip()
		test_text = test_text.strip()
		if len(gold_text) == 0:
			mprint("No gold tree", out, 'all')
			continue
		elif len(test_text) == 0:
			mprint("Not parsed", out, 'all')
			continue

		gold_complete_tree = pstree.tree_from_text(gold_text)
		treebanks.ptb_cleaning(gold_complete_tree)
		gold_tree = treebanks.apply_collins_rules(gold_complete_tree, False)
		if gold_tree is None:
			mprint("Empty gold tree", out, 'all')
			mprint(gold_complete_tree.__repr__(), out, 'all')
			mprint(gold_tree.__repr__(), out, 'all')
			continue

		if '()' in test_text:
			mprint("() test tree", out, 'all')
			continue
		test_complete_tree = pstree.tree_from_text(test_text)
		treebanks.ptb_cleaning(test_complete_tree)
		test_tree = treebanks.apply_collins_rules(test_complete_tree, False)
		if test_tree is None:
			mprint("Empty test tree", out, 'all')
			mprint(test_complete_tree.__repr__(), out, 'all')
			mprint(test_tree.__repr__(), out, 'all')
			continue

		gold_words = gold_tree.word_yield()
		test_words = test_tree.word_yield()
		if len(test_words.split()) != len(gold_words.split()):
			mprint("Sentence lengths do not match...", out, 'all')
			mprint("Gold: " + gold_words.__repr__(), out, 'all')
			mprint("Test: " + test_words.__repr__(), out, 'all')

		mprint("After applying collins rules:", out, 'out')
		mprint(render_tree.text_coloured_errors(test_tree, gold_tree).strip(), out, 'out')
		match, gold, test, crossing, POS = parse_errors.counts_for_prf(test_tree, gold_tree)
		stats['out'][0] += match
		stats['out'][1] += gold
		stats['out'][2] += test
		p, r, f = nlp_eval.calc_prf(match, gold, test)
		mprint("Eval: %.2f  %.2f  %.2f" % (p*100, r*100, f*100), out, 'out')

		# Work out the minimal span to show all errors
		gold_spans = set([(node.label, node.span[0], node.span[1]) for node in gold_tree.get_nodes()])
		test_spans = set([(node.label, node.span[0], node.span[1]) for node in test_tree.get_nodes()])
		diff = gold_spans.symmetric_difference(test_spans)
		width = [1e5, -1]
		for span in diff:
			if span[2] - span[1] == 1:
				continue
			if span[1] < width[0]:
				width[0] = span[1]
			if span[2] > width[1]:
				width[1] = span[2]
		mprint('\n\\scalebox{\\derivscale}{', out, 'tex')
		mprint(render_tree.tex_synttree(test_tree, gold_spans, span=width), out, 'tex')
		mprint( '}\n\\small\n(a) Parser output\n\n\\vspace{3mm}\n\\scalebox{\\derivscale}{', out, 'tex')
		mprint(render_tree.tex_synttree(gold_tree, test_spans, span=width), out, 'tex')
		mprint( '}\n\\small\n(b) Gold tree\n\\pagebreak', out, 'tex')

		mprint("", out, 'all')
	match = stats['out'][0]
	gold = stats['out'][1]
	test = stats['out'][2]
	p, r, f = nlp_eval.calc_prf(match, gold, test)
	mprint("Overall %s: %.2f  %.2f  %.2f" % ('out', p*100, r*100, f*100), out, 'out')
	
	mprint('\\end{document}', out, 'tex')

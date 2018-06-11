#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

from pstree import *

ptb_tag_set = set(['S', 'SBAR', 'SBARQ', 'SINV', 'SQ', 'ADJP', 'ADVP', 'CONJP',
'FRAG', 'INTJ', 'LST', 'NAC', 'NP', 'NX', 'PP', 'PRN', 'PRT', 'QP', 'RRC',
'UCP', 'VP', 'WHADJP', 'WHADVP', 'WHNP', 'WHPP', 'X', 'NML'])

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
}
bugfix_word_to_POS = {
    'Wa': 'NNP'
}
def ptb_cleaning(tree, in_place=True):
    '''Clean up some bugs/odd things in the PTB, and standardise punctuation.'''
    if not in_place:
        tree = tree.clone()
    for node in tree:
        # In a small number of cases multiple POS tags were assigned
        if '|' in node.label:
            if 'ADVP' in node.label:
                node.label = 'ADVP'
            else:
                node.label = node.label.split('|')[0]
        # Fix some issues with variation in output, and one error in the treebank
        # for a word with a punctuation POS
        if node.word in word_to_word_mapping:
            node.word = word_to_word_mapping[node.word]
        if node.word in word_to_POS_mapping:
            node.label = word_to_POS_mapping[node.word]
        if node.word in bugfix_word_to_POS:
            node.label = bugfix_word_to_POS[node.word]
    return tree

def remove_trivial_unaries(tree, in_place=True):
    '''Collapse A-over-A unary productions.

    >>> tree = tree_from_text("(ROOT (S (S (PP (PP (PP (IN By) (NP (CD 1997))))))))")
    >>> otree = remove_trivial_unaries(tree, False)
    >>> print otree
    (ROOT (S (PP (IN By) (NP (CD 1997)))))
    >>> print tree
    (ROOT (S (S (PP (PP (PP (IN By) (NP (CD 1997))))))))
    >>> remove_trivial_unaries(tree)
    (ROOT (S (PP (IN By) (NP (CD 1997)))))
    '''
    if in_place:
        if len(tree.subtrees) == 1 and tree.label == tree.subtrees[0].label:
            tree.subtrees = tree.subtrees[0].subtrees
            for subtree in tree.subtrees:
                subtree.parent = tree
            remove_trivial_unaries(tree, True)
        else:
            for subtree in tree.subtrees:
                remove_trivial_unaries(subtree, True)
    else:
        if len(tree.subtrees) == 1 and tree.label == tree.subtrees[0].label:
            return remove_trivial_unaries(tree.subtrees[0], False)
        subtrees = [remove_trivial_unaries(subtree, False) for subtree in tree.subtrees]
        tree = PSTree(tree.word, tree.label, tree.span, None, subtrees)
        for subtree in subtrees:
            subtree.parent = tree
    return tree

def remove_nodes(tree, filter_func, in_place=True, preserve_subtrees=False, init_call=True):
    if filter_func(tree) and not preserve_subtrees:
        return None
    subtrees = []
    for subtree in tree.subtrees:
        ans = remove_nodes(subtree, filter_func, in_place, preserve_subtrees, False)
        if ans is not None:
            if type(ans) == type([]):
                subtrees += ans
            else:
                subtrees.append(ans)
    if len(subtrees) == 0 and (not tree.is_terminal()):
        return None
    if filter_func(tree) and preserve_subtrees:
        return subtrees
    if in_place:
        tree.subtrees = subtrees
        for subtree in subtrees:
            subtree.parent = tree
    else:
        tree = PSTree(tree.word, tree.label, tree.span, None, subtrees)
    return tree

def remove_traces(tree, in_place=True):
    '''Adjust the tree to remove traces.

    >>> tree = tree_from_text("(ROOT (S (PP (IN By) (NP (CD 1997))) (, ,) (NP (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed) (NP (-NONE- *-6))))) (. .)))")
    >>> remove_traces(tree, False)
    (ROOT (S (PP (IN By) (NP (CD 1997))) (, ,) (NP (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed)))) (. .)))
    '''
    return remove_nodes(tree, PSTree.is_trace, in_place)

def split_label_type_and_function(label):
    parts = label.split('=')
    if len(label) > 0 and label[0] != '-':
        cur = parts
        parts = []
        for part in cur:
            parts += part.split('-')
    return parts

def remove_function_tags(tree, in_place=True):
    '''Adjust the tree to remove function tags on labels.

    >>> tree = tree_from_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti))) (. .)))")
    >>> remove_function_tags(tree, False)
    (ROOT (S (NP (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti))) (. .)))

    # don't remove brackets
    >>> tree = tree_from_text("(ROOT (S (NP-SBJ (`` ``) (NP-TTL (NNP Funny) (NNP Business)) ('' '') (PRN (-LRB- -LRB-) (NP (NNP Soho)) (, ,) (NP (CD 228) (NNS pages)) (, ,) (NP ($ $) (CD 17.95)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP-PRD (NP (NN anything)) (PP (RB but)))) (. .)))")
    >>> remove_function_tags(tree)
    (ROOT (S (NP (`` ``) (NP (NNP Funny) (NNP Business)) ('' '') (PRN (-LRB- -LRB-) (NP (NNP Soho)) (, ,) (NP (CD 228) (NNS pages)) (, ,) (NP ($ $) (CD 17.95)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP (NP (NN anything)) (PP (RB but)))) (. .)))
    '''
    label = split_label_type_and_function(tree.label)[0]
    if in_place:
        for subtree in tree.subtrees:
            remove_function_tags(subtree, True)
        tree.label = label
    else:
        subtrees = [remove_function_tags(subtree, False) for subtree in tree.subtrees]
        tree = PSTree(tree.word, label, tree.span, None, subtrees)
        for subtree in subtrees:
            subtree.parent = tree
    return tree

# Applies rules to strip out the parts of the tree that are not used in the
# standard evalb evaluation
def apply_collins_rules(tree, in_place=True):
    '''Adjust the tree to remove parts not evaluated by the standard evalb
    config.

    # cutting punctuation and -X parts of labels
    >>> tree = tree_from_text("(ROOT (S (NP-SBJ (NNP Ms.) (NNP Haag) ) (VP (VBZ plays) (NP (NNP Elianti) )) (. .) ))")
    >>> apply_collins_rules(tree)
    (ROOT (S (NP (NNP Ms.) (NNP Haag)) (VP (VBZ plays) (NP (NNP Elianti)))))
    >>> print tree.word_yield()
    Ms. Haag plays Elianti

    # cutting nulls
    >>> tree = tree_from_text("(ROOT (S (PP-TMP (IN By) (NP (CD 1997))) (, ,) (NP-SBJ-6 (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed) (NP (-NONE- *-6))))) (. .)))")
    >>> apply_collins_rules(tree)
    (ROOT (S (PP (IN By) (NP (CD 1997))) (NP (NP (ADJP (RB almost) (DT all)) (VBG remaining) (NNS uses)) (PP (IN of) (NP (JJ cancer-causing) (NN asbestos)))) (VP (MD will) (VP (VB be) (VP (VBN outlawed))))))

    # changing PRT to ADVP
    >>> tree = tree_from_text("(ROOT (S (NP-SBJ-41 (DT That) (NN fund)) (VP (VBD was) (VP (VBN put) (NP (-NONE- *-41)) (PRT (RP together)) (PP (IN by) (NP-LGS (NP (NNP Blackstone) (NNP Group)) (, ,) (NP (DT a) (NNP New) (NNP York) (NN investment) (NN bank)))))) (. .)))")
    >>> apply_collins_rules(tree)
    (ROOT (S (NP (DT That) (NN fund)) (VP (VBD was) (VP (VBN put) (ADVP (RP together)) (PP (IN by) (NP (NP (NNP Blackstone) (NNP Group)) (NP (DT a) (NNP New) (NNP York) (NN investment) (NN bank))))))))

    # not removing brackets
    >>> tree = tree_from_text("(ROOT (S (NP-SBJ (`` ``) (NP-TTL (NNP Funny) (NNP Business)) ('' '') (PRN (-LRB- -LRB-) (NP (NNP Soho)) (, ,) (NP (CD 228) (NNS pages)) (, ,) (NP ($ $) (CD 17.95) (-NONE- *U*)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP-PRD (NP (NN anything)) (PP (RB but) (NP (-NONE- *?*))))) (. .)))")
    >>> apply_collins_rules(tree)
    (ROOT (S (NP (NP (NNP Funny) (NNP Business)) (PRN (-LRB- -LRB-) (NP (NNP Soho)) (NP (CD 228) (NNS pages)) (NP ($ $) (CD 17.95)) (-RRB- -RRB-)) (PP (IN by) (NP (NNP Gary) (NNP Katzenstein)))) (VP (VBZ is) (NP (NP (NN anything)) (PP (RB but))))))
    '''
    tree = tree if in_place else tree.clone()
    remove_traces(tree, True)
    remove_function_tags(tree, True)
    ptb_cleaning(tree, True)

    # Remove Puncturation
    labels_to_ignore = ["-NONE-", ",", ":", "``", "''", "."]
    remove_nodes(tree, lambda(t): t.label in labels_to_ignore, True)

    # Set all PRTs to be ADVPs
    POS_to_convert = {'PRT': 'ADVP'}
    for node in tree:
        if node.label in POS_to_convert:
            node.label = POS_to_convert[node.label]

    tree.calculate_spans()
    return tree

def homogenise_tree(tree, tag_set=ptb_tag_set):
    '''Change the top of the tree to be of a consistent form.

    >>> tree = tree_from_text("( (S (NP (NNP Example))))", True)
    >>> homogenise_tree(tree)
    (ROOT (S (NP (NNP Example))))
    >>> tree = tree_from_text("( (ROOT (S (NP (NNP Example))) ) )", True)
    >>> homogenise_tree(tree)
    (ROOT (S (NP (NNP Example))))
    >>> tree = tree_from_text("(S1 (S (NP (NNP Example))))")
    >>> homogenise_tree(tree)
    (ROOT (S (NP (NNP Example))))
    '''
    orig = tree
    tree = tree.root()
    if tree.label != 'ROOT':
        while split_label_type_and_function(tree.label)[0] not in tag_set:
            if len(tree.subtrees) > 1:
                break
            elif tree.is_terminal():
                raise Exception("Tree has no labels in the tag set\n%s" % orig.__repr__())
            tree = tree.subtrees[0]
        if split_label_type_and_function(tree.label)[0] not in tag_set:
            tree.label = 'ROOT'
        else:
            root = PSTree(None, 'ROOT', tree.span, None, [])
            root.subtrees.append(tree)
            tree.parent = root
            tree = root
    return tree

def ptb_read_tree(source, return_empty=False, allow_empty_labels=False, allow_empty_words=False, blank_line_coverage=False):
    '''Read a single tree from the given PTB file.

    The function reads a character at a time, stopping as soon as a tree can be
    constructed, so multiple trees on a sinlge line are manageable.

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
    >>> ptb_read_tree(in_file)
    (ROOT (S (NP-SBJ (NNP Scotty)) (VP (VBD did) (RB not) (VP (VB go) (ADVP (RB back)) (PP (TO to) (NP (NN school))))) (. .)))'''
    cur_text = ''
    depth = 0
    while True:
        char = source.read(1)
        if char == '':
            return None
        if char == '\n' and cur_text == ' ' and blank_line_coverage:
            return "Empty"
        if char in '\n\t':
            char = ' '
        cur_text += char
        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
        if depth == 0:
            if '()' in cur_text:
                if return_empty:
                    return "Empty"
                cur_text = ''
                continue
            if '(' in cur_text:
                break

    tree = tree_from_text(cur_text, allow_empty_labels, allow_empty_words)
    ptb_cleaning(tree)
    return tree

def conll_read_tree(source, return_empty=False, allow_empty_labels=False, allow_empty_words=False, blank_line_coverage=False):
    '''Read a single tree from the given CoNLL Shared Task OntoNotes data file.

    >>> from StringIO import StringIO
    >>> file_text = """#begin document (nw/wsj/00/wsj_0020)
    ... nw/wsj/00/wsj_0020          0          0       They        PRP (TOP_(S_(NP_*)          -          -          -          -          * (ARG1*)          *        (0)
    ... nw/wsj/00/wsj_0020          0          1       will         MD      (VP_*          -          -          -          -          * (ARGM-M OD*)          *          -
    ... nw/wsj/00/wsj_0020          0          2     remain         VB      (VP_*     remain         01          1          -          *       ( V*)          *          -
    ... nw/wsj/00/wsj_0020          0          3         on         IN      (PP_*          -          -          -          -          *     (AR G3*          *          -
    ... nw/wsj/00/wsj_0020          0          4          a         DT  (NP_(NP_*          -          -          -          -          * *     (ARG2*          -
    ... nw/wsj/00/wsj_0020          0          5      lower        JJR     (NML_*          -          -          -          -          * *          *          -
    ... nw/wsj/00/wsj_0020          0          6          -       HYPH          *          -          -          -          -          * *          *          -
    ... nw/wsj/00/wsj_0020          0          7   priority         NN         *)          -          -          -          -          * *          *          -
    ... nw/wsj/00/wsj_0020          0          8       list         NN         *)          -          -          1          -          * *         *)          -
    ... nw/wsj/00/wsj_0020          0          9       that        WDT (SBAR_(WHNP_*)          -          -          -          -          * *          *          -
    ... nw/wsj/00/wsj_0020          0         10   includes        VBZ   (S_(VP_*          -          -          1          -          * *       (V*)          -
    ... nw/wsj/00/wsj_0020          0         11         17         CD      (NP_*          -          -          -          - (CARDINAL) *     (ARG1*        (10
    ... nw/wsj/00/wsj_0020          0         12      other         JJ          *          -          -          -          -          * *          *          -
    ... nw/wsj/00/wsj_0020          0         13  countries        NNS  *))))))))          -          -          3          -          * *)         *)        10)
    ... nw/wsj/00/wsj_0020          0         14          .          .        *))          -          -          -          -          * *          *          -
    ...
    ... """
    >>> in_file = StringIO(file_text)
    >>> tree = conll_read_tree(in_file)
    >>> print tree
    (TOP (S (NP (PRP They)) (VP (MD will) (VP (VB remain) (PP (IN on) (NP (NP (DT a) (NML (JJR lower) (HYPH -) (NN priority)) (NN list)) (SBAR (WHNP (WDT that)) (S (VP (VBZ includes) (NP (CD 17) (JJ other) (NNS countries))))))))) (. .)))'''
    cur_text = []
    while True:
        line = source.readline()
        # Check if we are out of input
        if line == '':
            return None
        # strip whitespace and see if this is then end of the parse
        line = line.strip()
        if line == '':
            break
        cur_text.append(line)

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
    return tree_from_text(text)

def generate_trees(source, tree_reader=ptb_read_tree, max_sents=-1, return_empty=False, allow_empty_labels=False, allow_empty_words=False):
    '''Read trees from the given file (opening the file if only a string is given).

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
    ...         (NP-SBJ (DT The) (NN bandit) )
    ...         (VP (VBZ laughs)
    ...             (PP (IN in)
    ...                 (NP (PRP$ his) (NN face) )))
    ...         (. .) ))"""
    >>> in_file = StringIO(file_text)
    >>> for tree in generate_trees(in_file):
    ...   print tree
    (ROOT (S (NP-SBJ (NNP Scotty)) (VP (VBD did) (RB not) (VP (VB go) (ADVP (RB back)) (PP (TO to) (NP (NN school))))) (. .)))
    (ROOT (S (NP-SBJ (DT The) (NN bandit)) (VP (VBZ laughs) (PP (IN in) (NP (PRP$ his) (NN face)))) (. .)))'''
    if type(source) == type(''):
        source = open(source)
    count = 0
    while True:
        tree = tree_reader(source, return_empty, allow_empty_labels, allow_empty_words)
        if tree == "Empty":
            yield None
            continue
        if tree is None:
            return
        yield tree
        count += 1
        if count >= max_sents > 0:
            return

def read_trees(source, tree_reader=ptb_read_tree, max_sents=-1, return_empty=False):
    return [tree for tree in generate_trees(source, tree_reader, max_sents, return_empty)]

if __name__ == '__main__':
    print "Running doctest"
    import doctest
    doctest.testmod()

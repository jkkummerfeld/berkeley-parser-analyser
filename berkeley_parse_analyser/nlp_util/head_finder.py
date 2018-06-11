#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:
'''Identifies the word that is the lexical head of each non-terminal in a parse'''

import sys

COLLINS_MAPPING_TABLE = {
    'ADJP': ('right', ['NNS', 'QP', 'NN', '$', 'ADVP', 'JJ', 'VBN', 'VBG', 'ADJP', 'JJR', 'NP',
                       'JJS', 'DT', 'FW', 'RBR', 'RBS', 'SBAR', 'RB']),
    'ADVP': ('left', ['RB', 'RBR', 'RBS', 'FW', 'ADVP', 'TO', 'CD', 'JJR', 'JJ', 'IN', 'NP', 'JJS',
                      'NN']),
    'CONJP': ('left', ['CC', 'RB', 'IN']),
    'FRAG': ('left', []),
    'INTJ': ('right', []),
    'LST': ('left', ['LS', ':']),
    'NAC': ('right', ['NN', 'NNS', 'NNP', 'NNPS', 'NP', 'NAC', 'EX', '$', 'CD', 'QP', 'PRP', 'VBG',
                      'JJ', 'JJS', 'JJR', 'ADJP', 'FW']),
    'PP': ('left', ['IN', 'TO', 'VBG', 'VBN', 'RP', 'FW']),
    'PRN': ('right', []),
    'PRT': ('left', ['RP']),
    'QP': ('right', ['$', 'IN', 'NNS', 'NN', 'JJ', 'RB', 'DT', 'CD', 'NCD', 'QP', 'JJR', 'JJS']),
    'RRC': ('left', ['VP', 'NP', 'ADVP', 'ADJP', 'PP']),
    'S': ('right', ['TO', 'IN', 'VP', 'S', 'SBAR', 'ADJP', 'UCP', 'NP']),
    'SBAR': ('right', ['WHNP', 'WHPP', 'WHADVP', 'WHADJP', 'IN', 'DT', 'S', 'SQ', 'SINV', 'SBAR',
                       'FRAG']),
    'SBARQ': ('right', ['SQ', 'S', 'SINV', 'SBARQ', 'FRAG']),
    'SINV': ('right', ['VBZ', 'VBD', 'VBP', 'VB', 'MD', 'VP', 'S', 'SINV', 'ADJP', 'NP']),
    'SQ': ('right', ['VBZ', 'VBD', 'VBP', 'VB', 'MD', 'VP', 'SQ']),
    'UCP': ('left', []),
    'VP': ('right', ['TO', 'VBD', 'VBN', 'MD', 'VBZ', 'VB', 'VBG', 'VBP', 'VP', 'ADJP', 'NN',
                     'NNS', 'NP']),
    'WHADJP': ('right', ['CC', 'WRB', 'JJ', 'ADJP']),
    'WHADVP': ('left', ['CC', 'WRB']),
    'WHNP': ('right', ['WDT', 'WP', 'WP$', 'WHADJP', 'WHPP', 'WHNP']),
    'WHPP': ('left', ['IN', 'TO', 'FW']),
    # Added by me:
    'NX': ('right', ['NN', 'NNS', 'NNP', 'NNPS', 'NP', 'NAC', 'EX', '$', 'CD', 'QP', 'PRP', 'VBG',
                     'JJ', 'JJS', 'JJR', 'ADJP', 'FW']),
    'X': ('right', ['NN', 'NNS', 'NNP', 'NNPS', 'NP', 'NAC', 'EX', '$', 'CD', 'QP', 'PRP', 'VBG',
                    'JJ', 'JJS', 'JJR', 'ADJP', 'FW']),
    'META': ('right', [])
}

def add_head(head_map, tree, head):
    '''Update head_map to have a representation of this node map to the given head'''
    tree_repr = (tree.span, tree.label)
    head_map[tree_repr] = head

def get_head(head_map, tree):
    '''Extract the head from head_map for tree'''
    tree_repr = (tree.span, tree.label)
    return head_map[tree_repr]

def first_search(tree, options, head_map):
    '''Find the first subtree to match as required'''
    for subtree in tree.subtrees:
        if get_head(head_map, subtree)[2] in options or subtree.label in options:
            add_head(head_map, tree, get_head(head_map, subtree))
            return True
    return False

def last_search(tree, options, head_map):
    '''Starting from the end, find the first subtree to match as required'''
    for i in xrange(len(tree.subtrees) - 1, -1, -1):
        subtree = tree.subtrees[i]
        if get_head(head_map, subtree)[2] in options or subtree.label in options:
            add_head(head_map, tree, get_head(head_map, subtree))
            return True
    return False

def collins_np(tree, head_map):
    '''Find the head for a noun phrase'''
    for subtree in tree.subtrees:
        collins_find_heads(subtree, head_map)

    if get_head(head_map, tree.subtrees[-1])[2] == 'POS':
        add_head(head_map, tree, get_head(head_map, tree.subtrees[-1]))
        return
    if last_search(tree, set(['NN', 'NNP', 'NNPS', 'NNS', 'NX', 'POS', 'JJR']), head_map):
        return
    if first_search(tree, set(['NP', 'NML']), head_map):
        return
    if last_search(tree, set(['$', 'ADJP', 'PRN']), head_map):
        return
    if last_search(tree, set(['CD']), head_map):
        return
    if last_search(tree, set(['JJ', 'JJS', 'RB', 'QP']), head_map):
        return
    add_head(head_map, tree, get_head(head_map, tree.subtrees[-1]))

def collins_find_heads(tree, head_map=None):
    '''Head finding using the method defined by Collins, as described below'''
    if head_map is None:
        head_map = {}
    for subtree in tree.subtrees:
        collins_find_heads(subtree, head_map)

    # A word is it's own head
    if tree.word is not None:
        head = (tree.span, tree.word, tree.label)
        add_head(head_map, tree, head)
        return head_map

    # If the label for this node is not in the table we are either at the bottom,
    # at an NP, or have an error
    if tree.label not in COLLINS_MAPPING_TABLE:
        if tree.label in ['NP', 'NML']:
            collins_np(tree, head_map)
        else:
            if tree.label not in ['ROOT', 'TOP', 'S1', '']:
                print >> sys.stderr, "Unknown Label: %s" % tree.label
                print >> sys.stderr, "In tree:", tree.root()
            add_head(head_map, tree, get_head(head_map, tree.subtrees[-1]))
        return head_map

    # Look through and take the first/last occurrence that matches
    info = COLLINS_MAPPING_TABLE[tree.label]
    for label in info[1]:
        for i in xrange(len(tree.subtrees)):
            if info[0] == 'right':
                i = len(tree.subtrees) - i - 1
            subtree = tree.subtrees[i]
            if subtree.label == label or get_head(head_map, subtree)[2] == label:
                add_head(head_map, tree, get_head(head_map, subtree))
                return head_map

    # Final fallback
    if info[0] == 'left':
        add_head(head_map, tree, get_head(head_map, tree.subtrees[0]))
    else:
        add_head(head_map, tree, get_head(head_map, tree.subtrees[-1]))

    return head_map

#  Text from Collins' website:
#
#  This file describes the table used to identify head-words in the papers
#
#  Three Generative, Lexicalised Models for Statistical Parsing  (ACL/EACL97)
#  A New Statistical Parser Based on Bigram Lexical Dependencies (ACL96)
#
#  There are two parts to this file:
#
#  [1] an email from David Magerman describing the head-table used in
#      D. Magerman. 1995. Statistical Decision-Tree Models for Parsing.
#      { Proceedings of the 33rd Annual Meeting of
#      the Association for Computational Linguistics}, pages 276-283.
#
#  [2] A modified version of David's head-table which I used in my experiments.
#
#  Many thanks to David Magerman for allowing me to distribute his table.
#
#
#  [1]
#
#  From magerman@bbn.com Thu May 25 13:48 EDT 1995
#  Posted-Date: Thu, 25 May 1995 13:48:07 -0400
#  Received-Date: Thu, 25 May 1995 13:48:43 +0500
#  Message-Id: <199505251748.NAA02892@thane.bbn.com>
#  To: mcollins@gradient.cis.upenn.edu, robertm@unagi.cis.upenn.edu,
#          mitch@linc.cis.upenn.edu
#  Cc: magerman@bbn.com
#  Subject: Re: Head words table
#  In-Reply-To: Your message of "Thu, 25 May 1995 13:17:14 EDT."
#               <9505251717.AA17874@gradient.cis.upenn.edu>
#  Date: Thu, 25 May 1995 13:48:07 -0400
#  From: David Magerman <magerman@bbn.com>
#  Content-Type: text
#  Content-Length: 2972
#
#
#  Hi all.  Mike and Robert asked me for the Tree Head Table, so I
#  thought I'd pass it along to everyone in one shot.  Feel free to
#  distribute it to whomever at Penn wants it.
#
#  Note that it's not complete, and that I've invented a tag (% for the
#  symbol %) and a label (NP$ for NP's that end in POS).  I also have
#  some optional mapping mechanisms that: (a) convert to_TO -> to_IN when
#  in a prepositional phrase and (b) translate (PRT x_RP) -> (ADVP x_RB),
#  thus mapping away the distinction between particles and adverbs.  I
#  currently use transformation (b) in my parser, but don't use (a).
#  These facts may or may not be relevant, depending on how you want to
#  use this table.
#
#  Cheers,
#  -- David
#
#  Tree Head Table
#  ---------------
#
#  Instructions:
#
#  1. The first column is the non-terminal.  The second column indicates
#  where you start when you are looking for a head (left is for
#  head-initial categories, right is for head-final categories).  The
#  rest of the line is a list of non-terminal and pre-terminal categories
#  which represent the head rule.
#
#  2. ** is a wildcard value.  Any non-terminal with ** in its rule means
#  that anything can be its head.  So, for a head-initial category, **
#  means the first word is always the head, and for a head-final
#  category, ** means the last word is always the head.  In most cases,
#  ** means I didn't investigate good head rules for that category, so it
#  might be worthwhile to do so yourself.
#
#  3. The Tree Head Table is used as follows:
#
#      a. Use tree head rule based on NT category of constituent
#      b. For each category X in tree head rule, scan the children of
#             the constituent for the first (or last, for head-final)
#             occurrence of category X.  If
#             X occurs, that child is the head.
#          c. If no child matches any category in the list, use the first
#             (or last, for head-final) child as the head.
#
#  4. I treat the NP category as a special case.  Before consulting the
#  head rule for NP, I look for the rightmost child with a label
#  beginning with the letter N.  If one exists, I use that child as the
#  head.  If no child's tag begins with N, I use the tree head rule.
#
#  ADJP    right   % QP JJ VBN VBG ADJP $ JJR JJS DT FW **** RBR RBS RB
#  ADVP    left    RBR RB RBS FW ADVP CD **** JJR JJS JJ
#  CONJP   left    CC RB IN
#  FRAG    left    **
#  INTJ    right   **
#  LST left    LS :
#  NAC right   NN NNS NNP NNPS NP NAC EX $ CD QP PRP VBG JJ JJS JJR ADJP FW
#  NP  right   EX $ CD QP PRP VBG JJ JJS JJR ADJP DT FW RB SYM PRP$
#  NP$ right   NN NNS NNP NNPS NP NAC EX $ CD QP PRP VBG JJ JJS JJR ADJP FW SYM
#  PNP right   **
#  PP  left    IN TO FW
#  PRN left    **
#  PRT left    RP
#  QP  right   CD NCD % QP JJ JJR JJS DT
#  RRC left    VP NP ADVP ADJP PP
#  S   right   VP SBAR ADJP UCP NP
#  SBAR    right   S SQ SINV SBAR FRAG X
#  SBARQ   right   SQ S SINV SBARQ FRAG X
#  SINV    right   S VP VBZ VBD VBP VB SINV ADJP NP
#  SQ  right   VP VBZ VBD VBP VB MD SQ
#  UCP left    **
#  VP  left    VBD VBN MD VBZ TO VB VP VBG VBP ADJP NP
#  WHADJP  right   JJ ADJP
#  WHADVP  left    WRB
#  WHNP    right   WDT WP WP$ WHADJP WHPP WHNP
#  WHPP    left    IN TO FW
#  X   left    **
#
#
#  [2]
#
#  Here's the head table which I used in my experiments below. The first column
#  is just the number of fields on that line. Otherwise, the format is the same
#  as David's.
#
#  Ignore the row for NPs -- I use a special set of rules for this. For these
#  I initially remove ADJPs, QPs, and also NPs which dominate a possesive
#  (tagged POS, e.g.  (NP (NP the man 's) telescope ) becomes
#  (NP the man 's telescope)). These are recovered as a post-processing stage
#  after parsing. The following rules are then used to recover the NP head:
#
#  If the last word is tagged POS, return (last-word);
#
#  Else search from right to left for the first child which is an NN, NNP, NNPS, NNS, NX, POS, or
#  JJR
#
#  Else search from left to right for first child which is an NP
#
#  Else search from right to left for the first child which is a $, ADJP or PRN
#
#  Else search from right to left for the first child which is a CD
#
#  Else search from right to left for the first child which is a JJ, JJS, RB or QP
#
#  Else return the last word
#
#
#  20 ADJP 0   NNS QP NN $ ADVP JJ VBN VBG ADJP JJR NP JJS DT FW RBR RBS SBAR RB
#  15 ADVP 1   RB RBR RBS FW ADVP TO CD JJR JJ IN NP JJS NN
#  5 CONJP 1   CC RB IN
#  2 FRAG  1
#  2 INTJ  0
#  4 LST   1   LS :
#  19 NAC  0   NN NNS NNP NNPS NP NAC EX $ CD QP PRP VBG JJ JJS JJR ADJP FW
#  8 PP    1   IN TO VBG VBN RP FW
#  2 PRN   0
#  3 PRT   1   RP
#  14 QP   0   $ IN NNS NN JJ RB DT CD NCD QP JJR JJS
#  7 RRC   1   VP NP ADVP ADJP PP
#  10 S    0   TO IN VP S SBAR ADJP UCP NP
#  13 SBAR 0   WHNP WHPP WHADVP WHADJP IN DT S SQ SINV SBAR FRAG
#  7 SBARQ 0   SQ S SINV SBARQ FRAG
#  12 SINV 0   VBZ VBD VBP VB MD VP S SINV ADJP NP
#  9 SQ    0   VBZ VBD VBP VB MD VP SQ
#  2 UCP   1
#  15 VP   0   TO VBD VBN MD VBZ VB VBG VBP VP ADJP NN NNS NP
#  6 WHADJP    0   CC WRB JJ ADJP
#  4 WHADVP    1   CC WRB
#  8 WHNP  0   WDT WP WP$ WHADJP WHPP WHNP
#  5 WHPP  1   IN TO FW

if __name__ == "__main__":
    print "Running doctest"
    import doctest
    doctest.testmod()

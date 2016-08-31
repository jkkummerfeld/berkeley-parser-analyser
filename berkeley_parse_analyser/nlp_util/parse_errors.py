#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

class ParseErrorSet:
    def __init__(self, gold=None, test=None, include_terminals=False):
        self.missing = []
        self.crossing = []
        self.extra = []
        self.POS = []
        self.spans = {}

        if gold is not None and test is not None:
            errors = get_errors(test, gold, include_terminals)
            for error in errors:
                self.add_error(error[0], error[1], error[2], error[3])

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
        elif etype == 'diff POS':
            self.POS.append(error)

    def is_extra(self, node):
        if node.span in self.spans:
            if node.label in self.spans[node.span]:
                for error in self.spans[node.span][node.label]:
                    if error[0] == 'extra':
                        return True
        return False

    def __len__(self):
        return len(self.missing) + len(self.extra) + len(self.crossing) + (2*len(self.POS))

def get_errors(test, gold, include_terminals=False):
    ans = []

    # Different POS
    if include_terminals:
        for tnode in test:
            if tnode.word is not None:
                for gnode in gold:
                    if gnode.word is not None and gnode.span == tnode.span:
                        if gnode.label != tnode.label:
                            ans.append(('diff POS', tnode.span, tnode.label, tnode, gnode.label))

    test_spans = [(span.span[0], span.span[1], span) for span in test]
    test_spans.sort()
    test_span_set = {}
    to_remove = []
    for span in test_spans:
        if span[2].is_terminal():
            to_remove.append(span)
            continue
        key = (span[0], span[1], span[2].label)
        if key not in test_span_set:
            test_span_set[key] = 0
        test_span_set[key] += 1
    for span in to_remove:
        test_spans.remove(span)

    gold_spans = [(span.span[0], span.span[1], span) for span in gold]
    gold_spans.sort()
    gold_span_set = {}
    to_remove = []
    for span in gold_spans:
        if span[2].is_terminal():
            to_remove.append(span)
            continue
        key = (span[0], span[1], span[2].label)
        if key not in gold_span_set:
            gold_span_set[key] = 0
        gold_span_set[key] += 1
    for span in to_remove:
        gold_spans.remove(span)

    # Extra
    for span in test_spans:
        key = (span[0], span[1], span[2].label)
        if key in gold_span_set and gold_span_set[key] > 0:
            gold_span_set[key] -= 1
        else:
            ans.append(('extra', span[2].span, span[2].label, span[2]))

    # Missing and crossing
    for span in gold_spans:
        key = (span[0], span[1], span[2].label)
        if key in test_span_set and test_span_set[key] > 0:
            test_span_set[key] -= 1
        else:
            name = 'missing'
            for tspan in test_span_set:
                if tspan[0] < span[0] < tspan[1] < span[1]:
                    name = 'crossing'
                    break
                if span[0] < tspan[0] < span[1] < tspan[1]:
                    name = 'crossing'
                    break
            ans.append((name, span[2].span, span[2].label, span[2]))
    return ans

def counts_for_prf(test, gold, include_root=False, include_terminals=False):
    # Note - currently assumes the roots match
    tcount = 0
    for node in test:
        if node.is_terminal() and not include_terminals:
            continue
        if node.parent is None and not include_root:
            continue
        tcount += 1
    gcount = 0
    for node in gold:
        if node.is_terminal() and not include_terminals:
            continue
        if node.parent is None and not include_root:
            continue
        gcount += 1
    match = tcount
    errors = ParseErrorSet(gold, test, True)
    match = tcount - len(errors.extra)
    if include_terminals:
        match -= len(errors.POS)
    return match, gcount, tcount, len(errors.crossing), len(errors.POS)

if __name__ == '__main__':
    print "No unit testing implemented for Error_Set"

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

from .pstree import clone_and_find, PSTree

def change_label_by_node(node, new_label, in_place):
    if not in_place:
        node = clone_and_find(node)
    node.label = new_label
    return (True, (node.root(), node))

def change_label_by_span(tree, new_label, span, cur_label, in_place=True):
    tree = tree.root()
    for node in tree:
        if node.span == span and node.label == cur_label:
            return change_label_by_node(node, new_label, in_place)
    return (False, "Failed to find node with ({}, {} - {})".format(cur_label, *span))

def change_label(tree, new_label, span=None, cur_label=None, in_place=True):
    if span is None and cur_label is None:
        return change_label_by_node(tree, new_label, in_place)
    elif span is not None and cur_label is not None:
        return change_label_by_span(tree, new_label, span, cur_label, in_place)
    else:
        raise Exception("Invalid combination of arguments for change label request")


def add_node(tree, span, label, position=0, in_place=True):
    '''Introduce a new node in the tree.  Position indicates what to do when a
    node already exists with the same span.  Zero indicates above any current
    nodes, one indicates beneath the first, and so on.'''
    tree = tree.root()
    if not in_place:
        tree = tree.clone()

    # Find the node(s) that should be within the new span
    nodes = tree.get_spanning_nodes(*span)
    # Do not operate on the root node
    if nodes[0].parent is None:
        nodes = nodes[0].subtrees[:]
    for i in range(position):
        if len(nodes) > 1:
            return (False, "Position {} is too deep".format(position))
        nodes[0] = nodes[0].subtrees[0]
    nodes.sort(key=lambda x: x.span)

    # Check that all of the nodes are at the same level
    parent = None
    for node in nodes:
        if parent is None:
            parent = node.parent
        if parent != node.parent:
            return (False, "The span ({} - {}) would cross brackets".format(*span))

    # Create the node
    nnode = PSTree(None, label, span, parent)
    position = parent.subtrees.index(nodes[0])
    parent.subtrees.insert(position, nnode)

    # Move the subtrees
    for node in nodes:
        node.parent.subtrees.remove(node)
        nnode.subtrees.append(node)
        node.parent = nnode

    return (True, (tree, nnode))


def remove_node_by_node(node, in_place):
    if not in_place:
        node = clone_and_find(node)
    parent = node.parent
    position = parent.subtrees.index(node)
    init_position = position
    parent.subtrees.pop(position)
    for subtree in node.subtrees:
        subtree.parent = parent
        parent.subtrees.insert(position, subtree)
        position += 1
    return (True, (parent, node, init_position, position))

def remove_node_by_span(tree, span, label, position, in_place):
    '''Delete a node from the tree.  Position indicates what to do when multiple
    nodes of the requested type exist.  Zero indicates to remove the top node,
    one indicates to remove the second, and so on.'''
    nodes = tree.get_nodes('all', span[0], span[1])
    nodes = [node for node in nodes if node.label == label]
    if len(nodes) <= position:
        return (False, "No node matching {} ({}, {} - {}) found".format(position, label, *span))
    return remove_node_by_node(nodes[position], in_place)

def remove_node(tree, span=None, label=None, position=None, in_place=True):
    if span is None and label is None:
        return remove_node_by_node(tree, in_place)
    elif span is not None and label is not None:
        if position is None:
            position = 0
        return remove_node_by_span(tree, span, label, position, in_place)
    else:
        raise Exception("Invalid combination of arguments for remove node request")


def move_nodes(nodes, new_parent, in_place=True, remove_empty=True, remove_trivial_unary=True):
    if not in_place:
        nodes = clone_and_find(nodes + [new_parent])
        new_parent = nodes[-1]
        nodes = nodes[:-1]

    # Find the insertion point in the new parent's subtrees
    old_parent = nodes[0].parent
    nodes.sort(key=lambda x: x.span)
    node_span = (nodes[0].span[0], nodes[-1].span[1])
    insertion_point = 0
    if new_parent.subtrees[0].span[0] == node_span[1]:
        # Inserting before all that are there currently
        pass
    elif new_parent.subtrees[0].span[0] == node_span[0]:
        # Inserting before all that are there currently
        pass
    else:
        for subtree in new_parent.subtrees:
            if subtree.span[0] == node_span[1]:
                break
            insertion_point += 1
            if subtree.span[1] == node_span[0]:
                break
        if insertion_point > len(new_parent.subtrees):
            return (False, "new_parent did not have suitable insertion point")

    # Move the nodes across
    for node in nodes:
        node.parent.subtrees.remove(node)
        new_parent.subtrees.insert(insertion_point, node)
        node.parent = new_parent
        insertion_point += 1

    # If the nodes left behind are empty, remove them
    to_check_for_unary = old_parent
    if remove_empty and len(old_parent.subtrees) == 0:
        to_remove = old_parent
        while len(to_remove.parent.subtrees) == 1:
            to_remove = to_remove.parent
        to_remove.parent.remove(to_remove)

        # If the removal applies, then we will need to check at that level for
        # unaries, rather than down at the old_parent
        to_check_for_unary = to_remove.parent

    # Remove trivial unaries
    if remove_trivial_unary:
        to_check = to_check_for_unary
        if len(to_check.subtrees) == 1 and to_check.label == to_check.subtrees[0].label:
            to_check.subtrees = to_check.subtrees[0].subtrees
            for subtree in to_check.subtrees:
                subtree.parent = to_check

    new_parent.root().calculate_spans()

    return (True, (new_parent.root(), nodes, new_parent))

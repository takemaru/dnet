#!/usr/bin/env python

import math
import sys

import grid.core

max_current     = 300
sending_voltage = 6600 / math.sqrt(3)
min_voltage     = 6300 / math.sqrt(3)

def define_subgraphs():
    edges = []
    sorted_sections = []
    for s in sorted(data.switches):
        ns = set()
        for t in data.find_neighbors(s):
            if t in data.sections:
                ns.add(t)
        neighbors = set()
        is_root = False
        for t in sorted(ns):
            for u in data.find_neighbors(t):
                if u in data.sections and u < t:
                    t = u
            neighbors.add(t)
            if t not in sorted_sections:
                sorted_sections.append(t)
        edge = [sorted_sections.index(t) + 1 for t in sorted(neighbors)]
        assert len(edge) == 2
        edges.append(edge)
    assert len(edges) == len(data.switches)

    roots = set()
    for s in data.sections:
        if data.sections[s]["substation"]:
            for t in data.find_neighbors(s):
                if t < s:
                    s = t
            roots.add(sorted_sections.index(s) + 1)
    assert len(roots) == len(data.get_root_sections())

    f = open(dir + "grid.subgraphs", "w")
    f.write("rforest " + " ".join([str(r) for r in sorted(roots)]) + "\n")
    f.write("%d\n" % len(sorted_sections))
    for edge in edges:
        f.write("%d %d\n" % (edge[0], edge[1]))
    f.close()

def find_neighbor_switches(s, processed_sections):
    switches = set()
    if s in data.switches:
        for t in data.find_neighbors(s) - processed_sections:
            assert t in data.sections
            processed_sections.add(t)
            for u in find_neighbor_switches(t, processed_sections.copy()):
                switches.add(u)
    else:
        processed_sections.add(s)
        for t in data.find_neighbors(s) - processed_sections:
            if t in data.switches:
                switches.add(t)
            else:
                for u in find_neighbor_switches(t, processed_sections.copy()):
                    switches.add(u)
    return switches - set([s])

def find_surrounding_switches(root, closed_switches):
    if len(closed_switches) > 0:
        return set([t for s in closed_switches for t in find_neighbor_switches(s, set())]) - \
            closed_switches
    else:
        return find_neighbor_switches(root, set())

def find_border_switches(root):
    assert data.sections[root]["substation"]
    border = set()
    for r in data.get_root_sections() - set([root]):
        for s in find_neighbor_switches(r, set()):
            border.add(s)
    return border

def is_tree(branches):
    '''inspired by networkx.algorithms.cycles'''
    gnodes = set(grid.core.flatten(branches))
    while gnodes:
        root = gnodes.pop()
        stack = [root]
        pred = { root: root }
        used = { root: set() }
        while stack:
            z = stack.pop()
            zused = used[z]
            nbrs = set([e[1] for e in branches
                        if e[0] == z] + [e[0] for e in branches if e[1] == z])
            for nbr in nbrs:
                if nbr not in used:
                    pred[nbr] = z
                    stack.append(nbr)
                    used[nbr] = set([z])
                elif nbr not in zused:
                    return False
        gnodes -= set(pred)
        root = None
    return True

def satisfies_electric_constraints(root, closed_switches):
    branches = data.build_tree(root, closed_switches, set())
    if not grid.core.is_tree(branches):
        return False

    current = data.calc_current(root, branches)
    if abs(current[root][0]) > max_current or \
            abs(current[root][1]) > max_current or \
            abs(current[root][2]) > max_current:
        return False
    assert len(current) == len(set(grid.core.flatten(branches)))

    leaves = set(grid.core.flatten(branches)) - set([b[0] for b in branches])
    for s in leaves:
        voltage_drop = [
            current[s][0] * data.sections[s]["impedance"][0] / 2,
            current[s][1] * data.sections[s]["impedance"][1] / 2,
            current[s][2] * data.sections[s]["impedance"][2] / 2,
        ]
        bs = [b for b in branches if b[1] == s]
        assert len(bs) == 1
        s, t = bs[0]
        while True:
            voltage_drop[0] += current[s][0] * data.sections[s]["impedance"][0]
            voltage_drop[1] += current[s][1] * data.sections[s]["impedance"][1]
            voltage_drop[2] += current[s][2] * data.sections[s]["impedance"][2]
            upper_branch = [b for b in branches if b[1] == s]
            assert len(upper_branch) <= 1
            if len(upper_branch) == 1:
                s, t = upper_branch[0]
            else:
                break
        if abs(sending_voltage - voltage_drop[0]) < min_voltage or \
                abs(sending_voltage - voltage_drop[1]) < min_voltage or \
                abs(sending_voltage - voltage_drop[2]) < min_voltage:
            return False

    return True

def write_bitmap(f, closed_switches, open_switches):
    bits = []
    for s in sorted(data.switches.keys()):
        if s in closed_switches:
            bits.append("1")
        elif s in open_switches:
            bits.append("0")
        else:
            bits.append("*")
    f.write(" ".join(bits) + "\n")

def do_enumerate_bitmaps(root, f, closed_switches, fixed_switches):
    unfixed_switches = find_surrounding_switches(root, closed_switches) - fixed_switches
    if len(unfixed_switches) == 0:
        return
    s = sorted(unfixed_switches)[0]
    fixed_switches.add(s)
    do_enumerate_bitmaps(root, f, closed_switches.copy(), fixed_switches.copy())
    closed_switches.add(s)
    if satisfies_electric_constraints(root, closed_switches):
        write_bitmap(f, closed_switches, find_surrounding_switches(root, closed_switches))
        do_enumerate_bitmaps(root, f, closed_switches.copy(), fixed_switches.copy())

def enumerate_bitmaps(root):
    f = open(dir + "grid-%s.bitmaps" % root, "w")
    if satisfies_electric_constraints(root, set()):
        write_bitmap(f, set(), find_surrounding_switches(root, set()))
    do_enumerate_bitmaps(root, f, set(), find_border_switches(root))
    f.close()

if __name__ == '__main__':
    dir = sys.argv[1] + "/" if len(sys.argv) > 1 else "./"
    data = grid.core.Data(sys.stdin)

    define_subgraphs()

    for root in data.get_root_sections():
        enumerate_bitmaps(root)

    msg = "Build a diagram by the following command:\n"
    cmd = "  /path/to/solver -n %d -t diagram %sgrid.subgraphs '&' " % (len(data.switches), dir) + \
        " '&' ".join(sorted([dir + "grid-%s.bitmaps" % s for s in data.sections if data.sections[s]["substation"]])) + \
        " > %sgrid.diagram\n" % dir
    sys.stderr.write(msg + cmd)

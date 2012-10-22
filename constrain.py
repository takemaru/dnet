#!/usr/bin/env python

import math
import sys

import util

dir = sys.argv[1] + "/" if len(sys.argv) > 1 else "./"

max_current     = 300
sending_voltage = 6600 / math.sqrt(3)
min_voltage     = 6300 / math.sqrt(3)

data = util.Data(sys.stdin)

for s in data.sections.values():
    l = s["load"]
    i = s["impedance"]
    s["load"]      = [l[0] + l[1] * 1j, l[2] + l[3] * 1j, l[4] + l[5] * 1j]
    s["impedance"] = [i[0] + i[1] * 1j, i[2] + i[3] * 1j, i[4] + i[5] * 1j]

def define_subgraphs():
    edges = []
    sorted_sections = []
    for s in sorted(data.switches):
        ns = set()
        for t in util.find_neighbors(s, data.nodes):
            if t in data.sections:
                ns.add(t)
        neighbors = set()
        is_root = False
        for t in sorted(ns):
            for u in util.find_neighbors(t, data.nodes):
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
            for t in util.find_neighbors(s, data.nodes):
                if t < s:
                    s = t
            roots.add(sorted_sections.index(s) + 1)
    assert len(roots) == len([s for s in data.sections.values() if s["substation"]])

    f = open(dir + "grid.subgraphs", "w")
    f.write("rforest " + " ".join([str(r) for r in sorted(roots)]) + "\n")
    f.write("%d\n" % len(sorted_sections))
    for edge in edges:
        f.write("%d %d\n" % (edge[0], edge[1]))
    f.close()

def find_neighbor_switches(s, passed_sections):
    switches = set()
    if s in data.switches:
        for t in util.find_neighbors(s, data.nodes) - passed_sections:
            assert t in data.sections
            passed_sections.add(t)
            for u in find_neighbor_switches(t, passed_sections.copy()):
                switches.add(u)
    else:
        passed_sections.add(s)
        for t in util.find_neighbors(s, data.nodes) - passed_sections:
            if t in data.switches:
                switches.add(t)
            else:
                for u in find_neighbor_switches(t, passed_sections.copy()):
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
    other_roots = [_ for _ in data.sections.keys() if data.sections[_]["substation"] and _ <> root]
    border = set()
    for r in other_roots:
        for s in find_neighbor_switches(r, set()):
            border.add(s)
    return border

def build_tree(root, closed_switches, passed):
    branches = []
    neighbors = util.find_neighbors(root, data.nodes) - passed
    if len(neighbors) == 1:
        s = neighbors.pop()
        assert s in data.switches
        if s in closed_switches:
            t = (util.find_neighbors(s, data.nodes) - set([root])).pop()
            branches.append((root, t))
            branches.extend(build_tree(t, closed_switches - set([s]), passed | set([root, s, t])))
    elif len(neighbors) > 1: # junction
        for s in neighbors:
            assert s in data.sections, (root, neighbors, s)
            branches.append((root, s))
        for s in neighbors:
            branches.extend(build_tree(s, closed_switches.copy(), passed | set([root]) | neighbors))
    return branches

def is_tree(branches):
    '''inspired by networkx.algorithms.cycles'''
    gnodes = set(util.flatten(branches))
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
    branches = build_tree(root, closed_switches, set())
    if not is_tree(branches):
        return False
    leaves = set(util.flatten(branches)) - set([b[0] for b in branches])

    current = {}
    for branch in branches:
        s, t = branch
        load = data.sections[t]["load"]
        if t not in current:
            current[t] = [0, 0, 0]
        current[t][0] += load[0]
        current[t][1] += load[1]
        current[t][2] += load[2]
        while True:
            if s not in current:
                current[s] = [0, 0, 0]
            current[s][0] += load[0]
            current[s][1] += load[1]
            current[s][2] += load[2]
            upper_branch = [b for b in branches if b[1] == s]
            assert len(upper_branch) <= 1
            if len(upper_branch) == 1:
                s, t = upper_branch[0]
            else:
                break
    load = data.sections[root]["load"]
    current[root][0] += load[0]
    current[root][1] += load[1]
    current[root][2] += load[2]
    if abs(current[root][0]) > max_current or \
            abs(current[root][1]) > max_current or \
            abs(current[root][2]) > max_current:
        return False
    assert len(current) == len(set(util.flatten(branches)))

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

define_subgraphs()

for root in sorted([s for s in data.sections if data.sections[s]["substation"]]):
    enumerate_bitmaps(root)

print "solver -n %d -t diagram %sgrid.subgraphs '&'" % (len(data.switches), dir),
print " '&' ".join(sorted([dir + "grid-%s.bitmaps" % s for s in data.sections if data.sections[s]["substation"]])),
print "> %sgrid.diagram" % dir

#assert find_neighbor_switches("section_0305", set()) == set(['switch_0015', 'switch_0014'])
#assert find_neighbor_switches("section_-001", set()) == set(['switch_0010', 'switch_0014'])
#assert find_neighbor_switches("switch_0008", set()) == set(['switch_0009', 'switch_0007'])
#assert find_neighbor_switches("switch_0009", set()) == set(['switch_0008', 'switch_0010', 'switch_0006'])
#
#assert find_surrounding_switches("section_-001", set()) == set(['switch_0010', 'switch_0014'])
#assert find_surrounding_switches("section_-001", set(["switch_0009", "switch_0010", "switch_0014"])) == set(['switch_0008', 'switch_0006', 'switch_0015'])
#
#assert find_border_switches("section_-001") == set(['switch_0013', 'switch_0001', 'switch_0011', 'switch_0016'])
#
#assert build_tree("section_-001", set(), set()) == [('section_-001', 'section_0303'), ('section_-001', 'section_0302')]
#assert build_tree("section_-001", set(["switch_0009", "switch_0010", "switch_0014"]), set()) == [('section_-001', 'section_0303'), ('section_-001', 'section_0302'), ('section_0303', 'section_0305'), ('section_0302', 'section_0300'), ('section_0300', 'section_0299'), ('section_0300', 'section_0298'), ('section_0298', 'section_0296')]
#
#assert is_tree([("section_-001", "section_0302"), ("section_-001", "section_0303"), ("section_0302", "section_0300")])
#assert not is_tree([("section_-001", "section_0302"), ("section_-001", "section_0303"), ("section_0302", "section_0300"), ("section_0300", "section_0303")])
#
#assert satisfies_electric_constraints("section_-001", set())
#assert satisfies_electric_constraints("section_-001", set(["switch_0009", "switch_0010", "switch_0014"]))
#assert not satisfies_electric_constraints("section_-001", set(["switch_0006", "switch_0007", "switch_0008", "switch_0009", "switch_0010", "switch_0014"]))

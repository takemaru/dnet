#!/usr/bin/env python

import networkx as nx
import re
import sys
import unionfind

import util

data = util.Data(sys.stdin)

switches = set(data.switches.keys())
sections = set(data.sections.keys())
roots = set([s for s in data.sections if data.sections[s]["substation"]])
uf = unionfind.UnionFind()
uf.insert_objects(switches | sections - roots)
for s in sorted(switches | sections - roots):
    neighbors = set()
    for n in [m for m in data.nodes if s in m]:
        if [t for t in n if t in roots] == []:
            for t in n:
                neighbors.add(t)
    for t in sorted(neighbors - set([s])):
        uf.union(s, t)

i = 1
comps = {}
for s in sorted(switches):
    c = uf.find(s)
    if c not in comps:
        comps[c] = (i, set())
        i += 1
    comps[c][1].add(s)
    for t in data.find_neighbors(s):
        comps[c][1].add(t)
assert sum([len(c[1]) for c in comps.values()]) == len(switches | sections - roots)

comps = [comps[c][1] for c in sorted(comps, key=lambda c: comps[c][0])]

s = "switch"
for c in comps:
    switches = [t for t in c if t in data.switches]
    assert s < min(switches), "switches must be ordered by independent components"
    s = max(switches)

assert len([t for s in data.sections if s < 0
            for t in data.find_neighbors(s) if t in data.switches]) == 0, \
    "root sections must be connected to a junction, not a switch"

class Node:
    def __init__(self, str):
        n, v, l, h, _ = re.split(r"[\W]+", str)
        self.n = n
        self.v = int(v)
        self.l = l
        self.h = h

    def __repr__(self):
        return "%s: (~%d?%s:%s)" % (self.n, self.v, self.l, self.h)

nodes = { "1": Node("1: (~0?1:1)") }
for line in open(sys.argv[1]):
    n = Node(line)
    nodes[n.n] = n
    if n.v == 1:
        root = n.n

g = nx.DiGraph()

def calc_loss(closed_switches, comp, roots):
    current = {}
    for root in roots:
        passed = set([s for s in data.find_neighbors(root) if s in data.sections])
        branches = data.build_tree(root, closed_switches, passed)
        assert util.is_tree(branches)
        current.update(data.calc_current(root, branches))
    sections = [s for s in comp if s in data.sections]
    return sum([abs(current[s][i]**2 * data.sections[s]["impedance"][i].real)
                    for s in sections for i in range(3)])

def find_configs(n, comp, closed_switches):
    n = nodes[n]
    configs = []
    if "switch_%04d" % n.v not in comp:
        configs.append((closed_switches, n.n))
    else:
        if n.l <> "0":
            configs.extend(find_configs(n.l, comp, closed_switches.copy()))
        assert n.h <> "0"
        closed_switches.add(n.v)
        configs.extend(find_configs(n.h, comp, closed_switches.copy()))
    return configs

def rebuild(entries, comp):
    roots = set()
    for s in comp:
        if s in data.sections:
            for t in data.find_neighbors(s):
                if t in data.sections and data.sections[t]["substation"]:
                    roots.add(s)
                    break
    next_entries = set()
    loss_cache = {}
    for n in entries:
        for closed_switches, m in find_configs(n, comp, set()):
            next_entries.add(m)
            key = ','.join([str(s) for s in sorted(closed_switches)])
            loss = loss_cache[key] if key in loss_cache else calc_loss(closed_switches, comp, roots)
            if not(n in g and m in g[n] and loss > g[n][m]["weight"]):
                g.add_edge(n, m, weight=loss, config=closed_switches)
    return next_entries

entries = set([root])
for comp in comps:
    entries = rebuild(entries, comp)

path = nx.dijkstra_path(g, root, "1")

loss = 0
closed_switches = []
for i in range(len(path) - 1):
    x, y = path[i], path[i + 1]
    loss += g[x][y]["weight"]
    closed_switches.extend(list(g[x][y]["config"]))
print loss
print sorted(closed_switches)

#assert find_configs(root, comps[0], set()) == [(set([1, 4, 5, 6, 7, 8, 9, 10]), '1e'), (set([1, 3, 4, 6, 7, 8, 9, 10]), '2b'), (set([1, 3, 4, 5, 6, 8, 9, 10]), '2b'), (set([1, 3, 4, 5, 6, 7, 9, 10]), '2b'), (set([1, 3, 4, 5, 6, 7, 8, 10]), '2b'), (set([1, 2, 5, 6, 7, 8, 9, 10]), '1e'), (set([1, 2, 4, 5, 7, 8, 9, 10]), '2b'), (set([1, 2, 3, 6, 7, 8, 9, 10]), '2b'), (set([1, 2, 3, 5, 6, 8, 9, 10]), '2b'), (set([1, 2, 3, 5, 6, 7, 9, 10]), '11'), (set([1, 2, 3, 5, 6, 7, 8, 10]), '11'), (set([1, 2, 3, 4, 7, 8, 9, 10]), '2b'), (set([1, 2, 3, 4, 5, 8, 9, 10]), '2b'), (set([1, 2, 3, 4, 5, 7, 9, 10]), '2d'), (set([1, 2, 3, 4, 5, 7, 8, 10]), '2d')]
#assert find_configs("2b", comps[1], set()) == [(set([12, 13]), '2f'), (set([11, 13]), '2f'), (set([11, 12]), '2f')]
#assert find_configs("2f", comps[2], set()) == [(set([16, 15]), '1'), (set([16, 14]), '1'), (set([14, 15]), '1')]

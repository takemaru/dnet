#!/usr/bin/env python

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
    for t in util.find_neighbors(s, data.nodes):
        comps[c][1].add(t)
assert sum([len(c[1]) for c in comps.values()]) == len(switches | sections - roots)

comps = [comps[c][1] for c in sorted(comps, key=lambda c: comps[c][0])]

s = "switch"
for c in comps:
    switches = [t for t in c if t in data.switches]
    assert s < min(switches), "switches must be ordered by independent components"
    s = max(switches)

assert len([t for s in data.sections if s < 0
            for t in util.find_neighbors(s, data.nodes) if t in data.switches]) == 0, \
    "root sections must be connected to a junction, not a switch"

class Node:
    def __init__(self, str):
        n, v, l, h, _ = re.split(r"[\W]+", str)
        self.n = n
        self.v = int(v)
        self.l = l
        self.h = h

nodes = {}
for line in open(sys.argv[1]):
    n = Node(line)
    nodes[n.n] = n
    if n.v == 1:
        entries = set([n])

for c in comps:
    entries = rebuild(entries, c)

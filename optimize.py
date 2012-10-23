#!/usr/bin/env python

import networkx as nx
import re
import sys
import unionfind

import util

class Node:
    def __init__(self, str):
        n, v, l, h, _ = re.split(r"[\W]+", str)
        self.n = n
        self.v = int(v)
        self.l = l
        self.h = h

def find_components():
    switches = set(data.switches.keys())
    sections = set(data.sections.keys())
    roots = data.get_root_sections()
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

    return comps

def find_configs(n, comp, closed_switches):
    n = nodes[n]
    configs = []
    if "switch_%04d" % n.v not in comp:
        configs.append((closed_switches, n.n))
    else:
        if n.l <> "0":
            configs.extend(find_configs(n.l, comp, closed_switches.copy()))
        assert n.h <> "0"
        closed_switches.add("switch_%04d" % n.v)
        configs.extend(find_configs(n.h, comp, closed_switches.copy()))
    return configs

def calc_component_loss(comp_roots, closed_switches):
    loss = 0
    for root, barrier in comp_roots:
        loss += data.calc_loss(root, closed_switches, barrier)
    return loss

def rebuild(entries, comp):
    comp_roots = []
    for s in comp:
        if s in data.sections:
            for t in data.find_neighbors(s):
                if t in data.sections and data.sections[t]["substation"]:
                    assert not data.sections[s]["substation"]
                    barrier = set([u for u in data.find_neighbors(s) if u in data.sections])
                    comp_roots.append((s, barrier))
                    break

    next_entries = set()
    loss_cache = {}
    for n in entries:
        for closed_switches, m in find_configs(n, comp, set()):
            next_entries.add(m)
            key = ','.join([str(s) for s in sorted(closed_switches)])
            if key in loss_cache:
                loss = loss_cache[key]
            else:
                loss = calc_component_loss(comp_roots, closed_switches)
            if not(n in graph and m in graph[n] and loss > graph[n][m]["weight"]):
                graph.add_edge(n, m, weight=loss, config=closed_switches)

    return next_entries

if __name__ == '__main__':
    data = util.Data(sys.stdin)

    comps = find_components()

    nodes = { "1": Node("1: (~0?1:1)") }
    for line in open(sys.argv[1]):
        n = Node(line)
        nodes[n.n] = n
        if n.v == 1:
            root = n.n

    graph = nx.DiGraph()

    entries = set([root])
    for comp in comps:
        entries = rebuild(entries, comp)

    path = nx.dijkstra_path(graph, root, "1")

    comp_loss = 0
    closed_switches = []
    for i in range(len(path) - 1):
        x, y = path[i], path[i + 1]
        comp_loss += graph[x][y]["weight"]
        closed_switches.extend(list(graph[x][y]["config"]))
    closed_switches = set(closed_switches)
    open_switches = sorted(set(data.switches.keys()) - closed_switches)

    loss = 0
    for root in data.get_root_sections():
        loss += data.calc_loss(root, closed_switches, set())

    lower_bound = 0
    for i in range(3):
        total_loads = sum([data.sections[s]["load"][i] for s in data.sections])
        resistance_sum = \
            sum([1 / data.sections[s]["impedance"][i].real for s in data.get_root_sections()])
        for root in data.get_root_sections():
            resistance = data.sections[root]["impedance"][i].real
            current = total_loads / (resistance * resistance_sum)
            lower_bound += abs(current ** 2 * resistance)

    print "minimum_loss:", "%g" % loss
    print "loss_without_root_sections:", "%g" % comp_loss
    print "lower_bound_of_minimum_loss:", "%g" % (lower_bound + comp_loss)
    print "open_switches:", open_switches
    if "original_number" in data.switches.values()[0]:
        print "open_switches_in_original_numbers:", \
            [data.switches[s]["original_number"] for s in open_switches]

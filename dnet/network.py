# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from dnet.configs import Configs
from dnet.unionfind import UnionFind
from graphillion import GraphSet
from math import sqrt
import networkx as nx
import yaml

def flatten(L):
    if isinstance(L, (list, tuple, set)):
        if isinstance(L, (tuple, set)):
            L = list(L)
        if L == []:
            return L
        else:
            return flatten(L[0]) + flatten(L[1:])
    else:
        return [L]

def is_tree(branches):
    '''inspired by networkx.algorithms.cycles'''
    gnodes = set(flatten(branches))
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

class Node(object):
    def __init__(self, str):
        n, v, l, h = str.split()
        self.n = n
        self.v = int(v)
        self.l = l
        self.h = h

class Network(object):
    def __init__(self, file_or_dir, format=None):
        if format == 'fukui-tepco':
            from dnet.converter import FukuiTepcoConverter
            obj = yaml.load(FukuiTepcoConverter(file_or_dir).convert())
        else:
            obj = yaml.load(open(file_or_dir))
        self.nodes = obj['nodes']
        self.switches = obj['switches']
        self.sections = obj['sections']
        for s in self.sections.values():
            l = s['load']
            i = s['impedance']
            s['load']      = [l[0] + l[1] * 1j, l[2] + l[3] * 1j, l[4] + l[5] * 1j]
            s['impedance'] = [i[0] + i[1] * 1j, i[2] + i[3] * 1j, i[4] + i[5] * 1j]
        if [l for s in self.sections.values() for l in s['load'] if l.real < 0] <> []:
            sys.stderr.write('Warning: it is assumed that section loads are non-negative\n')
        self.neighbor_cache = {}
        self._switch2edge = {}
        self._edge2switch = {}
        self.build_graph()

    def switch2edge(self, switch):
        if switch in self._switch2edge:
            return self._switch2edge[switch]
        else:
            for s, v in self.switches.iteritems():
                if 'original_number' in v and v['original_number'] == int(switch):
                    return self._switch2edge[s]
        raise KeyError, switch

    def edge2switch(self, edge):
        switch = self._edge2switch[edge]
        if 'original_number' in self.switches[switch]:
            switch = self.switches[switch]['original_number']
        return switch

    def forest2config(self, forest):
        return [self.edge2switch(e) for e in forest]

    def config2forest(self, config):
        return [self.switch2edge(s) for s in config]

    def get_root_sections(self):
        return set([s for s in self.sections if self.sections[s]['substation']])

    def find_neighbors(self, s):
        if s not in self.neighbor_cache:
            self.neighbor_cache[s] = set(flatten([n for n in self.nodes if s in n])) - set([s])
        return self.neighbor_cache[s]

    def build_tree(self, root, closed_switches, processed_elems):
        branches = []
        neighbors = self.find_neighbors(root) - processed_elems
        if len(neighbors) == 1:
            s = neighbors.pop()
            assert s in self.switches
            if s in closed_switches:
                t = (self.find_neighbors(s) - set([root])).pop()
                branches.append((root, t))
                ps = processed_elems | set([root, s, t])
                bs = self.build_tree(t, closed_switches - set([s]), ps)
                branches.extend(bs)
        elif len(neighbors) > 1: # junction
            for s in neighbors:
                assert s in self.sections, (root, neighbors, s)
                branches.append((root, s))
            for s in neighbors:
                ps = processed_elems | set([root]) | neighbors
                bs = self.build_tree(s, closed_switches.copy(), ps)
                branches.extend(bs)
        return branches

    def calc_current(self, root, branches):
        current = { root: [0, 0, 0] }
        for branch in branches:
            s, t = branch
            load = self.sections[t]['load']
            if t not in current:
                current[t] = [0, 0, 0]
            current[t] = [current[t][i] + load[i] for i in range(3)]
            while True:
                if s not in current:
                    current[s] = [0, 0, 0]
                current[s] = [current[s][i] + load[i] for i in range(3)]
                upper_branch = [b for b in branches if b[1] == s]
                assert len(upper_branch) <= 1
                if len(upper_branch) == 1:
                    s, t = upper_branch[0]
                else:
                    break
        load = self.sections[root]['load']
        current[root] = [current[root][i] + load[i] for i in range(3)]
        return current

    def calc_loss(self, root, closed_switches, barrier):
        branches = self.build_tree(root, closed_switches, barrier)
        assert is_tree(branches), 'loop found'
        sections = set([root] + flatten(branches))
        current = self.calc_current(root, branches)
        return sum([self.do_calc_loss(current[s][i], self.sections[s]['impedance'][i].real)
                    for s in sections for i in range(3)])

    def do_calc_loss(self, current, resistance):
        assert not isinstance(resistance, complex)
        return current.real**2 * resistance

    def build_graph(self):
        edges = []
        sorted_sections = []
        for s in sorted(self.switches):
            ns = set()
            for t in self.find_neighbors(s):
                if t in self.sections:
                    ns.add(t)
            neighbors = set()
            is_root = False
            for t in sorted(ns):
                for u in self.find_neighbors(t):
                    if u in self.sections and u < t:
                        t = u
                neighbors.add(t)
                if t not in sorted_sections:
                    sorted_sections.append(t)
            edge = tuple([sorted_sections.index(t) + 1 for t in sorted(neighbors)])
            assert len(edge) == 2
            edges.append(edge)
            self._switch2edge[s] = edge
            self._edge2switch[edge] = s
        assert len(edges) == len(self.switches)

        self.roots = set()
        for s in self.sections:
            if self.sections[s]['substation']:
                for t in self.find_neighbors(s):
                    if t < s:
                        s = t
                self.roots.add(sorted_sections.index(s) + 1)
        assert len(self.roots) == len(self.get_root_sections())

        GraphSet.set_universe(edges, traversal='as-is')

    def define_forests(self):
        return GraphSet.forests(roots=self.roots, is_spanning=True)

    def find_neighbor_switches(self, s, processed_sections):
        switches = set()
        if s in self.switches:
            for t in self.find_neighbors(s) - processed_sections:
                assert t in self.sections
                processed_sections.add(t)
                for u in self.find_neighbor_switches(t, processed_sections.copy()):
                    switches.add(u)
        else:
            processed_sections.add(s)
            for t in self.find_neighbors(s) - processed_sections:
                if t in self.switches:
                    switches.add(t)
                else:
                    for u in self.find_neighbor_switches(t, processed_sections.copy()):
                        switches.add(u)
        return switches - set([s])

    def find_surrounding_switches(self, root, closed_switches):
        if len(closed_switches) > 0:
            return set([t for s in closed_switches for t in self.find_neighbor_switches(s, set())]) - \
                closed_switches
        else:
            return self.find_neighbor_switches(root, set())

    def find_border_switches(self, root):
        assert self.sections[root]['substation']
        border = set()
        for r in self.get_root_sections() - set([root]):
            for s in self.find_neighbor_switches(r, set()):
                border.add(s)
        return border

    def satisfies_electric_constraints(self, root, closed_switches):
        branches = self.build_tree(root, closed_switches, set())
        if not is_tree(branches):
            return False

        current = self.calc_current(root, branches)
        if abs(current[root][0]) > Network.MAX_CURRENT or \
                abs(current[root][1]) > Network.MAX_CURRENT or \
                abs(current[root][2]) > Network.MAX_CURRENT:
            return False
        assert len(current) == len(set(flatten(branches)))

        leaves = set(flatten(branches)) - set([b[0] for b in branches])
        for s in leaves:
            voltage_drop = [current[s][i] * self.sections[s]['impedance'][i] / 2 for i in range(3)]
            bs = [b for b in branches if b[1] == s]
            assert len(bs) == 1
            s, t = bs[0]
            while True:
                voltage_drop = \
                    [voltage_drop[i] + current[s][i] * self.sections[s]['impedance'][i] for i in range(3)]
                upper_branch = [b for b in branches if b[1] == s]
                assert len(upper_branch) <= 1
                if len(upper_branch) == 1:
                    s, t = upper_branch[0]
                else:
                    break
            if abs(Network.SENDING_VOLTAGE - voltage_drop[0]) < Network.VOLTAGE_RANGE[0] or \
                    abs(Network.SENDING_VOLTAGE - voltage_drop[1]) < Network.VOLTAGE_RANGE[0] or \
                    abs(Network.SENDING_VOLTAGE - voltage_drop[2]) < Network.VOLTAGE_RANGE[0] or \
                    Network.VOLTAGE_RANGE[1] < abs(Network.SENDING_VOLTAGE - voltage_drop[0]) or \
                    Network.VOLTAGE_RANGE[1] < abs(Network.SENDING_VOLTAGE - voltage_drop[1]) or \
                    Network.VOLTAGE_RANGE[1] < abs(Network.SENDING_VOLTAGE - voltage_drop[2]):
                return False

        return True

    def find_trees(self, closed_switches, open_switches):
        closed_switches = [self._switch2edge[s] for s in closed_switches]
        open_switches = [self._switch2edge[s] for s in open_switches]
        return GraphSet({'include': closed_switches, 'exclude': open_switches})

    def do_enumerate_trees(self, root, closed_switches, fixed_switches):
        gs = GraphSet()
        unfixed_switches = self.find_surrounding_switches(root, closed_switches) - fixed_switches
        if len(unfixed_switches) == 0:
            return gs
        s = sorted(unfixed_switches)[0]
        fixed_switches.add(s)
        gs |= self.do_enumerate_trees(root, closed_switches.copy(), fixed_switches.copy())
        closed_switches.add(s)
        if self.satisfies_electric_constraints(root, closed_switches):
            gs |= self.find_trees(closed_switches, self.find_surrounding_switches(root, closed_switches))
            gs |= self.do_enumerate_trees(root, closed_switches.copy(), fixed_switches.copy())
        return gs

    def enumerate_trees(self, root):
        gs = GraphSet()
        if self.satisfies_electric_constraints(root, set()):
            gs = self.find_trees(set(), self.find_surrounding_switches(root, set()))
        return gs | self.do_enumerate_trees(root, set(), self.find_border_switches(root))

    def enumerate(self):
        gs = self.define_forests()
        for root in self.get_root_sections():
            gs &= self.enumerate_trees(root)
        return Configs(self, gs)

    def loss(self, config):
        loss = 0
        for root in self.get_root_sections():
            loss += self.calc_loss(root, set(config), set())
        return loss

    def find_components(self):
        switches = set(self.switches.keys())
        sections = set(self.sections.keys())
        roots = self.get_root_sections()
        uf = UnionFind()
        uf.insert_objects(switches | sections - roots)
        for s in sorted(switches | sections - roots):
            neighbors = set()
            for n in [m for m in self.nodes if s in m]:
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
            for t in self.find_neighbors(s):
                comps[c][1].add(t)
        assert sum([len(c[1]) for c in comps.values()]) == len(switches | sections - roots)

        comps = [comps[c][1] for c in sorted(comps, key=lambda c: comps[c][0])]

        s = 'switch'
        for c in comps:
            switches = [t for t in c if t in self.switches]
            assert s < min(switches), 'switches must be ordered by independent components'
            s = max(switches)

        assert len([t for s in self.sections if s < 0
                    for t in self.find_neighbors(s) if t in self.switches]) == 0, \
                    'root sections must be connected to a junction, not a switch'

        return comps

    def find_configs(self, n, comp, closed_switches):
        n = self.nodes[n]
        configs = []
        if 'switch_%04d' % n.v not in comp:
            configs.append((closed_switches, n.n))
        else:
            if n.l <> 'B':
                configs.extend(self.find_configs(n.l, comp, closed_switches.copy()))
            assert n.h <> 'B'
            closed_switches.add('switch_%04d' % n.v)
            configs.extend(self.find_configs(n.h, comp, closed_switches.copy()))
        return configs

    def calc_component_loss(self, comp_roots, closed_switches):
        loss = 0
        for root, barrier in comp_roots:
            loss += self.calc_loss(root, closed_switches, barrier)
        return loss

    def rebuild(self, entries, comp):
        comp_roots = []
        for s in comp:
            if s in self.sections:
                for t in self.find_neighbors(s):
                    if t in self.sections and self.sections[t]['substation']:
                        assert not self.sections[s]['substation']
                        barrier = set([u for u in self.find_neighbors(s) if u in self.sections])
                        comp_roots.append((s, barrier))
                        break

        next_entries = set()
        loss_cache = {}
        for n in entries:
            for closed_switches, m in self.find_configs(n, comp, set()):
                next_entries.add(m)
                key = ','.join([str(s) for s in sorted(closed_switches)])
                if key in loss_cache:
                    loss = loss_cache[key]
                else:
                    loss = self.calc_component_loss(comp_roots, closed_switches)
                if not(n in self.graph and m in self.graph[n] and loss > self.graph[n][m]['weight']):
                    self.graph.add_edge(n, m, weight=loss, config=closed_switches)

        return next_entries

    def optimize(self, gs):
        comps = self.find_components()

        self.nodes = { 'B': Node('B %d B B ' % (len(self.switches) + 1)),
                       'T': Node('T %d T T ' % (len(self.switches) + 1)) }
        root = None
        for line in gs.dumps().split('\n'):
            if line.startswith('.'):
                break
            n = Node(line)
            self.nodes[n.n] = n
            root = n.n

        self.graph = nx.DiGraph()

        entries = set([root])
        for comp in comps:
            entries = self.rebuild(entries, comp)

        path = nx.dijkstra_path(self.graph, root, 'T')

        comp_loss = 0
        closed_switches = []
        for i in range(len(path) - 1):
            x, y = path[i], path[i + 1]
            comp_loss += self.graph[x][y]['weight']
            closed_switches.extend(list(self.graph[x][y]['config']))
        closed_switches = set(closed_switches)
        open_switches = sorted(set(self.switches.keys()) - closed_switches)

        loss = 0
        for root in self.get_root_sections():
            loss += self.calc_loss(root, closed_switches, set())

        lower_bound = 0
        for i in range(3):
            total_loads = sum([self.sections[s]['load'][i] for s in self.sections])
            resistance_sum = \
                sum([1 / self.sections[s]['impedance'][i].real for s in self.get_root_sections()])
            for root in self.get_root_sections():
                resistance = self.sections[root]['impedance'][i].real
                current = total_loads / (resistance * resistance_sum)
                lower_bound += self.do_calc_loss(current, resistance)

        results= { 'minimum_loss': loss,
                   'loss_without_root_sections': comp_loss,
                   'lower_bound_of_minimum_loss': lower_bound + comp_loss}

        if 'original_number' in self.switches.values()[0]:
            results['open_switches'] = [self.switches[s]['original_number'] for s in open_switches]
        else:
            results['open_switches'] = open_switches

        return results

    MAX_CURRENT     = 300
    SENDING_VOLTAGE = 6600 / sqrt(3)
    VOLTAGE_RANGE   = (6300 / sqrt(3), 6900 / sqrt(3))

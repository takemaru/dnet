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

"""Module for a distribution network.
"""

from dnet.configset import ConfigSet
from dnet.unionfind import UnionFind
from dnet.util import flatten, is_tree
from graphillion import GraphSet
from math import sqrt
import networkx as nx
import yaml


class Graph(object):
    """Is a dual representation graph of the distribution network.
    """

    def __init__(self):
        self.edges = []
        self.roots = set()
        self._switch2edge = {}
        self._edge2switch = {}
        self._section2vertex = {}
        self._vertex2sections = {}


class Node(object):
    """Represents a ZDD node.
    """

    def __init__(self, str):
        n, v, l, h = str.split()
        self.n = n
        self.v = int(v)
        self.l = l
        self.h = h


class SearchSpace(object):
    """Represents a search space for the optimization.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.start = None
        self.end = None


class Network(object):
    """Represents a distribution network.
    """

    def __init__(self, file_or_dir, format=None):
        if format == 'fukui-tepco':
            from dnet.converter import FukuiTepcoConverter
            obj = yaml.load(FukuiTepcoConverter(file_or_dir).convert())
        else:
            obj = yaml.load(open(file_or_dir))
        self.nodes = obj['nodes']
        self.sections = obj['sections']
        self.switches = obj['switches']
        self._switch_set = set(self.switches)  # for fast membership query
        for s in self.sections.values():
            l = s['load']
            z = s['impedance']
            s['load'] = []
            s['impedance'] = []
            for i in range(Network.NUM_PHASES):
                s['load'].append(l[2*i] + l[2*i + 1]*1j)
                s['impedance'].append(z[2*i] + z[2*i + 1]*1j)
        if [l for s in self.sections.values() for l in s['load'] if l.real < 0]:
            msg = 'Warning: it is assumed that section loads are non-negative'
            sys.stderr.write(msg + '\n')
        self._neighbor_cache = {}
        self.graph = self._build_graph()
        self.search_space = SearchSpace()

    def enumerate(self, topology_constraints_only=None):
        gs = self._enumerate_forests()
        if not topology_constraints_only:
            for root in self._get_root_sections():
                gs &= self._enumerate_trees(root)
        return ConfigSet(self, gs)

    def loss(self, config, is_optimal=False):
        loss = 0
        for s in self._get_root_sections():
            loss += self._calc_loss(s, set(config), set())

        if not is_optimal:
            return loss
        else:
            lower_bound = 0  # theoretical lower bound in root sections
            for i in range(Network.NUM_PHASES):
                total_loads = 0.0
                for s in self.sections:
                    total_loads += self.sections[s]['load'][i]
                resistance_sum = 0.0
                for s in self._get_root_sections():
                    resistance_sum += 1 / self.sections[s]['impedance'][i].real
                for root in self._get_root_sections():
                    resistance = self.sections[root]['impedance'][i].real
                    current = total_loads / (resistance * resistance_sum)
                    lower_bound += self._do_calc_loss(current, resistance)

            comp_loss = 0  # loss without root sections
            for s in self._get_root_sections():
                comp_loss += self._calc_loss(s, set(config), set(), no_root=True)

            return loss, lower_bound + comp_loss

    def optimize(self, gs):
        comps = self._find_components()

        self._zdd = { 'B': Node('B %d B B ' % (len(self.switches) + 1)),
                      'T': Node('T %d T T ' % (len(self.switches) + 1)) }
        for line in gs.dumps().split('\n'):
            if line.startswith('.'):
                break
            n = Node(line)
            self._zdd[n.n] = n
            self.search_space.start = n.n

        entries = set([self.search_space.start])
        for comp in comps:
            entries = self._rebuild(entries, comp)

        self.search_space.end = 'T'

        path = nx.dijkstra_path(self.search_space.graph, self.search_space.start,
                                self.search_space.end)

        closed_switches = []
        for i in range(len(path) - 1):
            x, y = path[i], path[i + 1]
            closed_switches.extend(list(self.search_space.graph[x][y]['config']))

        return sorted(list(set(closed_switches)))

    def _has_same_topology(self, other):
        return self.nodes == other.nodes and self.switches == other.switches

    def _to_edge(self, switch):
        return self.graph._switch2edge[switch]

    def _to_switch(self, edge):
        return self.graph._edge2switch[edge]

    def _to_config(self, forest):
        return [self._to_switch(e) for e in forest]

    def _to_forest(self, config):
        return [self._to_edge(s) for s in config]

    def _get_root_sections(self):
        root_sections = set()
        for s in self.sections:
            if self.sections[s]['substation']:
                root_sections.add(s)
        return root_sections

    def _find_neighbors(self, s):
        if s not in self._neighbor_cache:
            neighbors = flatten([n for n in self.nodes if s in n])
            self._neighbor_cache[s] = set(neighbors) - set([s])
        return self._neighbor_cache[s]

    def _build_tree(self, root, closed_switches, processed_elems):
        branches = []
        neighbors = self._find_neighbors(root) - processed_elems
        if len(neighbors) == 1:
            s = neighbors.pop()
            assert s in self._switch_set
            if s in closed_switches:
                t = (self._find_neighbors(s) - set([root])).pop()
                branches.append((root, t))
                ps = processed_elems | set([root, s, t])
                bs = self._build_tree(t, closed_switches - set([s]), ps)
                branches.extend(bs)
        elif len(neighbors) > 1: # junction
            for s in neighbors:
                assert s in self.sections, (root, neighbors, s)
                branches.append((root, s))
            for s in neighbors:
                ps = processed_elems | set([root]) | neighbors
                bs = self._build_tree(s, closed_switches.copy(), ps)
                branches.extend(bs)
        return branches

    def _calc_current(self, root, branches):
        n_phases = Network.NUM_PHASES
        current = { root: [0, 0, 0] }
        for branch in branches:
            s, t = branch
            load = self.sections[t]['load']
            if t not in current:
                current[t] = [0, 0, 0]
            current[t] = [current[t][i] + load[i] for i in range(n_phases)]
            while True:
                if s not in current:
                    current[s] = [0, 0, 0]
                current[s] = [current[s][i] + load[i] for i in range(n_phases)]
                upper_branch = [b for b in branches if b[1] == s]
                assert len(upper_branch) <= 1
                if len(upper_branch) == 1:
                    s, t = upper_branch[0]
                else:
                    break
        load = self.sections[root]['load']
        current[root] = [current[root][i] + load[i] for i in range(n_phases)]
        return current

    def _calc_loss(self, root, closed_switches, barrier, no_root=False):
        branches = self._build_tree(root, closed_switches, barrier)
        assert is_tree(branches), 'loop found'
        sections = set([root] + flatten(branches))
        current = self._calc_current(root, branches)
        loss = 0.0
        for s in sections:
            if no_root and self.sections[s]['substation']:
                continue
            for i in range(Network.NUM_PHASES):
                j = current[s][i]
                r = self.sections[s]['impedance'][i].real
                loss += self._do_calc_loss(j, r)
        return loss

    def _do_calc_loss(self, current, resistance):
        assert not isinstance(resistance, complex)
        return abs(current)**2 * resistance

    def _build_graph(self):
        graph = Graph()
        sorted_sections = []
        for s in self.switches:
            ns = set()
            for t in self._find_neighbors(s):
                if t in self.sections:
                    ns.add(t)
            neighbors = set()
            is_root = False
            for t in sorted(ns):
                junctions = set([t])
                for u in self._find_neighbors(t):
                    if u in self.sections:
                        junctions.add(u)
                    if u in self.sections and u < t:
                        t = u
                neighbors.add(t)
                if t not in sorted_sections:
                    sorted_sections.append(t)
                    v = sorted_sections.index(t) + 1
                    graph._section2vertex[t] = v
                    graph._vertex2sections[v] = list(junctions)
            e = tuple([sorted_sections.index(t) + 1 for t in sorted(neighbors)])
            assert len(e) == 2
            graph.edges.append(e)
            graph._switch2edge[s] = e
            graph._edge2switch[e] = s
        assert len(graph.edges) == len(self.switches)

        for s in self.sections:
            if self.sections[s]['substation']:
                for t in self._find_neighbors(s):
                    if t < s:
                        s = t
                graph.roots.add(sorted_sections.index(s) + 1)
        assert len(graph.roots) == len(self._get_root_sections())

        GraphSet.set_universe(graph.edges, traversal='as-is')

        return graph

    def _enumerate_forests(self):
        return GraphSet.forests(roots=self.graph.roots, is_spanning=True)

    def _find_neighbor_switches(self, s, processed_sections):
        switches = set()
        if s in self._switch_set:
            for t in self._find_neighbors(s) - processed_sections:
                assert t in self.sections
                processed_sections.add(t)
                for u in self._find_neighbor_switches(t, processed_sections.copy()):
                    switches.add(u)
        else:
            processed_sections.add(s)
            for t in self._find_neighbors(s) - processed_sections:
                if t in self._switch_set:
                    switches.add(t)
                else:
                    for u in self._find_neighbor_switches(t, processed_sections.copy()):
                        switches.add(u)
        return switches - set([s])

    def _find_surrounding_switches(self, root, closed_switches):
        if len(closed_switches) > 0:
            switches = set()
            for s in closed_switches:
                for t in self._find_neighbor_switches(s, set()):
                    switches.add(t)
            return switches - closed_switches
        else:
            return self._find_neighbor_switches(root, set())

    def _find_border_switches(self, root):
        assert self.sections[root]['substation']
        border = set()
        for r in self._get_root_sections() - set([root]):
            for s in self._find_neighbor_switches(r, set()):
                border.add(s)
        return border

    def _satisfies_electric_constraints(self, root, closed_switches):
        branches = self._build_tree(root, closed_switches, set())
        if not is_tree(branches):
            return False

        current = self._calc_current(root, branches)
        for i in range(Network.NUM_PHASES):
            if abs(current[root][i]) > Network.MAX_CURRENT:
                return False
        assert len(current) == len(set(flatten(branches)))

        leaves = set(flatten(branches)) - set([b[0] for b in branches])
        for s in leaves:
            voltage_drop = []
            for i in range(Network.NUM_PHASES):
                j = current[s][i]
                z = self.sections[s]['impedance'][i]
                voltage_drop.append(j * z / 2)
            bs = [b for b in branches if b[1] == s]
            assert len(bs) == 1
            s, t = bs[0]
            while True:
                for i in range(Network.NUM_PHASES):
                    j = current[s][i]
                    z = self.sections[s]['impedance'][i]
                    voltage_drop[i] += j * z
                upper_branch = [b for b in branches if b[1] == s]
                assert len(upper_branch) <= 1
                if len(upper_branch) == 1:
                    s, t = upper_branch[0]
                else:
                    break
            v = voltage_drop
            v0 = Network.SENDING_VOLTAGE
            vl, vh = Network.VOLTAGE_RANGE
            for i in range(Network.NUM_PHASES):
                if abs(v0 - v[i]) < vl or vh < abs(v0 - v[i]):
                    return False

        return True

    def _find_trees(self, closed_switches, open_switches):
        closed_switches = [self._to_edge(s) for s in closed_switches]
        open_switches = [self._to_edge(s) for s in open_switches]
        return GraphSet({'include': closed_switches, 'exclude': open_switches})

    def _do_enumerate_trees(self, root, closed_switches, fixed_switches):
        gs = GraphSet()
        sur_switches = self._find_surrounding_switches(root, closed_switches)
        unfixed_switches = sur_switches - fixed_switches
        if len(unfixed_switches) == 0:
            return gs
        s = sorted(unfixed_switches)[0]
        fixed_switches.add(s)
        gs |= self._do_enumerate_trees(root, closed_switches.copy(), fixed_switches.copy())
        closed_switches.add(s)
        if self._satisfies_electric_constraints(root, closed_switches):
            sur_switches = self._find_surrounding_switches(root, closed_switches)
            gs |= self._find_trees(closed_switches, sur_switches)
            gs |= self._do_enumerate_trees(root, closed_switches.copy(), fixed_switches.copy())
        return gs

    def _enumerate_trees(self, root):
        gs = GraphSet()
        if self._satisfies_electric_constraints(root, set()):
            sur_switches = self._find_surrounding_switches(root, set())
            gs = self._find_trees(set(), sur_switches)
        border_switches = self._find_border_switches(root)
        return gs | self._do_enumerate_trees(root, set(), border_switches)

    def _find_components(self):
        switches = set(self.switches)
        sections = set(self.sections.keys())
        roots = self._get_root_sections()
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
        for s in self.switches:
            c = uf.find(s)
            if c not in comps:
                comps[c] = (i, set())
                i += 1
            comps[c][1].add(s)
            for t in self._find_neighbors(s):
                comps[c][1].add(t)
        assert sum([len(c[1]) for c in comps.values()]) == len(switches | sections - roots)

        comps = [comps[c][1] for c in sorted(comps, key=lambda c: comps[c][0])]

        s = None
        for c in comps:
            switches = [t for t in c if t in self._switch_set]
            assert s is None or self.switches.index(s) < min([self.switches.index(t) for t in switches]), \
                'switches must be ordered by independent components'
            s = switches[0]
            for t in switches:
                if self.switches.index(t) > self.switches.index(s):
                    s = t

        assert len([t for s in self.sections if s < 0
                    for t in self._find_neighbors(s) if t in self._switch_set]) == 0, \
                    'root sections must be connected to a junction, not a switch'

        return comps

    def _find_configs(self, n, comp, closed_switches):
        n = self._zdd[n]
        configs = []
        if n.v > len(self.switches) or self.switches[n.v - 1] not in comp:
            configs.append((closed_switches, n.n))
        else:
            if n.l <> 'B':
                configs2 = self._find_configs(n.l, comp, closed_switches.copy())
                configs.extend(configs2)
            assert n.h <> 'B'
            closed_switches.add(self.switches[n.v - 1])
            configs.extend(self._find_configs(n.h, comp, closed_switches.copy()))
        return configs

    def _calc_component_loss(self, comp_roots, closed_switches):
        loss = 0
        for root, barrier in comp_roots:
            loss += self._calc_loss(root, closed_switches, barrier)
        return loss

    def _rebuild(self, entries, comp):
        comp_roots = []
        for s in comp:
            if s in self.sections:
                for t in self._find_neighbors(s):
                    if t in self.sections and self.sections[t]['substation']:
                        assert not self.sections[s]['substation']
                        barrier = set()
                        for u in self._find_neighbors(s):
                            if u in self.sections:
                                barrier.add(u)
                        comp_roots.append((s, barrier))
                        break

        next_entries = set()
        loss_cache = {}
        for n in entries:
            for closed_switches, m in self._find_configs(n, comp, set()):
                next_entries.add(m)
                key = ','.join([str(s) for s in sorted(closed_switches)])
                if key in loss_cache:
                    loss = loss_cache[key]
                else:
                    loss = self._calc_component_loss(comp_roots, closed_switches)
                    loss_cache[key] = loss
                if not(n in self.search_space.graph \
                           and m in self.search_space.graph[n] \
                           and loss > self.search_space.graph[n][m]['weight']):
                    self.search_space.graph.add_edge(n, m, weight=loss,
                                                     config=closed_switches)

        return next_entries

    MAX_CURRENT     = 300
    SENDING_VOLTAGE = 6600 / sqrt(3)
    VOLTAGE_RANGE   = (6300 / sqrt(3), 6900 / sqrt(3))
    NUM_PHASES = 3

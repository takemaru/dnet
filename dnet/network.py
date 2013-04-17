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
from dnet.util import flatten, is_tree
from graphillion import GraphSet
from math import sqrt
import networkx as nx
import yaml


class Node(object):
    """Represents a ZDD node.
    """

    def __init__(self, str):
        n, v, l, h = str.split()
        self.n = n
        self.v = int(v)
        self.l = l
        self.h = h


class Network(object):
    """Represents a distribution network.
    """

    def __init__(self, file_or_dir, format=None):
        if format == 'fukui-tepco':
            from dnet.converter import FukuiTepcoConverter
            obj = yaml.load(FukuiTepcoConverter(file_or_dir).convert())
        else:
            obj = yaml.load(open(file_or_dir))
        self._nodes = obj['nodes']
        self._switches = obj['switches']
        self._sections = obj['sections']
        for s in self._sections.values():
            l = s['load']
            i = s['impedance']
            s['load']      = [l[0] + l[1]*1j, l[2] + l[3]*1j, l[4] + l[5]*1j]
            s['impedance'] = [i[0] + i[1]*1j, i[2] + i[3]*1j, i[4] + i[5]*1j]
        if [l for s in self._sections.values() for l in s['load'] if l.real < 0]:
            msg = 'Warning: it is assumed that section loads are non-negative'
            sys.stderr.write(msg + '\n')
        self._neighbor_cache = {}
        self._switch2edge = {}
        self._edge2switch = {}
        self._roots = self._build_graph()
        self._search_space = None

    def switch2edge(self, switch):
        if switch in self._switch2edge:
            return self._switch2edge[switch]
        else:
            for s, v in self._switches.iteritems():
                if 'original_number' in v and v['original_number'] == int(switch):
                    return self._switch2edge[s]
        raise KeyError, switch

    def edge2switch(self, edge):
        switch = self._edge2switch[edge]
        if 'original_number' in self._switches[switch]:
            switch = self._switches[switch]['original_number']
        return switch

    def forest2config(self, forest):
        return [self.edge2switch(e) for e in forest]

    def config2forest(self, config):
        return [self.switch2edge(s) for s in config]

    def enumerate(self):
        gs = self._enumerate_forests()
        for root in self._get_root_sections():
            gs &= self._enumerate_trees(root)
        return Configs(self, gs)

    def loss(self, config):
        loss = 0
        for s in self._get_root_sections():
            loss += self._calc_loss(s, set(config), set())
        return loss

    def optimize(self, gs):
        comps = self._find_components()

        self._zdd = { 'B': Node('B %d B B ' % (len(self._switches) + 1)),
                      'T': Node('T %d T T ' % (len(self._switches) + 1)) }
        root = None
        for line in gs.dumps().split('\n'):
            if line.startswith('.'):
                break
            n = Node(line)
            self._zdd[n.n] = n
            root = n.n

        self._search_space = nx.DiGraph()

        entries = set([root])
        for comp in comps:
            entries = self._rebuild(entries, comp)

        path = nx.dijkstra_path(self._search_space, root, 'T')

        comp_loss = 0
        closed_switches = []
        for i in range(len(path) - 1):
            x, y = path[i], path[i + 1]
            comp_loss += self._search_space[x][y]['weight']
            closed_switches.extend(list(self._search_space[x][y]['config']))
        closed_switches = set(closed_switches)
        open_switches = sorted(set(self._switches.keys()) - closed_switches)

        loss = 0
        for root in self._get_root_sections():
            loss += self._calc_loss(root, closed_switches, set())

        lower_bound = 0
        for i in range(3):
            total_loads = 0.0
            for s in self._sections:
                total_loads += self._sections[s]['load'][i]
            resistance_sum = 0.0
            for s in self._get_root_sections():
                resistance_sum += 1 / self._sections[s]['impedance'][i].real
            for root in self._get_root_sections():
                resistance = self._sections[root]['impedance'][i].real
                current = total_loads / (resistance * resistance_sum)
                lower_bound += self._do_calc_loss(current, resistance)

        results= { 'minimum_loss': loss,
                   'loss_without_root_sections': comp_loss,
                   'lower_bound_of_minimum_loss': lower_bound + comp_loss}

        if 'original_number' in self._switches.values()[0]:
            results['open_switches'] = []
            for s in open_switches:
                t = self._switches[s]['original_number']
                results['open_switches'].append(t)
        else:
            results['open_switches'] = open_switches

        return results

    def _get_root_sections(self):
        root_sections = set()
        for s in self._sections:
            if self._sections[s]['substation']:
                root_sections.add(s)
        return root_sections

    def _find_neighbors(self, s):
        if s not in self._neighbor_cache:
            neighbors = flatten([n for n in self._nodes if s in n])
            self._neighbor_cache[s] = set(neighbors) - set([s])
        return self._neighbor_cache[s]

    def _build_tree(self, root, closed_switches, processed_elems):
        branches = []
        neighbors = self._find_neighbors(root) - processed_elems
        if len(neighbors) == 1:
            s = neighbors.pop()
            assert s in self._switches
            if s in closed_switches:
                t = (self._find_neighbors(s) - set([root])).pop()
                branches.append((root, t))
                ps = processed_elems | set([root, s, t])
                bs = self._build_tree(t, closed_switches - set([s]), ps)
                branches.extend(bs)
        elif len(neighbors) > 1: # junction
            for s in neighbors:
                assert s in self._sections, (root, neighbors, s)
                branches.append((root, s))
            for s in neighbors:
                ps = processed_elems | set([root]) | neighbors
                bs = self._build_tree(s, closed_switches.copy(), ps)
                branches.extend(bs)
        return branches

    def _calc_current(self, root, branches):
        current = { root: [0, 0, 0] }
        for branch in branches:
            s, t = branch
            load = self._sections[t]['load']
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
        load = self._sections[root]['load']
        current[root] = [current[root][i] + load[i] for i in range(3)]
        return current

    def _calc_loss(self, root, closed_switches, barrier):
        branches = self._build_tree(root, closed_switches, barrier)
        assert is_tree(branches), 'loop found'
        sections = set([root] + flatten(branches))
        current = self._calc_current(root, branches)
        loss = 0.0
        for i in range(3):
            for s in sections:
                j = current[s][i]
                r = self._sections[s]['impedance'][i].real
                loss += self._do_calc_loss(j, r)
        return loss

    def _do_calc_loss(self, current, resistance):
        assert not isinstance(resistance, complex)
        return current.real**2 * resistance

    def _build_graph(self):
        edges = []
        sorted_sections = []
        for s in sorted(self._switches):
            ns = set()
            for t in self._find_neighbors(s):
                if t in self._sections:
                    ns.add(t)
            neighbors = set()
            is_root = False
            for t in sorted(ns):
                for u in self._find_neighbors(t):
                    if u in self._sections and u < t:
                        t = u
                neighbors.add(t)
                if t not in sorted_sections:
                    sorted_sections.append(t)
            edge = [sorted_sections.index(t) + 1 for t in sorted(neighbors)]
            edge = tuple(edge)
            assert len(edge) == 2
            edges.append(edge)
            self._switch2edge[s] = edge
            self._edge2switch[edge] = s
        assert len(edges) == len(self._switches)

        roots = set()
        for s in self._sections:
            if self._sections[s]['substation']:
                for t in self._find_neighbors(s):
                    if t < s:
                        s = t
                roots.add(sorted_sections.index(s) + 1)
        assert len(roots) == len(self._get_root_sections())

        GraphSet.set_universe(edges, traversal='as-is')

        return roots

    def _enumerate_forests(self):
        return GraphSet.forests(roots=self._roots, is_spanning=True)

    def _find_neighbor_switches(self, s, processed_sections):
        switches = set()
        if s in self._switches:
            for t in self._find_neighbors(s) - processed_sections:
                assert t in self._sections
                processed_sections.add(t)
                for u in self._find_neighbor_switches(t, processed_sections.copy()):
                    switches.add(u)
        else:
            processed_sections.add(s)
            for t in self._find_neighbors(s) - processed_sections:
                if t in self._switches:
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
        assert self._sections[root]['substation']
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
        if abs(current[root][0]) > Network.MAX_CURRENT or \
                abs(current[root][1]) > Network.MAX_CURRENT or \
                abs(current[root][2]) > Network.MAX_CURRENT:
            return False
        assert len(current) == len(set(flatten(branches)))

        leaves = set(flatten(branches)) - set([b[0] for b in branches])
        for s in leaves:
            voltage_drop = []
            for i in range(3):
                j = current[s][i]
                z = self._sections[s]['impedance'][i]
                voltage_drop.append(j * z / 2)
            bs = [b for b in branches if b[1] == s]
            assert len(bs) == 1
            s, t = bs[0]
            while True:
                for i in range(3):
                    j = current[s][i]
                    z = self._sections[s]['impedance'][i]
                    voltage_drop[i] += j * z
                upper_branch = [b for b in branches if b[1] == s]
                assert len(upper_branch) <= 1
                if len(upper_branch) == 1:
                    s, t = upper_branch[0]
                else:
                    break
            v1, v2, v3 = voltage_drop
            v0 = Network.SENDING_VOLTAGE
            vl, vh = Network.VOLTAGE_RANGE
            if abs(v0 - v1) < vl or abs(v0 - v2) < vl or abs(v0 - v3) < vl or \
                    vh < abs(v0 - v1) or vh < abs(v0 - v2) or vh < abs(v0 - v3):
                return False

        return True

    def _find_trees(self, closed_switches, open_switches):
        closed_switches = [self._switch2edge[s] for s in closed_switches]
        open_switches = [self._switch2edge[s] for s in open_switches]
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
        switches = set(self._switches.keys())
        sections = set(self._sections.keys())
        roots = self._get_root_sections()
        uf = UnionFind()
        uf.insert_objects(switches | sections - roots)
        for s in sorted(switches | sections - roots):
            neighbors = set()
            for n in [m for m in self._nodes if s in m]:
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
            for t in self._find_neighbors(s):
                comps[c][1].add(t)
        assert sum([len(c[1]) for c in comps.values()]) == len(switches | sections - roots)

        comps = [comps[c][1] for c in sorted(comps, key=lambda c: comps[c][0])]

        s = 'switch'
        for c in comps:
            switches = [t for t in c if t in self._switches]
            assert s < min(switches), 'switches must be ordered by independent components'
            s = max(switches)

        assert len([t for s in self._sections if s < 0
                    for t in self._find_neighbors(s) if t in self._switches]) == 0, \
                    'root sections must be connected to a junction, not a switch'

        return comps

    def _find_configs(self, n, comp, closed_switches):
        n = self._zdd[n]
        configs = []
        if 'switch_%04d' % n.v not in comp:
            configs.append((closed_switches, n.n))
        else:
            if n.l <> 'B':
                configs2 = self._find_configs(n.l, comp, closed_switches.copy())
                configs.extend(configs2)
            assert n.h <> 'B'
            closed_switches.add('switch_%04d' % n.v)
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
            if s in self._sections:
                for t in self._find_neighbors(s):
                    if t in self._sections and self._sections[t]['substation']:
                        assert not self._sections[s]['substation']
                        barrier = set()
                        for u in self._find_neighbors(s):
                            if u in self._sections:
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
                if not(n in self._search_space and m in self._search_space[n] \
                           and loss > self._search_space[n][m]['weight']):
                    self._search_space.add_edge(n, m, weight=loss,
                                                config=closed_switches)

        return next_entries

    MAX_CURRENT     = 300
    SENDING_VOLTAGE = 6600 / sqrt(3)
    VOLTAGE_RANGE   = (6300 / sqrt(3), 6900 / sqrt(3))

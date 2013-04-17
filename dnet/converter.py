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

"""Data converter for DNET.
"""

from dnet.unionfind import UnionFind
import yaml


class FukuiTepcoConverter(object):

    def __init__(self, dir):
        self._files = {'switch'   : dir + '/sw_list.dat',
                       'topology' : dir + '/SWed.dat',
                       'load'     : dir + '/LNewSL.dat',
                       'impedance': dir + '/LNewZ.dat',
                       'root'     : dir + '/root.dat'}

    def convert(self):
        switch_numbers = set()
        for line in open(self._files['switch']):
            for s in line.split():
                switch_numbers.add(int(s))

        switches = set()
        sections = set()
        nodes = {}
        for line in open(self._files['topology']):
            s, m, n, _ = line.split()
            s, m, n = int(s), int(m), int(n)
            if m not in nodes: nodes[m] = set()
            if n not in nodes: nodes[n] = set()
            nodes[m].add(s)
            nodes[n].add(s)
            if s in switch_numbers:
                switches.add(s)
            else:
                sections.add(s)

        loads = {}
        for line in open(self._files['load']):
            _, s, m, n, ur, ui, vr, vi, wr, wi = line.split()
            loads[int(s)] = [float(ur), float(ui), float(vr), float(vi), \
                                 float(wr), float(wi)]

        impedances = {}
        for line in open(self._files['impedance']):
            s, p, m, n, ur, ui, vr, vi, wr, wi = line.split()
            s = int(s)
            if p == '0':
                impedances[s] = [float(ur), float(ui)]
            elif p == '1':
                impedances[s].extend([float(vr), float(vi)])
            else:
                impedances[s].extend([float(wr), float(wi)])

        roots = set()
        for line in open(self._files['root']):
            _, n, lu, lv, lw, ir, ii = line.split()
            n = int(n)
            nodes[n].add(-n)
            sections.add(-n)
            roots.add(-n)
            loads[-n] = [float(lu), 0, float(lv), 0, float(lw), 0]
            impedances[-n] = [float(ir), float(ii)] * 3

        def find_neighbors(s):
            neighbors = []
            for ns in nodes.values():
                if s in ns:
                    neighbors.extend(ns)
            return set(neighbors) - set([s])

        assert len([t for s in sections if s < 0 for t in find_neighbors(s) if t in switches]) == 0, \
            'root sections must be connected to a junction, not a switch'

        uf = UnionFind()
        uf.insert_objects(switches | sections - roots)
        for s in sorted(switches | sections - roots):
            neighbors = set()
            for n in [m for m in nodes.values() if s in m]:
                if [t for t in n if t in roots] == []:
                    for t in n:
                        neighbors.add(t)
            for t in sorted(neighbors - set([s])):
                uf.union(s, t)

        visited = []
        queue = []
        s = sorted(sections - roots)[0]
        while True:
            if s in visited: continue
            visited.append(s)
            neighbors = set()
            for t in find_neighbors(s):
                neighbors.add(t)
            queue.extend(neighbors - set(visited) - set(queue) - roots)
            if queue == []: break
            s, queue = queue[0], queue[1:]
        assert len(visited) == len(switches | sections - roots)

        i = 1
        comps = {}
        for s in visited:
            c = uf.find(s)
            if c not in comps:
                comps[c] = (i, set())
                i += 1
            comps[c][1].add(s)
        assert sum([len(c[1]) for c in comps.values()]) == len(switches | sections - roots)

        sorted_switches = []
        for i in range(1, len(comps) + 1):
            comp = [c for c in comps.values() if c[0] == i][0]
            visited = []
            queue = []
            s = sorted(comp[1])[0]
            while s:
                if s in visited: continue
                if s in switches:
                    sorted_switches.append(s)
                visited.append(s)
                neighbors = set()
                for t in find_neighbors(s):
                    if t in comp[1]:
                        neighbors.add(t)
                queue.extend(neighbors - set(visited) - set(queue) - roots)
                if queue == []: break
                s, queue = queue[0], queue[1:]
        assert len(sorted_switches) == len(switches)

        obj = { 'nodes': [], 'switches': {}, 'sections': {} }

        for n in sorted(nodes):
            ss = []
            for s in nodes[n]:
                if s in switches:
                    ss.append('switch_%04d' % s)
                else:
                    ss.append('section_%04d' % s)
            obj['nodes'].append(sorted(ss))

        obj['switches'] = ['switch_%04d' % s for s in sorted_switches]
#        for s in sorted(switches):
#            c = uf.find(s)
#            i = comps[c][0]

        for s in sorted(sections):
#            c = uf.find(s)
#            i = comps[c][0] if c > 0 else 0
            obj['sections']['section_%04d' % s] = {
                'load'      : loads[s],
                'impedance' : impedances[s],
                'substation': s < 0,
            }

        return yaml.dump(obj)

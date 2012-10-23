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

class Data:
    def __init__(self, f):
        obj = yaml.load(f)
        self.nodes = obj["nodes"]
        self.switches = obj["switches"]
        self.sections = obj["sections"]
        for s in self.sections.values():
            l = s["load"]
            i = s["impedance"]
            s["load"]      = [l[0] + l[1] * 1j, l[2] + l[3] * 1j, l[4] + l[5] * 1j]
            s["impedance"] = [i[0] + i[1] * 1j, i[2] + i[3] * 1j, i[4] + i[5] * 1j]
        self.neighbor_cache = {}

    def find_neighbors(self, s):
        if s not in self.neighbor_cache:
            self.neighbor_cache[s] = set(flatten([n for n in self.nodes if s in n])) - set([s])
        return self.neighbor_cache[s]

    def build_tree(self, root, closed_switches, passed):
        branches = []
        neighbors = self.find_neighbors(root) - passed
        if len(neighbors) == 1:
            s = neighbors.pop()
            assert s in self.switches
            if s in closed_switches:
                t = (self.find_neighbors(s) - set([root])).pop()
                branches.append((root, t))
                bs = self.build_tree(t, closed_switches - set([s]), passed | set([root, s, t]))
                branches.extend(bs)
        elif len(neighbors) > 1: # junction
            for s in neighbors:
                assert s in self.sections, (root, neighbors, s)
                branches.append((root, s))
            for s in neighbors:
                bs = self.build_tree(s, closed_switches.copy(), passed | set([root]) | neighbors)
                branches.extend(bs)
        return branches

    def calc_current(self, root, branches):
        current = { root: [0, 0, 0] }
        for branch in branches:
            s, t = branch
            load = self.sections[t]["load"]
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
        load = self.sections[root]["load"]
        current[root][0] += load[0]
        current[root][1] += load[1]
        current[root][2] += load[2]
        return current

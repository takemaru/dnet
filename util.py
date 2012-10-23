import yaml

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

neighbor_cache = {}

def find_neighbors(s, nodes): # XXX cache depends on nodes as well as s
    if s not in neighbor_cache:
        neighbor_cache[s] = set(flatten([n for n in nodes if s in n])) - set([s])
    return neighbor_cache[s]

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

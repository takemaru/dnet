import yaml

class Data:
    def __init__(self, str):
        obj = yaml.load(str)
        self.nodes = obj["nodes"]
        self.switches = obj["switches"]
        self.sections = obj["sections"]

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

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

"""Module for a set of configurations.
"""

from graphillion import GraphSet


class ConfigSet(object):
    """Represents a set of configurations.

    This class supports similar interface with graphillion.GraphSet,
    which represents a set of graphs (a configuration can be regarded
    as a forest of graph).
    """

    def __init__(self, nw, gs):
        self._nw = nw
        self._gs = gs

    def copy(self):
        return ConfigSet(self._nw, self._gs.copy())

    def __nonzero__(self):
        return bool(self._gs)

    def union(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        others = [other._gs for other in others]
        return ConfigSet(self._nw, self._gs.union(*others))

    def intersection(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        others = [other._gs for other in others]
        return ConfigSet(self._nw, self._gs.intersection(*others))

    def difference(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        others = [other._gs for other in others]
        return ConfigSet(self._nw, self._gs.difference(*others))

    def symmetric_difference(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        others = [other._gs for other in others]
        return ConfigSet(self._nw, self._gs.symmetric_difference(*others))

    def update(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        self._gs.update(*[other._gs for other in others])
        return self

    def intersection_update(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        self._gs.intersection_update(*[other._gs for other in others])
        return self

    def difference_update(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        self._gs.difference_update(*[other._gs for other in others])
        return self

    def symmetric_difference_update(self, *others):
        for other in others:
            if not self._nw._has_same_topology(other._nw):
                raise TypeError, other
        self._gs.symmetric_difference_update(*[other._gs for other in others])
        return self

    def __invert__(self):
        return ConfigSet(self._nw, ~self._gs)

    __or__ = union
    __and__ = intersection
    __sub__ = difference
    __xor__ = symmetric_difference

    __ior__ = update
    __iand__ = intersection_update
    __isub__ = difference_update
    __ixor__ = symmetric_difference_update

    def isdisjoint(self, other):
        if not self._nw._has_same_topology(other._nw):
            raise TypeError, other
        return self._gs.isdisjoint(other._gs)

    def issubset(self, other):
        if not self._nw._has_same_topology(other._nw):
            raise TypeError, other
        return self._gs.issubset(other._gs)

    def issuperset(self, other):
        if not self._nw._has_same_topology(other._nw):
            raise TypeError, other
        return self._gs.issuperset(other._gs)

    __le__ = issubset
    __ge__ = issuperset

    def __lt__(self, other):
        if not self._nw._has_same_topology(other._nw):
            raise TypeError, other
        return self._gs < other._gs

    def __gt__(self, other):
        if not self._nw._has_same_topology(other._nw):
            raise TypeError, other
        return self._gs > other._gs

    def __eq__(self, other):
        return self._nw._has_same_topology(other._nw) and self._gs == other._gs

    def __ne__(self, other):
        return not self._nw._has_same_topology(other._nw) or \
            self._gs != other._gs

    def __len__(self):
        return len(self._gs)

    def len(self, size=None):
        if size is None:
            return self._gs.len()
        else:
            return ConfigSet(self._nw, self._gs.len(size))

    def __iter__(self):
        for g in iter(self._gs):
            yield self._nw._to_config(g)

    def rand_iter(self):
        for g in self._gs.rand_iter():
            yield self._nw._to_config(g)

    def min_iter(self, weights=None):
        if weights is not None:
            weights = self._conv_weights(weights)
        for g in self._gs.min_iter(weights):
            yield self._nw._to_config(g)

    def max_iter(self, weights=None):
        if weights is not None:
            weights = self._conv_weights(weights)
        for g in self._gs.max_iter(weights):
            yield self._nw._to_config(g)

    def _conv_weights(weights):
        weights2 = {}
        for s, w in weights.iteritems():
            weights2[self._nw._to_edge(s)] = w
        return weights2

    def __contains__(self, config_or_switch):
        if isinstance(config_or_switch, list):
            return self._nw._to_forest(config_or_switch) in self._gs
        else:
            return self._nw._to_edge(config_or_switch) in self._gs

    def add(self, config_or_switch):
        if isinstance(config_or_switch, list):
            self._gs.add(self._nw._to_forest(config_or_switch))
        else:
            self._gs.add(self._nw._to_edge(config_or_switch))

    def remove(self, config):
        if isinstance(config_or_switch, list):
            self._gs.remove(self._nw._to_forest(config_or_switch))
        else:
            self._gs.remove(self._nw._to_edge(config_or_switch))

    def discard(self, config):
        if isinstance(config_or_switch, list):
            self._gs.discard(self._nw._to_forest(config_or_switch))
        else:
            self._gs.discard(self._nw._to_edge(config_or_switch))

    def pop(self):
        return self._nw._to_config(self._gs.pop())

    def cler(self):
        self._gs.clear()

    def flip(self, switch):
        self._gs.flip(self._nw._to_edge(switch))

    def minimal(self):
        return ConfigSet(self._nw, self._gs.minimal())

    def maximal(self):
        return ConfigSet(self._nw, self._gs.maximal())

    def blocking(self):
        return ConfigSet(self._nw, self._gs.blocking())

    def smaller(self, size):
        return ConfigSet(self._nw, self._gs.smaller(size))

    def larger(self, size):
        return ConfigSet(self._nw, self._gs.larger(size))

    def complement(self):
        return ConfigSet(self._nw, self._gs.complement())

    def including(self, obj):
        if isinstance(obj, ConfigSet):
            obj = obj._gs
        elif isinstance(obj, list):
            obj = self._nw._to_forest(obj)
        else:
            obj = self._nw._to_edge(obj)
        return ConfigSet(self._nw, self._gs.including(obj))

    def excluding(self, obj):
        if isinstance(obj, ConfigSet):
            obj = obj._gs
        elif isinstance(obj, list):
            obj = self._nw._to_forest(obj)
        else:
            obj = self._nw._to_edge(obj)
        return ConfigSet(self._nw, self._gs.excluding(obj))

    def included(self, obj):
        if isinstance(obj, ConfigSet):
            obj = obj._gs
        elif isinstance(obj, list):
            obj = self._nw._to_forest(obj)
        else:
            raise TypeError, obj
        return ConfigSet(self._nw, self._gs.included(obj))

    def choice(self):
        return self._nw._to_config(self._gs.choice())

    def dump(self, fp):
        self._gs.dump(fp)

    def dumps(self):
        return self._gs.dumps()

    def load(self, fp):
        self._gs.load(fp)

    def loads(self, s):
        self._gs.loads(s)

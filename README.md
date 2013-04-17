DNET - Distribution Network Evaluation Tool
=====================================================================

* [Features](#features "Features")
* [Overview](#overview "Overview")
* [Installing](#installing "Installing")
* [Network data](#network-data "Network data")
* [Tutorial](#tutorial "Tutorial")
* [Additional notes](#additional-notes "Additional notes")
* [References](#references "References")

Features
--------------------------------------------------------------------------------

* Highly efficient analysis tool for power distribution networks
* Power loss minimization (nonconvex optimization over several
  hundreds of variables!) and more
* Featuring [Graphillion](http://graphillion.org/), an efficient
  graphset operation library
* Open source MIT license
* Additional benefits from Python: fast prototyping, easy to teach,
  and multi-platform

Overview
---------------------------------------------------------------------

DNET (Distribution Network Evaluation Tool) is an analysis tool that
works with power distribution networks for efficient and stable
operation such as loss minimization and service restoration.

Power distribution networks consist of several switches.  The
structure, or *configuration*, can be reconfigured by changing the
open/closed status of the switches depending on the operational
requirements.  However, networks of practical size have hundreds of
switches, which makes network analysis a quite tough problem due to
the huge size of search space.  Moreover, power distribution networks
are generally operated in a radial structure under the complicated
operational constraints such as line capacity and voltage profiles.
The loss minimization in a distribution network is a hard nonconvex
optimization problem.

DNET finds the best configuration you want with a great efficiency.
All feasible configurations are examined without stuck in local
minima.  DNET handles complicated electrical constraints with
realistic unbalanced three-phase loads.  We've optimized a large
distribution network with 468 switches using DNET; please see papers
listed in [References](#references) in detail.  We believe that DNET
takes you to the next stage of power distribution network analysis.

DNET can be used freely under the MIT license.  It is mainly developed
by [JST ERATO Minato
project](http://www-erato.ist.hokudai.ac.jp/?language=en).  We would
really appreciate if you would refer to our paper and address our
contribution on the use of DNET in your paper.

> Takeru Inoue, Keiji Takano, Takayuki Watanabe, Jun Kawahara, Ryo
  Yoshinaka, Akihiro Kishimoto, Koji Tsuda, Shin-ichi Minato, and
  Yasuhiro Hayashi, "Loss Minimization of Power Distribution Networks
  with Guaranteed Error Bound," Hokkaido University, Division of
  Computer Science, TCS Technical Reports, TCS-TR-A-12-59, August 2012.
  ([pdf](http://www-alg.ist.hokudai.ac.jp/~thomas/TCSTR/tcstr_12_59/tcstr_12_59.pdf))

DNET is still under the development.  The current version just
supports power loss minimization and configuration search, but we
believe service restoration is also possible if you can use DNET
appropriately with deep understanding of the theory.  We really
appreciate any pull request and patch if you add some changes that
benefit a wide variety of people.


Installing
---------------------------------------------------------------------

### Requirements

#### Python

To use Graphillion, you need Python version 2.6 or later.
http://www.python.org/

#### Graphillion, NetworkX, and PyYAML

Graphillion and NetworkX are Python modules for graphs, while PyYAML
is another Python module for a compact syntax called
[YAML](http://en.wikipedia.org/wiki/YAML).  They can be installed by:

```bash
$ sudo easy_install graphillion
$ sudo easy_install networkx
$ sudo easy_install pyyaml
```

### Quick install

Just type:

```bash
$ sudo easy_install pydnet  # caution: don't type just "dnet"
```

and an attempt will be made to find and install an appropriate version
that matches your operating system and Python version.

### Installing from source

You can install from source by downloading a source archive file
(tar.gz or zip) or by checking out the source files from the GitHub
source code repository.

#### Source archive file

1. Download the source (tar.gz or zip file) from
   https://github.com/takemaru/dnet
2. Unpack and change directory to the source directory (it should have
   the file setup.py)
3. Run `python setup.py build` to build
4. (optional) Run `python setup.py test -q` to execute the tests
5. Run `sudo python setup.py install` to install

#### GitHub repository

1. Clone the Dnet repository `git clone https://github.com/takemaru/dnet.git`
2. Change directory to "dnet"
3. Run `python setup.py build` to build
4. (optional) Run `python setup.py test -q` to execute the tests
5. Run `sudo python setup.py install` to install

If you don't have permission to install software on your system, you
can install into another directory using the `-user`, `-prefix`, or
`-home` flags to setup.py.  For example:

```bash
$ python setup.py install --prefix=/home/username/python
  or
$ python setup.py install --home=~
  or
$ python setup.py install --user
```

If you didn't install in the standard Python site-packages directory
you will need to set your `PYTHONPATH` variable to the alternate
location.  See http://docs.python.org/inst/search-path.html for further
details.


Network data
---------------------------------------------------------------------

DNET requires network data, which includes network topology (line
connectivity and switch positions), loads, and impedance.  The data
must be formatted by YAML syntax.  We explain the formatting rules
using an example, [data/test.yaml] in the DNET package.  This example
network consists of three feeders and 16 switches, as shown in the
figure.

![Example network](http://github.com/takemaru/dnet/blob/master/doc/example_nw.png?raw=true)

The data file is divided into three parts; nodes, sections, and
switches.  Since YAML rules are quite simple, we believe it is not so
difficult to understand it.

### Nodes

The "nodes" part describes nodes, at which a switch and/or section(s)
are connected.  In the above example network, nodes are indicated by
black or red circles.  The following YAML data shows some nodes in the
example network; three sections are connected at the first node (i.e.,
section_-001, section_0302, and section_0303), while a section and a
switch is connected at the fourth node (i.e., section_0302 and
switch_0010).

```yaml
nodes:
- [section_-001, section_0302, section_0303]
- [section_-002, section_0001, section_0002]
- [section_-003, section_0008, section_0309]
- [section_0302, switch_0010]
:
```

### Sections

The "sections" part describes section information including load and
impedance.  In DNET, loads are assumed to be unbalanced three-phase
and be connected in delta.  Loads are also assumed to be uniformly
distributed along a line section, and are modeled as constant *current*,
not as power (see Section 2 in [theory.pdf] for more detail).

In the data file, load and impedance are specified by six values,
which are real and imaginary parts of the three phases; for
section_-001 in the following YAML, load current is 16.3225894 + 0j in
the 0-th phase, and impedance is 0.0684 + 0.3678805j in the all
phases.  Substation attribute indicates whether the line section is
directly connected to a feeding point in a substation.

```yaml
sections:
  section_-001:
    impedance: [0.0864, 0.3678805, 0.0864, 0.3678805, 0.0864, 0.3678805]
    load: [16.3225894, 0, 16.3225894, 0, 1.29105e-11, 0]
    substation: true
:
```

### Switches

The "switches" part specifies the switch order in a list.
We have to be careful to assign the order.  Switches should be
ordered based on the proximity in the network as shown in the figure,
because DNET's efficiency highly depends on the order.  For the loss
minimization, the order must not step over junctions connected to a
substation (such junctions are indicated by red circles in the
figure); see Sections 4.1 and 5.1 in [theory.pdf] for more detail.

```yaml
switches:
- switch_0001
- switch_0002
- switch_0003
:
```

### Fukui-TEPCO format

Network data in the [Fukui-TEPCO
format](http://www.hayashilab.sci.waseda.ac.jp/RIANT/riant_test_feeder.html)
can be also accepted in DNET.  Since Fukui-TEPCO format lacks switch
indicators, you have to add file `sw_list.dat` that includes switch
names; see examples in
[data/test-fukui-tepco/](https://github.com/takemaru/dnet/tree/master/data/test-fukui-tepco)
in detail.


Tutorial
---------------------------------------------------------------------

We assume network data used in this tutorial is stored in a directory
`data/`.  Download a file
[data/test.yaml](https://github.com/takemaru/dnet/blob/master/data/test.yaml?raw=true)
or all files in
[data/test-fukui-tepco/](https://github.com/takemaru/dnet/tree/master/data/test-fukui-tepco),
and put it into the directory before beginning the tutorial.

Start the Python interpreter and import DNET.

```python
$ python
>>> from dnet import Network
```

You might need to change the maximum current and voltage range for
your own data.  The default values are given as follows.

```python
>>> from math import sqrt
>>> Network.MAX_CURRENT     = 300
>>> Network.SENDING_VOLTAGE = 6600 / sqrt(3)
>>> Network.VOLTAGE_RANGE   = (6300 / sqrt(3), 6900 / sqrt(3))
```

Load the network data as follows.

```python
>>> nw = Network('data/test.yaml')
```

If your data is in the Fukui-TEPCO format, specify data directory with
the format type.

```python
>>> nw = Network('data/test-fukui-tepco', format='fukui-tepco')
```

We can access to the loaded network data (if you've loaded the
Fukui-TEPCO format data, the switch numbers are different).

```python
>>> nw.nodes
[['section_-001', 'section_0302', 'section_0303'], ['section_-002', 'section_0001', ...
>>> nw.sections
{'section_1068': {'load': [(23.87780659+4.33926456j), (23.1904931+4.214360495j), ...
>>> nw.switches
['switch_0001', 'switch_0002', 'switch_0003', 'switch_0004', 'switch_0005', ...
```

Then, enumerate all feasible configurations as follows.

```python
>>> configs = nw.enumerate()
```

We count the number of all the feasible configurations.

```python
>>> configs.len()
111L
```

This shows that the network has 111 feasible configurations.

Object `configs` is an instance of ConfigSet.  ConfigSet supports
similar interface with graphillion.GraphSet, which represents a set of
graphs (a configuration can be regarded as a forest of graph).  We can
utilize the rich functions provided by Graphillion, such as search and
iteration, for configuration analysis.

We search for configurations by a query; e.g., switch 2 is closed
while switch 3 is open.  Statuses of the other switches are not cared.

```python
>>> filtered_configs = configs.including('switch_0002').excluding('switch_0003')
>>> filtered_configs.len()
15L
```

These configurations can be visited one by one using an iterator as
follows.

```python
>>> for config in filtered_configs:
...     config
...
['switch_0001', 'switch_0011', 'switch_0002', 'switch_0005', 'switch_0004', 'switch_0007', 'switch_0008', 'switch_0009', 'switch_0010', 'switch_0014', 'switch_0012', 'switch_0015']
['switch_0001', 'switch_0011', 'switch_0002', 'switch_0005', 'switch_0004', 'switch_0007', 'switch_0008', 'switch_0009', 'switch_0010', 'switch_0014', 'switch_0012', 'switch_0016']
['switch_0001', 'switch_0011', 'switch_0002', 'switch_0005', 'switch_0004', 'switch_0007', 'switch_0008', 'switch_0009', 'switch_0010', 'switch_0012', 'switch_0016', 'switch_0015']
:
```

Each line shows a configuration, which is represented by a set of
*closed* switches in DNET.

We select 5 configurations uniformly randomly, and calculate the
average loss over them.

```python
>>> i = 1
>>> sum = 0.0
>>> for config in filtered_configs.rand_iter():
...     sum += nw.loss(config)
...     if i == 5:
...         break
...     i += 1
...
>>> sum / 5
83014.06804812004
```

We finally search for the minimum loss configuration from all feasible
configurations enumerated above.

```python
>>> nw.optimize(configs)
{ 'minimum_loss': 69734.285418826621,
  'lower_bound_of_minimum_loss': 67028.86898923367,
  'loss_without_root_sections': 46128.464350540948,
  'open_switches': ['switch_0004', 'switch_0007', 'switch_0012', 'switch_0015'] }
```

The minimum loss is 69734 and the lower bound is 67029; the lower
bound means a theoretical bound under which the minimum loss never be
(see Section 3.3 in [theory.pdf] in detail).  In the optimal
configuration, switch 4, switch 7, switch 12, and switch 15 are open,
and the other switches are closed.


Additional notes
---------------------------------------------------------------------

- DNET assumes that just switches are controllable in a distribution
  network while other components like capacitors are ignored; we
  consider the distribution network analysis as a combinatorial
  problem, in which the variable is open/closed status of the
  switches.

- In DNET, section loads must be given as constant *current*.  Line current
  is calculated by sweeping backward to sum up downstream section
  loads.  This is because our loss minimization method depends on this
  backward sweeping; see Section 3.1 in [theory.pdf] in detail.
  However, if you are interested in only the configuration search,
  line current can be calculated in the ordinary way with section
  loads of constant *power*; fix `_calc_current()` and
  `_satisfies_electric_constraints()` in `dnet/network.py`.

- DNET assumes that all section loads are non-negative.  This can be
  an issue if introducing distributed generators; see Sections 4.1 and
  8 in [theory.pdf] for more detail.

- In the loss minimization, switches between a substation and a
  junction are assumed to be closed.  This is because such junctions
  (i.e., red circles in the figure) must be energized in any
  configurations in our loss minimization method; see Section 4.1 in
  [theory.pdf] for more detail.

- The search space used in the optimization process is a directed
  acyclic graph.  The shortest path indicates the optimal solution,
  and the path weight corresponds to the minimum loss.  We can
  retrieve all edges with their weights as follows (vertex `'T'` is
  the terminal one on the path).

```python
>>> for u, v in nw._search_space.edges():
...     u, v, nw._search_space[u][v]['weight']
...
('4082', 'T', 227.25507204036546)
('38', 'T', 227.25507204036546)
('46', '38', 190.18278149818809)
:
```

References
---------------------------------------------------------------------

- Takeru Inoue, Keiji Takano, Takayuki Watanabe, Jun Kawahara, Ryo
  Yoshinaka, Akihiro Kishimoto, Koji Tsuda, Shin-ichi Minato, and
  Yasuhiro Hayashi, "Loss Minimization of Power Distribution Networks
  with Guaranteed Error Bound," Hokkaido University, Division of
  Computer Science, TCS Technical Reports, TCS-TR-A-12-59, August 2012.
  ([pdf](http://www-alg.ist.hokudai.ac.jp/~thomas/TCSTR/tcstr_12_59/tcstr_12_59.pdf))
- Takeru Inoue, "Theory of Distribution Network Evaluation Tool."
  [theory.pdf]
- [PyDNET : Python Package Index](https://pypi.python.org/pypi/PyDNET)

[data/test.yaml]: http://github.com/takemaru/dnet/blob/master/data/test.yaml
[theory.pdf]: http://github.com/takemaru/dnet/blob/master/doc/theory.pdf?raw=true

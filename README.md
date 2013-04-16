DNET - Distribution Network Evaluation Tool
=====================================================================

* [Overview](#overview "Overview")
* [Installing](#installing "Installing")
* [Network data](#network-data "Network data")
* [Tutorial](#tutorial "Tutorial")
* [Limitations](#limitations "Limitations")
* [References](#references "References")

Overview
---------------------------------------------------------------------

DNET (Distribution Network Evaluation Tool) is an analysis tool that
evaluates power distribution networks for efficient and stable
operation such as loss minimization and service restoration.

Power distribution networks consist of several switches, and
reconfigure their structures, or *configurations*, by changing the
open/closed status of the switches depending on the operational
requirements.  However, networks of practical size have hundreds of
switches, which makes network analysis a quite tough problem due to
the huge size of search space.  Moreover, power distribution networks
are generally operated in a radial structure under the complicated
operational constraints such as line capacity and voltage profiles.

DNET finds the best configuration you want with a great efficiency,
while it examines all feasible configurations without stuck in local
minima.  It supports all the constraints with realistic unbalanced
three-phase loads.  We believe that DNET takes you to the next stage
of power distribution network analysis.

DNET can be used freely under the MIT license.  It is mainly developed
in [JST ERATO Minato
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
supports configuration search and loss minimization, but we believe
service restoration is also possible if you can use DNET appropriately
with deep understanding of the theory.  We really appreciate any pull
request and patch if you add some changes that benefit a wide variety
of people.


Installing
---------------------------------------------------------------------

### Requirements

#### Python

To use Graphillion, you need Python version 2.6 or later.
http://www.python.org/

#### Graphillion, NetworkX, and PyYAML

Graphillion and NetworkX are Python modules for graphs, while PyYAML
is another Python module for YAML.  They can be installed by:

```bash
$ sudo easy_install graphillion
$ sudo easy_install networkx
$ sudo easy_install pyyaml
```

### Quick install

Just type:

```bash
$ sudo easy_install dnet
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
must be formatted by [YAML](http://en.wikipedia.org/wiki/YAML) syntax.
We explain the formatting rules using an example,
[test/results/data.yaml] in the DNET package.  This example network
consists of three feeders and 16 switches, as shown in the figure.

![Example network](http://github.com/takemaru/dnet/blob/master/doc/example_nw.png?raw=true)

The data file is divided into three parts; nodes, sections, and
switches.  Since YAML rules are quite simple, we believe it is not so
difficult to understand it.

### Nodes

The "nodes" part describes nodes, at which a switch and/or section(s)
are connected.  In the above example network, nodes are indicated by
black or red circles.  The following YAML data shows some nodes in the
example network; three sections are connected at the first line (i.e.,
section_-001, section_0302, and section_0303), while a section and a
switch is connected at the fourth line (i.e., section_0302 and
switch_0010).

```yaml
nodes:
- [section_-001, section_0302, section_0303]
- [section_-002, section_0001, section_0002]
- [section_-003, section_0008, section_0309]
- [section_0302, switch_0010]
```

### Sections

The "sections" part describes section information including load and
impedance.  In DNET, loads are assumed to be unbalanced three-phase
and be connected in delta.  Loads are also assumed to be uniformly
distributed along a line section, and are modeled as constant current,
not as power (see Section 2 in [theory.pdf] for more detail).

In the data file, load and impedance are specified by six values,
which are real and imaginary parts of the three phases; for
section_-001 in the following YAML, load current is 16.3225894 + 0j in
the 0-th phase, and impedance is 0.0684 + 0.3678805j in the all
phases.  Substation attribute indicates whether the line section is
directly connected to a substation.  There is no restriction on
section names, unlike switches as described below.

```yaml
sections:
  section_-001:
    impedance: [0.0864, 0.3678805, 0.0864, 0.3678805, 0.0864, 0.3678805]
    load: [16.3225894, 0, 16.3225894, 0, 1.29105e-11, 0]
    substation: true
```

### Switches

The "switches" part describes switch information.  However, no
information is required in the current version, and so just an empty
curly brace is given for each switch, as shown in the following YAML.

```yaml
switches:
  switch_0001: {}
  switch_0002: {}
  switch_0003: {}
```

We have to be careful to assign switch names.  First, the switch
numbers must be successive positive integers, and they must be
represented by four-figure numbers with leading zeros (i.e., printf of
"switch_%04d").  Second, switches should be numbered based on the
proximity in the network as shown in the figure, because DNET's
efficiency highly depends on the order.  Third, in the loss
minimization, the order must not step over junctions connected to a
substation (such junctions are indicated by red circles in the
figure); see Sections 4.1 and 5.1 in [theory.pdf] for more detail.

Optionally, switches may have original_number attribute, which is the
original switch number in your data and will be shown in the DNET's
results.

```yaml
switches:
  switch_0001: {original_number: 1064}
  switch_0002: {original_number: 1060}
  switch_0003: {original_number: 1065}
```

### Converter

Network data in the [Fukui-TEPCO
format](http://www.hayashilab.sci.waseda.ac.jp/RIANT/riant_test_feeder.html)
can be converted to the DNET format by `script/dnet-converter`.
Since Fukui-TEPCO format lacks switch indicators, you have to add
file `sw_list.dat` that includes switch numbers; see examples in
`test/data/` in detail.  The data is converted as follows.

```bash
$ python script/dnet-converter test/data > data.yaml
```


Tutorial
---------------------------------------------------------------------

First of all, we enumerate all feasible configurations in the
compressive graph representation (don't worry, you do not have to
understand the complicated data structure).  For the constraints of
line capacity and voltage profiles, maximum current and voltage range
must be defined at the head of `script/dnet-enumerator`.

```python
max_current     = 300
sending_voltage = 6600 / math.sqrt(3)
voltage_range   = (6300 / math.sqrt(3), 6900 / math.sqrt(3))
```

Then, enumerate all configurations as follows.

```bash
$ mkdir -p /tmp/dnet
$ python script/dnet-enumerator test/results/data.yaml /tmp/dnet
```

In this tutorial, we choose `/tmp/dnet` as the output directory, in
which result files will be placed.  Configurations are stored in
`/tmp/dnet/diagram`.

### Configuration search

We count the number of all the feasible configurations.

```bash
$ fukashigi -n 16 -t cardinality /tmp/dnet/diagram
111
```

This shows that the network has 111 feasible configurations.

Next, we retrieve configurations by issuing a query; e.g., switch-1 to
switch-5 are closed, switch-9 *or* switch-10 is open, and the status
of other switches are not cared.

```bash
$ echo "1 2 3 4 5" > closed
$ echo "9 10" > open
$ fukashigi -n 16 -t enum /tmp/dnet/diagram "/" closed "%" open
7 8 10 12 13 14 15
7 8 10 12 13 14 16
7 8 10 12 13 15 16
```

The result shows three configurations that meet the query; note that
closed switches in the query (switch-1 to switch-5) are omitted in the
result.

We try random sampling from the configurations; select a single
feasible configuration uniformly randomly as follows.

```bash
$ fukashigi -n 16 -t enum -s 1 /tmp/dnet/diagram
1 2 4 5 7 8 9 10 12 13 14 16
```

The result shows a list of switch numbers that are closed in the
configuration (your result may be different depending on random number
generators).

Finally, we can calculate power loss of a given configuration.

```bash
$ python script/dnet-loss test/results/data.yaml -c 1 2 4 5 7 8 9 10 12 13 14 16
80199.3
```

### Power loss minimization

We search for the minimum loss configuration from all feasible
configurations enumerated above.

```bash
$ python script/dnet-optimizer test/results/data.yaml /tmp/dnet/diagram
minimum_loss: 69734.3
loss_without_root_sections: 46128.5
lower_bound_of_minimum_loss: 67585.2
open_switches: ['switch_0004', 'switch_0007', 'switch_0012', 'switch_0015']
```

The minimum loss is 72055.7 and the lower bound is 69238.4; the lower
bound means a theoretical bound under which the minimum loss never be
(see Section 3.3 in [theory.pdf] in detail).  In the optimal
configuration, switch-4, switch-7, switch-12, and switch-15 are open,
and the other switches are closed.


Limitations
---------------------------------------------------------------------

- DNET assumes that just switches are controllable in a distribution
  network while other components like capacitors are ignored; we
  consider the distribution network analysis as a combinatorial
  problem, in which the variable is open/closed status of the
  switches.

- In DNET, section loads are given as constant current.  Line current
  is calculated by sweeping backward to sum up downstream section
  loads.  This is because our loss minimization method depends on this
  backward sweeping; see Section 3.1 in [theory.pdf] in detail.
  However, if you are interested in only the configuration search,
  line current can be calculated in the ordinary way with section
  loads of constant *power*; fix dnet.core.Network.calc_current() and
  satisfies_electric_constraints() in `script/dnet-enumerator`.

- DNET assumes that all section loads are non-negative.  This can be
  an issue if introducing distributed generators; see Sections 4.1 and
  8 in [theory.pdf] for more detail.

- In the loss minimization, switches between a substation and a
  junction are assumed to be closed.  This is because such junctions
  (i.e., red circles in the figure) must be energized in any
  configurations in our loss minimization method; see Section 4.1 in
  [theory.pdf] for more detail.


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

[test/results/data.yaml]: http://github.com/takemaru/dnet/blob/master/test/results/data.yaml
[theory.pdf]: http://github.com/takemaru/dnet/blob/master/doc/theory.pdf?raw=true

DNET - Distribution Network Evaluation Tool
=====================================================================

What's DNET
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
three-phase loads.  We believe that DNET brings you to the next stage
of power distribution network analysis.

DNET can be used freely under the MIT license, which is found in
[MIT-LICENSE.txt] in the DNET package.  We would really appreciate if
you would address our contribution in your paper on the use of DNET
(e.g., in Acknowledgement section in the paper).

DNET is mainly developed in [JST ERATO Minato
project](http://www-erato.ist.hokudai.ac.jp/?language=en).  It is
implemented by the authors listed in [AUTHORS.txt], and its theory is
studied by several people as described in [theory.pdf].

DNET is still under the development.  The current version just
supports configuration search and loss minimization, but we believe
service restoration is also possible if you can use DNET appropriately
with deep understanding of the theory.  We really appreciate any pull
request and patch if you add some changes that benefit a wide variety
of people.

Requirements
---------------------------------------------------------------------

DNET is Python scripts, which depend on some C/C++ programs.  We
require Python and C/C++ compilers for installation and execution.  We
confirmed that DNET works the following environment.

- Python 2.7
- gcc/g++ 4.1.2
- GNU Make 3.81

Installation
---------------------------------------------------------------------

First, we retrieve a DNET package by git (if your system does not have
git, click the "ZIP" button in the top of DNET page and extract it).
We then change the directory.

```bash
$ git clone https://github.com/takemaru/dnet.git
$ cd dnet/
```

Next, we resolve dependencies.  DNET requires *fukashigi*
combinatorial problem solver, and fukashigi depends on two libraries
(frontier method and binary decision diagrams).  These packages are
not yet available online (will be soon we believe), and so we include
them in `pkg/` in the DNET.  Install them as follows.

```bash
$ cd pkg/

$ tar fxz sapporobdd-0.1.2.tar.gz
$ cd sapporobdd-0.1.2/
$ ./configure
$ make
$ sudo make install
$ cd ../

$ tar fxz frontier-0.1.1.tar.gz
$ cd frontier-0.1.1/
$ ./configure
$ make
$ sudo make install
$ cd ../

$ tar fxz fukashigi-0.1.3.tar.gz
$ cd fukashigi-0.1.3/
$ ./configure
$ make check
$ sudo make install
$ cd ../
```

If you use a 32-bit machine, you can pass --enable-32bit option to
configure scripts for all the packages.

DNET also depends Python modules,
[networkx](http://networkx.lanl.gov/) and [yaml](http://pyyaml.org/).
Install them by pip or as follows.

```bash
$ tar fxz networkx-1.7.tar.gz
$ cd networkx-1.7/
$ python setup.py build
$ sudo python setup.py install
$ cd ../

$ tar fxz PyYAML-3.10.tar.gz
$ cd PyYAML-3.10/
$ python setup.py build
$ sudo python setup.py install
$ cd ../
```

Finally, we can do self-tests for DNET by,

```bash
$ cd ../
$ make check
:
ok
```

If you found "ok" at the end of test results, the installation would
have been done successfully.

Network data
---------------------------------------------------------------------

DNET requires network data, which includes network topology (line
connectivity and switch positions), loads, and impedance.  The data
must be formatted by [YAML](http://en.wikipedia.org/wiki/YAML) syntax.
We explain the formatting rules using an example, [test/data.yaml] in
the DNET package.  This example network consists of three feeders and
16 switches, as shown in the figure.

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

Usage
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
$ python script/dnet-enumerator test/data.yaml /tmp/dnet
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
$ fukashigi -n 16 -t e /tmp/dnet/diagram "/" closed "%" open
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
$ fukashigi -n 16 -t 1 /tmp/dnet/diagram 
1 3 4 5 6 8 9 10 11 12 14 16 
```

The result shows a list of switch numbers that are closed in the
configuration (your result may be different depending on random number
generators).

Finally, we can calculate power loss of a given configuration.

```bash
$ python script/dnet-loss test/data.yaml -c 1 3 4 5 6 8 9 10 11 12 14 16
74285.5
```

### Power loss minimization

We search for the minimum loss configuration from all feasible
configurations enumerated above.

```bash
$ python script/dnet-optimizer test/data.yaml test/diagram
minimum_loss: 72055.7
loss_without_root_sections: 47781.7
lower_bound_of_minimum_loss: 69238.4
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

FAQ
---------------------------------------------------------------------

Q. How to rectify DNET for *energy* loss minimization?

A. We give a hint to consider multiple load profiles for emulating energy
loss minimization.

First, we select configurations that satisfy the constraints for all
the load profiles.  Enumerate configurations for each load profile,
and combine them as follows by using fukashigi.

```bash
$ fukashigi -n <number of switches> -t diagram result-1/diagram "&" and result-2/diagram "&" ...
```

Next, we search for the minimum energy-loss configuration.
Modify YAML data to contain multiple load profiles as follows.

```yaml
sections:
  section_-001:
    impedance: [0.0864, 0.3678805, 0.0864, 0.3678805, 0.0864, 0.3678805]
    load: [[16.3225894, 0, 16.3225894, 0, 1.29105e-11, 0],
           [41.21753365, 0, 16.02966235, 0, 31.33198201, 0],
           ...]
    substation: true
```

Fix dnet.core.Network.__init__() to handle multiple load profiles.
Fix dnet.core.Network.calc_current() to choose a load profile by
adding an argument, and modify dnet.core.Network.calc_loss() to call
calc_current() multiple times by changing the argument.

References
---------------------------------------------------------------------

- Takeru Inoue, "Theory of Distribution Network Evaluation Tool."
  [theory.pdf]
- Takeru Inoue, Keiji Takano, Takayuki Watanabe, Jun Kawahara, Ryo
  Yoshinaka, Akihiro Kishimoto, Koji Tsuda, Shin-ichi Minato, and
  Yasuhiro Hayashi, "Loss Minimization of Power Distribution Networks
  with Guaranteed Error Bound," Hokkaido University, Division of
  Computer Science, TCS Technical Reports, TCS-TR-A-12-59, August 2012.
  ([pdf](http://www-alg.ist.hokudai.ac.jp/~thomas/TCSTR/tcstr_12_59/tcstr_12_59.pdf))

[AUTHORS.txt]: http://github.com/takemaru/dnet/blob/master/AUTHORS.txt
[MIT-LICENSE.txt]: http://github.com/takemaru/dnet/blob/master/MIT-LICENSE.txt
[test/data.yaml]: http://github.com/takemaru/dnet/blob/master/test/data.yaml
[theory.pdf]: http://github.com/takemaru/dnet/blob/master/doc/theory.pdf?raw=true

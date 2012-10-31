DNET - Distribution Network Evaluation Tool
=====================================================================

What's DNET
---------------------------------------------------------------------

DNET (Distribution Network Evaluation Tool) is an efficient analysis
tool that evaluates power distribution networks for power loss
minimization, service restoration, and so forth.  DNET examines all
network configurations (i.e., all combinations of switch's on-off
status in a network) in an exhaustive way, and finds the best one you
want without loss of efficiency.  It is highly scalable and so it
handles a network with hundreds of switches, due to the use of
compressive graph representation named zero-suppressed binary decision
diagram.

DNET can be used freely under the MIT license, which is found in
`MIT-LICENSE.txt` in the DNET package.  We would really appreciate if
you would address our contribution in your paper on the use of DNET
(e.g., in Acknowledgement section in the paper).

DNET is mainly developed in [JST ERATO Minato
project](http://www-erato.ist.hokudai.ac.jp/?language=en).  It is
implemented by the authors listed in `AUTHORS.txt`, and its theory is
studied by several people as described in `doc/dnet-thoery.pdf`.

DNET is still under the development.  The current version just
supports feasible configuration search and power loss minimization,
but we believe service restoration is also possible if you can use
DNET appropriately with deep understanding of the DNET theory.  We
really appreciate any pull request and patch.

Installation
---------------------------------------------------------------------

First, we extract DNET and move into it.

```bash
$ tar fxz dnet-0.1.0.tar.gz
$ cd dnet-0.1.0/
```

Next, we resolve dependencies.  DNET requires *fukashigi*
combinatorial problem solver, and fukashigi requires frontier method
and a BDD implementation.  These packages are not yet available online
(will be soon we believe), and so we include them in `pkg/` directory
in the DNET.  Install them as follows:

```bash
$ cd pkg/

$ tar fxz sapporobdd-0.1.tar.gz
$ cd sapporobdd-0.1/
$ ./configure
$ make
$ sudo make install
$ cd ../

$ tar fxz frontier-0.1.tar.gz
$ cd frontier-0.1/
$ ./configure
$ make
$ sudo make install
$ cd ../

$ tar fxz fukashigi-0.1.tar.gz
$ cd fukashigi-0.1/
$ ./configure
$ make
$ make check
$ sudo make install
$ cd ../
```

If you use a 64-bit machine, you can pass `--enable-64bit` option to
configure scripts for all the packages.

Finally, we can do tests for DNET by:

```bash
$ make check
:
ok
```

If you found "ok" at the end of test results, the installation would
have been done successfully.

Usage
---------------------------------------------------------------------

We provide a brief example for feasible configuration search and power
loss minimization.  A small distribution network including three
feeders and sixteen switches in the examples.  This network data is
found in `test/data.yaml`.  The data format will be described in the
next section.

For both configuration search and loss minimization, we first
enumerate all feasible configurations in the compressive graph
represesntation (don't worry, you do not have to understand the
complicated graph representation).

In this example, we choose `/tmp/dnet` as the output directory, in
which result files will be placed.

```bash
$ python script/dnet-enumerator test/data.yaml /tmp/dnet
```

You find some files in `/tmp/dnet`, and `/tmp/dnet/diagram` includes
all feasible configurations.

### Feasible configuration search

We count the number of all the feasible configurations.

```bash
$ fukashigi -n 16 -t cardinality /tmp/dnet/diagram
111
```

This network has 111 feasible configurations.

Next, we do random sampling; select a single feasible configuration
uniformly randomly from feasible ones.

```bash
$ fukashigi -n 16 -t 1 /tmp/dnet/diagram 
1 3 4 5 6 8 9 10 11 12 14 16 
```

The result shows a list of switch numbers that are closed in the
configuration (your result may be different depending on random number
generators).

We retrieve configurations by issuing a query; e.g., switch-1 to
switch-5 are closed, while switch-8 *or* switch-9 is open.

```bash
$ echo "1 2 3 4 5" > closed
$ echo "8 9" > open
$ fukashigi -n 16 -t e /tmp/dnet/diagram "/" closed "%" open
7 8 10 12 13 14 15
7 8 10 12 13 14 16
7 8 10 12 13 15 16
7 9 10 12 13 14 15
7 9 10 12 13 14 16
7 9 10 12 13 15 16
```

The result shows six configurations that meet the query; note that
closed switches in the query (switch-1 to switch-5) are omitted.

Finally, we can calculate power loss of a given confiugration.

```bash
$ python dnet/core.py test/data.yaml -c 1 3 4 5 6 8 9 10 11 12 14 16

```

script/dnet-loss を作って，開閉どちらのスイッチリストも受け付ける

### Power loss minimization

The loss minimization process is divided into two stages; enumerate
all feasible configurations, and search optimal one from them.



Data format
---------------------------------------------------------------------

YAML

図がないと厳しいよなぁ

最適化するときは，スイッチ番号に注意

data in the Fukui-TEPCO format
can be converted by `scripts/dnet-converter`

Limitations
---------------------------------------------------------------------

capacitor

assumptions
see Section 3.1 in doc/dnet-theory.pdf in detail

References
---------------------------------------------------------------------

doc/dnet-theory.pdf

[[1](http://www-alg.ist.hokudai.ac.jp/~thomas/TCSTR/tcstr_12_59/tcstr_12_59.pdf)]
Takeru Inoue, Keiji Takano, Takayuki Watanabe, Jun Kawahara, Ryo
Yoshinaka, Akihiro Kishimoto, Koji Tsuda, Shin-ichi Minato, and
Yasuhiro Hayashi, "Loss Minimization of Power Distribution Networks
with Guaranteed Error Bound," Hokkaido University, Division of
Computer Science, TCS Technical Reports, TCS-TR-A-12-59, August 2012.


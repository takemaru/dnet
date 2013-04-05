PYTHON=python

all:

check: check_prep check_converter check_enumerator check_loss check_optimizer
	@echo ok

check_prep:
	-rm -rf /tmp/dnet
	mkdir -p /tmp/dnet

check_converter:
	$(PYTHON) script/dnet-converter > /tmp/dnet/data.yaml
	diff -bru test/results/data.yaml /tmp/dnet/data.yaml

check_enumerator:
	$(PYTHON) script/dnet-enumerator test/results/data.yaml /tmp/dnet
	diff -bru test/results/subgraphs /tmp/dnet/subgraphs
	diff -bru test/results/section_-001.bitmaps /tmp/dnet/section_-001.bitmaps
	diff -bru test/results/section_-002.bitmaps /tmp/dnet/section_-002.bitmaps
	diff -bru test/results/section_-003.bitmaps /tmp/dnet/section_-003.bitmaps
	diff -bru test/results/diagram /tmp/dnet/diagram

check_loss:
	$(PYTHON) script/dnet-loss test/results/data.yaml -c 1 2 3 5 6 8 9 10 11 13 14 16 > /tmp/dnet/loss
	diff -bru test/results/loss /tmp/dnet/loss

check_optimizer:
	$(PYTHON) script/dnet-optimizer test/results/data.yaml test/results/diagram > /tmp/dnet/result.yaml
	diff -bru test/results/result.yaml /tmp/dnet/result.yaml

clean:
	-rm -fr /tmp/dnet

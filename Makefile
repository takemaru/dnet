all:

check: check_mkdir check_converter check_enumerator check_loss check_optimizer
	@echo ok

check_mkdir:
	-rm -rf /tmp/dnet
	mkdir -p /tmp/dnet

check_converter:
	python script/dnet-converter > /tmp/dnet/data.yaml
	diff -bru test/data.yaml /tmp/dnet/data.yaml

check_enumerator:
	python script/dnet-enumerator test/data.yaml /tmp/dnet
	diff -bru test/subgraphs /tmp/dnet/subgraphs
	diff -bru test/section_-001.bitmaps /tmp/dnet/section_-001.bitmaps
	diff -bru test/section_-002.bitmaps /tmp/dnet/section_-002.bitmaps
	diff -bru test/section_-003.bitmaps /tmp/dnet/section_-003.bitmaps
	diff -bru test/diagram /tmp/dnet/diagram

check_loss:
	python script/dnet-loss test/data.yaml -c 1 2 3 5 6 8 9 10 11 13 14 16 > /tmp/dnet/loss
	diff -bru test/loss /tmp/dnet/loss

check_optimizer:
	python script/dnet-optimizer test/data.yaml test/diagram > /tmp/dnet/result.yaml
	diff -bru test/result.yaml /tmp/dnet/result.yaml

clean:
	-rm -fr /tmp/dnet

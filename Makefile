all:

check: check_mkdir check_converter check_constrain check_optimize
	@echo ok

check_mkdir:
	mkdir -p /tmp/dnet

check_converter:
	python scripts/dnet-converter > /tmp/dnet/data.yaml
	diff -bru test/data.yaml /tmp/dnet/data.yaml

check_constrain:
	python dnet/constrain.py /tmp/dnet < test/data.yaml
	diff -bru test/subgraphs /tmp/dnet/subgraphs
	diff -bru test/section_-001.bitmaps /tmp/dnet/section_-001.bitmaps
	diff -bru test/section_-002.bitmaps /tmp/dnet/section_-002.bitmaps
	diff -bru test/section_-003.bitmaps /tmp/dnet/section_-003.bitmaps

check_optimize:
	python dnet/optimize.py test/diagram < test/data.yaml > /tmp/dnet/result.yaml
	diff -bru test/result.yaml /tmp/dnet/result.yaml

clean:
	-rm -fr /tmp/dnet

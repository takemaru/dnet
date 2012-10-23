all:

test: convert constrain optimize
	@echo ok

convert:
	python grid/convert.py > /tmp/grid.yaml
	diff -bru t/grid.yaml /tmp/grid.yaml

constrain:
	python grid/constrain.py /tmp < t/grid.yaml
	diff -bru t/grid.subgraphs /tmp/grid.subgraphs
	diff -bru t/grid-section_-001.bitmaps /tmp/grid-section_-001.bitmaps
	diff -bru t/grid-section_-002.bitmaps /tmp/grid-section_-002.bitmaps
	diff -bru t/grid-section_-003.bitmaps /tmp/grid-section_-003.bitmaps

optimize:
	python grid/optimize.py t/grid.diagram < t/grid.yaml > /tmp/grid-result.yaml
	diff -bru t/grid-result.yaml /tmp/grid-result.yaml

clean:
	rm -f topology.yaml switches.yaml sections.yaml graph.dat

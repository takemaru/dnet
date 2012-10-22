all:

test: convert constrain
	@echo ok

convert:
	python convert.py > /tmp/grid.yaml
	diff -bru t/grid.yaml /tmp/grid.yaml

constrain:
	python constrain.py /tmp < t/grid.yaml
	diff -bru t/grid.subgraphs /tmp/grid.subgraphs
	diff -bru t/grid-section_-001.bitmaps /tmp/grid-section_-001.bitmaps
	diff -bru t/grid-section_-002.bitmaps /tmp/grid-section_-002.bitmaps
	diff -bru t/grid-section_-003.bitmaps /tmp/grid-section_-003.bitmaps

clean:
	rm -f topology.yaml switches.yaml sections.yaml graph.dat

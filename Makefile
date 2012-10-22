all:

test: convert constrain
	@echo ok

convert:
	python convert.py > grid.yaml
	diff -bru t/grid.yaml grid.yaml

constrain:
	python constrain.py < grid.yaml
	diff -bru t/grid.subgraphs grid.subgraphs
	diff -bru t/grid-section_-001.bitmaps grid-section_-001.bitmaps
	diff -bru t/grid-section_-002.bitmaps grid-section_-002.bitmaps
	diff -bru t/grid-section_-003.bitmaps grid-section_-003.bitmaps

clean:
	rm -f topology.yaml switches.yaml sections.yaml graph.dat

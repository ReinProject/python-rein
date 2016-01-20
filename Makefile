clean:
	rm -f enrollment.txt
	rm -f enrollment.txt.sig

test:
	python -m unittest2 rein/lib/*.py

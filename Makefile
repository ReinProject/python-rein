clean:
	rm -f enrollment.txt
	rm -f enrollment.txt.sig

test:
	nosetests -v

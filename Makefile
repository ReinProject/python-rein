clean:
	rm -f enrollment.txt
	rm -f enrollment.txt.sig

test:
	nosetests -v --ignore-files="test_cli.py"
	
test_all:
	nosetests -v

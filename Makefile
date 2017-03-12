clean:
	rm -f enrollment.txt
	rm -f enrollment.txt.sig

test:
	nosetests \
		--with-coverage \
		--cover-erase \
		--cover-package="rein" \
		--verbose \
		--ignore-files="test_cli.py"
	
test_all:
	nosetests \
		--with_coverage \
		--cover-erase \
		--cover-package="rein" \
		--verbose

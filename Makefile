.PHONY: check pep8 pyflakes

all: check

check: pep8 pyflakes

pep8:
	pep8 --exclude=.git,cache,docs --ignore=E123,E126,E128,E251 --max-line-length 120 .

pyflakes:
	rm -Rf cache/templates/
	pyflakes .

.PHONY: check pep8 pyflakes dist i18n assets

all: check

check: pep8 pyflakes

pep8:
	pep8 --exclude=.git,cache,docs --ignore=E123,E126,E128,E251 --max-line-length 120 .

pyflakes:
	rm -Rf cache/templates/
	pyflakes .

i18n:
	@python setup.py extract_messages
	@python setup.py update_catalog

dist:
	@python setup.py clean
	@python setup.py compile_catalog build_assets sdist

update:
	bower install
	@python setup.py compile_catalog build_assets

assets:
	@python setup.py build_assets

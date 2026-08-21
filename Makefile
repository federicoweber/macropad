CIRCUITPY ?= /Volumes/CIRCUITPY
PYCACHE_DIR ?= /private/tmp/ai-macropad-pycache
CIRCUP ?= circup

.PHONY: check deploy install libraries

check:
	PYTHONPYCACHEPREFIX="$(PYCACHE_DIR)" python3 -m unittest discover -s tests -v
	PYTHONPYCACHEPREFIX="$(PYCACHE_DIR)" python3 -m compileall -q code.py config.py tests

libraries:
	test -d "$(CIRCUITPY)"
	$(CIRCUP) --path "$(CIRCUITPY)" install -r requirements.txt

deploy:
	test -d "$(CIRCUITPY)"
	cp code.py config.py "$(CIRCUITPY)/"
	sync

install: libraries deploy

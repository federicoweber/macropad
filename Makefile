CIRCUITPY ?= /Volumes/CIRCUITPY
PYCACHE_DIR ?= /private/tmp/ai-macropad-pycache
CIRCUP ?= circup

.PHONY: check deploy install libraries

check:
	PYTHONPYCACHEPREFIX="$(PYCACHE_DIR)" python3 -m unittest discover -s tests -v
	PYTHONPYCACHEPREFIX="$(PYCACHE_DIR)" python3 -m compileall -q boot.py code.py config.py spotify_protocol.py spotify_relay.py tests

libraries:
	test -d "$(CIRCUITPY)"
	$(CIRCUP) --path "$(CIRCUITPY)" install -r requirements.txt

deploy:
	test -d "$(CIRCUITPY)"
	cp boot.py code.py config.py spotify_protocol.py "$(CIRCUITPY)/"
	sync

install: libraries deploy

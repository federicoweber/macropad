CIRCUITPY ?= /Volumes/CIRCUITPY
PYCACHE_DIR ?= /private/tmp/ai-macropad-pycache
CIRCUP ?= circup
AUDIO_METER_APP ?= .build/SpotifyAudioMeter.app
AUDIO_METER_BIN := $(AUDIO_METER_APP)/Contents/MacOS/SpotifyAudioMeter
SWIFT_MODULE_CACHE ?= /private/tmp/ai-macropad-swift-module-cache

.PHONY: audio-meter check deploy install libraries

audio-meter:
	mkdir -p "$(AUDIO_METER_APP)/Contents/MacOS"
	mkdir -p "$(SWIFT_MODULE_CACHE)"
	cp host/SpotifyAudioMeter/Info.plist "$(AUDIO_METER_APP)/Contents/Info.plist"
	CLANG_MODULE_CACHE_PATH="$(SWIFT_MODULE_CACHE)" xcrun swiftc -O -parse-as-library -module-cache-path "$(SWIFT_MODULE_CACHE)" host/SpotifyAudioMeter/main.swift -o "$(AUDIO_METER_BIN)"
	codesign --force --sign - "$(AUDIO_METER_APP)"

check:
	PYTHONPYCACHEPREFIX="$(PYCACHE_DIR)" python3 -m unittest discover -s tests -v
	PYTHONPYCACHEPREFIX="$(PYCACHE_DIR)" python3 -m compileall -q boot.py code.py config.py spotify_protocol.py spotify_relay.py spotify_web_metadata.py tests

libraries:
	test -d "$(CIRCUITPY)"
	$(CIRCUP) --path "$(CIRCUITPY)" install -r requirements.txt

deploy:
	test -d "$(CIRCUITPY)"
	cp boot.py code.py config.py spotify_protocol.py "$(CIRCUITPY)/"
	sync

install: audio-meter libraries deploy

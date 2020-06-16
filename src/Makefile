PYTHON_BIN = python
RCC_COMPILER_BIN = pyside2-rcc
RCC_OUTPUT_FILE = ./resources.qrc

.PHONY: run
run: rcc
	$(PYTHON_BIN) . -u gui

.PHONY: rcc
rcc:
	$(RCC_COMPILER_BIN) $(RCC_OUTPUT_FILE) -compress 9 -name init -o qrc.py

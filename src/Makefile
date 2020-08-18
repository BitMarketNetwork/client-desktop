PYTHON_BIN = python
PIP_BIN = pip
RCC_COMPILER_BIN = pyside2-rcc
RCC_OUTPUT_FILE = ./resources.qrc


.PHONY: gui
gui: rcc
	$(PYTHON_BIN) . -u gui 

.PHONY: drop
drop:
	rm -f $(DB_FILE)

.PHONY: drop_win
drop_win:
	del $(DB_FILE)

.PHONY: rcc
rcc:
	$(RCC_COMPILER_BIN) $(RCC_OUTPUT_FILE) -compress 9 -name init -o qrc.py

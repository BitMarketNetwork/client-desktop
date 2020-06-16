
# client-desktop

## General warnings

* look for all available commands in Makefile
* under Windows OS some commands have *_win suffix and you should use them instead of originals

## Installation guide for developpers

* create virtual environment

```bash
virtualenv .env -p /usr/bin/python3.7
```

or

```bash
python -m venv .env
```

* activate virtual environment

```bash
source .env/bin/activate
```

or for Windows

```bash
source .env\Scripts\activate
```

* move to the code

```bash
    cd src
```

* install python packages

```bash
    pip install -r requirements_prod.txt
```

* launch

```bash
    make
```

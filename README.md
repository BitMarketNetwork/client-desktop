# BitMarket Network Client

[![image logo]][homepage]

# Table of Contents

- [Development version](#development-version)
    - [Requirements](#requirements)
    - [Windows Requirements](#windows-requirements)
    - [macOS Requirements](#macos-requirements)
    - [Linux Requirements](#linux-requirements)
    - [Run application](#run-application)

# Development version

AMD64 (x86_64) architecture only has been tested among other platforms. Please
don't try to use x86!

### Requirements:

- GNU Make 4.1+
- Python 3.7+ with PIP
    * [requirements.txt](requirements.txt)
    * [requirements-dev.txt](requirements-dev.txt)
- Qt 5.15.1
- NSIS 3.06+ (for Windows)
- AppImage Tool 12 (for Linux)

### Windows Requirements

- **[Python 3.7.x 64-bit and PIP][python download windows]**<br/>
  For more convenience, add Python to the `PATH` environment variable, this can
  be done by the installer itself. After completing the installation you may
  install PIP:
  ```shell
  $ python -m ensurepip
  ```


- **[Qt 5.15.1 64-bit][qt download]**<br/>
  Currently for Qt an online installer only is available. Download and run it.
  Install the following packages:
    - `Qt/Developer and Designer Tools/MinGW 8.x.x 64-bit` this is required for
      the `mingw32-make` tool. For more convenience, add the package bin path to
      the `PATH` environment variable.
    - `Qt/Qt 5.15.1/MinGW 8.x.x 64-bit` this is required for the `lrelease`,
      `lupdate` tools.


- **[NSIS 3.06+][nsis download]**<br/>
  This tool is required only if you want to create the distribution package.


### macOS Requirements

- **[Homebrew][homebrew download]**<br/>
  Install it if you don't want to install any other requirements manually.


- **Python 3.7+**<br/>
  By default Homebrew installs the latest Python version, some PIP-packages may
  be non-compatible with the latest Python version.
  ```bash
  $ brew install python@3.7
  # optional
  $ brew link --overwrite python@3.7
  ```


- **GNU Make 4.1+**<br/>
  Unfortunately, preinstalled `make` by XCode is outdated
  ```bash
  $ brew install make
  ```


- **Qt 5.15.x**<br/>
  ```bash
  $ brew install qt5@5.15.1
  ```


### Linux Requirements

- Basic packages:<br/>
  **Ubuntu and Debian:**
  ```bash
  $ sudo apt install make python3-pip qt5-default qttools5-dev-tools
  ```
  **Arch Linux:**
  ```bash
  $ sudo pacman -S --needed make python-pip qt5-tools
  ```


- **[AppImage Tool 12][appimage download]**<br/>
  This tool is required only if you want to create the distribution package.
  ```bash
  $ wget https://github.com/AppImage/AppImageKit/releases/download/12/appimagetool-x86_64.AppImage
  $ chmod +x appimagetool-x86_64.AppImage
  $ sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
  ```


### Run application

Optionally, for avoiding the requirement's conflict you can create a
[Python virtual environment][python venv] for running the application
independently of the system site directories

Some required executables (especially Windows) can be unavailable in `PATH`
environment variable, see [Makefile](Makefile) file. In the first lines you can
see `BMN_*_BIN_DIR` variables. You can change their values inline or set the
appropriate environment variables.

- Check out the code from GitHub, or download and extract tarball / ZIP archive:
  ```shell
  $ git clone git://github.com/BitMarketNetwork/client-desktop.git
  $ cd client-desktop
  ```

- Install application dependencies:
  ```shell
  $ python3 -m pip install -r requirements-dev.txt
  # or
  $ python -m pip install -r requirements-dev.txt
  ```
  or if you don't want to create the distribution package:
  ```shell
  $ python3 -m pip install -r requirements.txt
  # or
  $ python -m pip install -r requirements.txt
  ```
  **For Linux only:** Possibly required PySide2 tools will be installed to
  the `~/.local/bin`, because for more convenience you might want to add this
  path to `PATH` environment variable:
  ```bash
  $ export PATH=~/.local/bin:$PATH
  ```


- Build/update advanced production files:
  ```shell
  # for Windows:
  $ mingw32-make
  # for macOS:
  $ gmake
  # for Linux:
  $ make
  ```

- Run tests (optional):
  ```shell
  # for Windows:
  $ mingw32-make check
  # for macOS:
  $ gmake gui check
  # for Linux:
  $ make gui check
  ```

- Run:
  ```shell
  # for Windows:
  $ mingw32-make gui
  # for macOS:
  $ gmake gui
  # for Linux:
  $ make gui
  # or
  $ python3 bmn-client
  ```

- Build the distribution package:
  ```shell
  # for Windows:
  $ mingw32-make dist
  # for macOS:
  $ gmake dist
  # for Linux:
  $ make dist
  ```

[homepage]:
    https://bitmarket.network
    "BitMarket Network"

[image logo]:
    bmnclient/resources/images/logo.svg
    "BitMarket Network"

[python download windows]:
    https://www.python.org/downloads/windows/
    "Download Python"

[qt download]:
    https://www.qt.io/download
    "Download Qt"

[nsis download]:
    https://nsis.sourceforge.io/Download
    "Download NSIS"

[python venv]:
    https://docs.python.org/3/library/venv.html
    "Creation of virtual environments"

[homebrew download]:
    https://brew.sh
    "Download Homebrew"

[appimage download]:
    https://github.com/AppImage/AppImageKit/releases/tag/12
    "Download AppImage"

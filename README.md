# BitMarket Network Client

[![image logo]][homepage]

# Table of Contents

- [Development version](#development-version)
    - [Requirements](#requirements)
    - [Windows Requirements](#windows-requirements)
    - [macOS Requirements](#macos-requirements)
    - [Linux Requirements](#linux-requirements)
    - [Run Application](#run-application)

# Development version

AMD64 (x86_64) architecture only has been tested among other platforms. Please
don't try to use x86!

## Requirements

- GNU Make 4.1+
- Python 3.7+ with PIP
    * [requirements.txt](requirements.txt)
    * [requirements-dev.txt](requirements-dev.txt)
- MinGW-w64 8.1+ (for Windows)
- NSIS 3.06+ (for Windows)
- AppImage Tool 12 (for Linux)

## Windows Requirements

- **[Python 3.7+ (64-bit) and PIP][python download windows]**:

  For more convenience, add Python to the `PATH` environment variable, this can
  be done by the installer itself. After completing the installation you may
  install PIP:
  ```shell
  $ python -m ensurepip
  ```

- **[MinGW-w64 8.1+][mingw download]**:

  Run the mingw-w64-install.exe. When asked, select:
    - Version: **8.1.0 (or later)**
    - Architecture: **x86_64**
    - Threads: **(any)**
    - Exception: **(any)**
    - Build version: **(any)**

  For more convenience, add the package bin path (for example
  `C:\Program Files\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin`) to
  the `PATH` environment variable.

- **[NSIS 3.06+][nsis download]**:

  This tool is required only if you want to create the distribution package.

## macOS Requirements

- **[Homebrew][homebrew download]**:

  Install it if you don't want to install any other requirements manually.

- **Python 3.7+**:

  By default, Homebrew installs the latest Python version, some PIP-packages may
  be non-compatible with the latest Python version.
  ```bash
  $ brew install python@3.8
  ```
  optional:
  ```bash
  $ brew link --overwrite python@3.8
  ```

- **GNU Make 4.1**:

  Unfortunately, preinstalled `make` by XCode is outdated.
  ```bash
  $ brew install make
  ```

## Linux Requirements

- **System packages**:

    - Ubuntu and Debian:

      ```bash
      $ sudo apt install make python3-pip
      ```

    - Arch Linux:

      ```bash
      $ sudo pacman -S --needed make python-pip
      ```

- **[AppImage Tool 12][appimage download]**:

  This tool is required only if you want to create the distribution package.
  ```bash
  $ wget https://github.com/AppImage/AppImageKit/releases/download/12/appimagetool-x86_64.AppImage
  $ chmod +x appimagetool-x86_64.AppImage
  $ sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool
  ```

## Run Application

Optionally, for avoiding the requirement's conflict you can create a
[Python virtual environment][python venv] for running the application
independently of the system site directories

Some required executables (especially Windows) can be unavailable in `PATH`
environment variable, see [Makefile](Makefile) file. In the first lines you can
see `BMN_*_BIN_DIR` variables. You can change their values inline or set the
appropriate environment variables.

Depending on your installed environment, in the instructions below you will need
to use `python` instead of `python3`.

- **Check out the code from GitHub, or download and extract tarball / ZIP
  archive**:

  ```shell
  $ git clone git://github.com/BitMarketNetwork/client-desktop.git
  $ cd client-desktop
  ```

- **Install application dependencies**:

  ```shell
  $ python3 -m pip install -r requirements.txt
  ```
  ...and if you want to create the distribution package or run full tests:
  ```shell
  $ python3 -m pip install -r requirements-dev.txt
  ```

- **Windows environment variables**:

  Possibly required PySide6 tools will be installed to the
  `%APPDATA%\Python\Python3x\Scripts`, because for more convenience you might
  want to add this path to `PATH` environment variable.

- **Linux environment variables**:

  Possibly required PySide6 tools will be installed to the `~/.local/bin`,
  because for more convenience you might want to add this path to `PATH`
  environment variable:
  ```bash
  $ export PATH=~/.local/bin:$PATH
  ```

- **Build/Update advanced production files**:

    - Windows:

      ```shell
      $ mingw32-make
      ```

    - macOS:

      ```shell
      $ gmake
      ```

    - Linux:

      ```shell
      $ make
      ```

- **Run tests (optional)**:

    - Windows:

      ```shell
      $ mingw32-make check
      ```

    - macOS:

      ```shell
      $ gmake check
      ```

    - Linux:

      ```shell
      $ make check
      ```

- **Run application**:

    - Windows:

      ```shell
      $ mingw32-make gui
      ```

    - macOS:

      ```shell
      $ gmake gui
      ```

    - Linux:

      ```shell
      $ make gui
      ```
      ...or:
      ```shell
      $ python3 bmn-client
      ```

- **Build the distribution package**:

    - Windows:

      ```shell
      $ mingw32-make dist
      ```

    - macOS:

      ```shell
      $ gmake dist
      ```

    - Linux:

      ```shell
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

[mingw download]:
https://sourceforge.net/projects/mingw-w64/files/Toolchains%20targetting%20Win32/Personal%20Builds/mingw-builds/installer/mingw-w64-install.exe
"Download MinGW-w64"

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

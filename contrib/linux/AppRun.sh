#!/bin/sh -e
APPDIR="$(dirname "$(readlink -e "${0}")")"
exec "${D}{APPDIR}/${BMN_SHORT_NAME}" "${@}"

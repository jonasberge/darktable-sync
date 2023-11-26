#!/bin/bash

BASE_DIR=/media/photography/Darktable
INSTALL_DIR=$BASE_DIR/install
PREFIX=$INSTALL_DIR/darktable-ubuntu
DARKTABLE_BIN_DIR=$PREFIX/bin
MERGE_SCRIPT=$INSTALL_DIR/scripts/merge-config.py
LINUX_CONFIG_DIR=$BASE_DIR/config-ubuntu
WINDOWS_CONFIG_DIR=$BASE_DIR/config-windows

set -x

echo "(merging config directories)"
cd "$BASE_DIR"
python3 "$MERGE_SCRIPT" -t 2 -m newest -d linux -l "$LINUX_CONFIG_DIR" -w "$WINDOWS_CONFIG_DIR" --debug | tee "$(dirname $MERGE_SCRIPT)/merge-log.txt"

echo "(launching darktable)"
cd "$DARKTABLE_BIN_DIR"
"$DARKTABLE_BIN_DIR/$1" --configdir "$LINUX_CONFIG_DIR" ${@:2}

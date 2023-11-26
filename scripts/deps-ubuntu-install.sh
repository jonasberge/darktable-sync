#!/bin/bash

cd $(mktemp -d)
chmod 0755 .
mkdir tmp
cd tmp

# old: '/^#\sdeb-src /s/^# *//;t;d'
# new: '/^deb /s/^deb /deb-src /;t;d'

sed -e '/^deb /s/^deb /deb-src /;t;d' "/etc/apt/sources.list" \
  | sudo tee /etc/apt/sources.list.d/darktable-sources-tmp.list \
  && (
    sudo apt-get update
    sudo mk-build-deps -i -r darktable
  )
sudo rm /etc/apt/sources.list.d/darktable-sources-tmp.list

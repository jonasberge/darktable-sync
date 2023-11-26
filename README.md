# Darktable sync

Some helper scripts to allow for the following neat things,
so I can edit my photos without hassle,
no matter on which operating system I am at the moment:

- I need the same Darktable version on both operating systems
- I need to be able to edit the Darktable source and compile that (`darktable-git`)
- All my presets should be synced (they are in `data.db`)
- My shortcuts should be synced as well (`.shortcutsrc`)
- And of course my settings should be synced (`.darktablerc`)

All this is done with these scripts.
Only thing missing is that the library is not synced,
but that's not trivial, as Windows and Linux use different paths
(`C:\path` vs. `/path`)
and my photo partition has different base paths on those operating systems
(`H:\` on Windows, `/media/photography` on Linux).
A solution for this might be implemented in the future.
The biggest problem with this is only
that if I create a second version of a photo
it won't be shown if I switch operating systems
until I re-import the already imported folder,
which is sometimes irritating.

Main code here is the script which merges
two `.darktablerc` files (or `.shortcutsrc`) to create one which includes the most recent changes:
[`scripts/merge-config.py`](./scripts/merge-config.py).

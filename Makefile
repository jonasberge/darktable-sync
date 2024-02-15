GIT_URL=https://github.com/darktable-org/darktable.git
INSTALL_PREFIX_UBUNTU=/media/photography/Darktable/install/darktable-ubuntu
INSTALL_PREFIX_WINDOWS=/f/Darktable/install/darktable-windows
PARALLELISM_CORES=8

.PHONY: clone checkout-git-branch deps-ubuntu deps-msys2 update-lensfun-database \
	install-ubuntu install-windows build-ubuntu build-windows clean-ubuntu clean-windows

clone: darktable-git

darktable-git:
	git clone --recurse-submodules $(GIT_URL) $@

checkout-git-branch:
	cd darktable-git; \
		git fetch --tags darktable; \
		git submodule update --recursive; \
		cat ../git-branch | xargs git checkout; \
		touch .nobackup

deps-ubuntu:
	sudo bash scripts/deps-ubuntu-install.sh

darktable-git/build_ubuntu: checkout-git-branch
	cd darktable-git; \
		mkdir build_ubuntu; \
		cd build_ubuntu; \
		cmake -DCMAKE_INSTALL_PREFIX=$(INSTALL_PREFIX_UBUNTU) ..; \
		cmake --build . -j $(PARALLELISM_CORES)

build-ubuntu: darktable-git/build_ubuntu
clean-ubuntu:
	cd darktable-git; rm -rf build_ubuntu

install-ubuntu: darktable-git/build_ubuntu
	rm -rf $(shell basename $(INSTALL_PREFIX_UBUNTU))
	cd darktable-git/build_ubuntu; \
		sudo cmake --install .
	touch "$(INSTALL_PREFIX_UBUNTU)/.nobackup"

# https://github.com/darktable-org/darktable/tree/master/packaging/windows
deps-msys2:
	pacman -Syu
	pacman -S --needed --noconfirm base-devel git intltool po4a
	pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-{cc,cmake,gcc-libs,ninja,nsis,omp}
	pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-{exiv2,lcms2,lensfun,dbus-glib,openexr,sqlite3,libxslt,libavif,libheif,libjxl,libwebp,libsecret,lua,graphicsmagick,openjpeg2,gtk3,pugixml,libexif,osm-gps-map,libgphoto2,drmingw,gettext,icu,iso-codes,python-jsonschema}
	pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-gmic
	pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-{portmidi,SDL2}

# this must be done in a UCRT terminal
darktable-git/build_windows: checkout-git-branch
	lensfun-update-data || true
	cd darktable-git; \
		mkdir build_windows; \
		cd build_windows; \
		cmake -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$(INSTALL_PREFIX_WINDOWS) ..; \
		cmake --build . -j $(PARALLELISM_CORES)

build-windows: darktable-git/build_windows
clean-windows:
	cd darktable-git; rm -rf build_windows

install-windows: darktable-git/build_windows
	cd darktable-git/build_windows; \
		cmake --install .
	touch "$(INSTALL_PREFIX_WINDOWS)/.nobackup"

install-windows-exe: darktable-git/build_windows
	ls darktable-git/build_windows/darktable-*-win64.exe | head -1 | xargs start

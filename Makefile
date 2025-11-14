.PHONY: binary pkg install-local uninstall-local clean \
        binary-dev binary-alpha binary-beta binary-prod \
        pkg-dev pkg-alpha pkg-beta pkg-prod

binary:
	bash packaging/macos/build_binary.sh

pkg:
	bash packaging/macos/build_pkg.sh

binary-dev:
	PREID=dev bash packaging/macos/build_binary.sh
binary-alpha:
	PREID=alpha bash packaging/macos/build_binary.sh
binary-beta:
	PREID=beta bash packaging/macos/build_binary.sh
binary-prod:
	PREID= bash packaging/macos/build_binary.sh

pkg-dev:
	PREID=dev bash packaging/macos/build_pkg.sh
pkg-alpha:
	PREID=alpha bash packaging/macos/build_pkg.sh
pkg-beta:
	PREID=beta bash packaging/macos/build_pkg.sh
pkg-prod:
	PREID= bash packaging/macos/build_pkg.sh

install-local: binary
	bash scripts/install_local_mac.sh

uninstall-local:
	bash scripts/uninstall_local_mac.sh

clean:
	rm -rf build dist .packaging-venv *.spec

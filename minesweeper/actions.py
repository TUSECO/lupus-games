#!/usr/bin/python3
from luppo.actionsapi import luppotools
from luppo.actionsapi import shelltools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("MINESWEEPER_SRC_DIR", os.getcwd())

    # Copy application main entry and package directory
    main_py = os.path.join(src_dir, "minesweeper.py")
    if not os.path.isfile(main_py):
        main_py = "minesweeper.py"
    if os.path.isfile(main_py):
        luppotools.insinto("/usr/share/minesweeper", main_py)

    # Launcher script (/usr/bin/minesweeper)
    launcher_path = os.path.join(src_dir, "minesweeper")
    if not os.path.isfile(launcher_path):
        launcher_path = "minesweeper"

    if not os.path.isfile(launcher_path):
        with open("minesweeper", "w") as f:
            f.write("#!/bin/bash\nexec python3 /usr/share/minesweeper/minesweeper.py \"$@\"\n")
        os.chmod("minesweeper", 0o755)
        launcher_path = "minesweeper"

    luppotools.dobin(launcher_path)

    # Desktop entry
    desktop_path = os.path.join(src_dir, "minesweeper.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "minesweeper.desktop"
    if os.path.isfile(desktop_path):
        luppotools.insinto("/usr/share/applications", desktop_path)

    # App icon
    icon_path = os.path.join(src_dir, "minesweeper.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join("minesweeper.png")
    if os.path.isfile(icon_path):
        luppotools.insinto("/usr/share/minesweeper", icon_path, "minesweeper.png")
    if os.path.isfile(icon_path):
        luppotools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "minesweeper.png")

    license_path = os.path.join(src_dir, "LICENSE")
    if not os.path.isfile(license_path):
        license_path = "LICENSE"
    if os.path.isfile(license_path):
        luppotools.dodoc(license_path)
#!/usr/bin/python3
from luppo.actionsapi import luppotools
from luppo.actionsapi import shelltools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("TICTACTOE_SRC_DIR", os.getcwd())

    # Copy application main entry and package directory
    main_py = os.path.join(src_dir, "tictactoe.py")
    if not os.path.isfile(main_py):
        main_py = "tictactoe.py"
    if os.path.isfile(main_py):
        luppotools.insinto("/usr/share/tictactoe", main_py)

    # Launcher script (/usr/bin/tictactoe)
    launcher_path = os.path.join(src_dir, "tictactoe")
    if not os.path.isfile(launcher_path):
        launcher_path = "tictactoe"
    
    if not os.path.isfile(launcher_path):
        with open("tictactoe", "w") as f:
            f.write("#!/bin/bash\nexec python3 /usr/share/tictactoe/tictactoe.py \"$@\"\n")
        os.chmod("tictactoe", 0o755)
        launcher_path = "tictactoe"

    luppotools.dobin(launcher_path)

    # Desktop entry
    desktop_path = os.path.join(src_dir, "tictactoe.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "tictactoe.desktop"
    if os.path.isfile(desktop_path):
        luppotools.insinto("/usr/share/applications", desktop_path)

    # App icon
    icon_path = os.path.join(src_dir, "tictactoe.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join("tictactoe.png")
    if os.path.isfile(icon_path):
        luppotools.insinto("/usr/share/tictactoe", icon_path, "tictactoe.png")
    if os.path.isfile(icon_path):
        luppotools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "tictactoe.png")

    license_path = os.path.join(src_dir, "LICENSE")
    if not os.path.isfile(license_path):
        license_path = "LICENSE"
    if os.path.isfile(license_path):
        luppotools.dodoc(license_path)

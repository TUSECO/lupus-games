#!/usr/bin/python3
from pisi.actionsapi import pisitools
from pisi.actionsapi import shelltools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("SNAKE_SRC_DIR", os.getcwd())

    # Copy application main entry and package directory
    main_py = os.path.join(src_dir, "snake.py")
    if not os.path.isfile(main_py):
        main_py = "snake.py"
    if os.path.isfile(main_py):
        pisitools.insinto("/usr/share/snake", main_py)

    # Launcher script (/usr/bin/snake)
    launcher_path = os.path.join(src_dir, "snake")
    if not os.path.isfile(launcher_path):
        launcher_path = "snake"

    if not os.path.isfile(launcher_path):
        with open("snake", "w") as f:
            f.write("#!/bin/bash\nexec python3 /usr/share/snake/snake.py \"$@\"\n")
        os.chmod("snake", 0o755)
        launcher_path = "snake"

    pisitools.dobin(launcher_path)

    # Desktop entry
    desktop_path = os.path.join(src_dir, "snake.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "snake.desktop"
    if os.path.isfile(desktop_path):
        pisitools.insinto("/usr/share/applications", desktop_path)

    # App icon
    icon_path = os.path.join(src_dir, "snake.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join("snake.png")
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/snake", icon_path, "snake.png")
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "snake.png")

    license_path = os.path.join(src_dir, "LICENSE")
    if not os.path.isfile(license_path):
        license_path = "LICENSE"
    if os.path.isfile(license_path):
        pisitools.dodoc(license_path)
#!/usr/bin/python3
from pisi.actionsapi import pisitools
from pisi.actionsapi import shelltools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("FLAPPYBIRD_SRC_DIR", os.getcwd())

    # Copy application main entry and package directory
    main_py = os.path.join(src_dir, "flappybird.py")
    if not os.path.isfile(main_py):
        main_py = "flappybird.py"
    if os.path.isfile(main_py):
        pisitools.insinto("/usr/share/flappybird", main_py)

    flappybird_dir = os.path.join(src_dir, "assets")
    if not os.path.isdir(flappybird_dir):
        flappybird_dir = "assets"
    if os.path.isdir(flappybird_dir):
        pisitools.insinto("/usr/share/flappybird", flappybird_dir)

    # Launcher script (/usr/bin/flappybird)
    launcher_path = os.path.join(src_dir, "flappybird")
    if not os.path.isfile(launcher_path):
        launcher_path = "flappybird"
    
    if not os.path.isfile(launcher_path):
        with open("flappybird", "w") as f:
            f.write("#!/bin/bash\nexec python3 /usr/share/flappybird/flappybird.py \"$@\"\n")
        os.chmod("flappybird", 0o755)
        launcher_path = "flappybird"

    pisitools.dobin(launcher_path)

    # Desktop entry
    desktop_path = os.path.join(src_dir, "flappybird.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "flappybird.desktop"
    if os.path.isfile(desktop_path):
        pisitools.insinto("/usr/share/applications", desktop_path)

    # App icon
    icon_path = os.path.join(src_dir, "flappybird.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join("flappybird.png")
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/flappybird", icon_path, "flappybird.png")
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "flappybird.png")

    license_path = os.path.join(src_dir, "LICENSE")
    if not os.path.isfile(license_path):
        license_path = "LICENSE"
    if os.path.isfile(license_path):
        pisitools.dodoc(license_path)

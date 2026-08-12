#!/usr/bin/python3
from pisi.actionsapi import pisitools
from pisi.actionsapi import shelltools
import os

WorkDir = "."

def build():
    pass

def install():
    src_dir = os.environ.get("CHESS_SRC_DIR", os.getcwd())

    # Copy application main entry and package directory
    main_py = os.path.join(src_dir, "chess.py")
    engine_py = os.path.join(src_dir, "chess_engine.py")
    if not os.path.isfile(main_py):
        main_py = "chess.py"
    if not os.path.isfile(main_py):
        engine_py = "chess_engine.py"
    if os.path.isfile(main_py):
        pisitools.insinto("/usr/share/chess", main_py)
    if os.path.isfile(engine_py):
        pisitools.insinto("/usr/share/chess", engine_py)

    # Launcher script (/usr/bin/chess)
    launcher_path = os.path.join(src_dir, "chess")
    if not os.path.isfile(launcher_path):
        launcher_path = "chess"

    if not os.path.isfile(launcher_path):
        with open("chess", "w") as f:
            f.write("#!/bin/bash\nexec python3 /usr/share/chess/chess.py \"$@\"\n")
        os.chmod("chess", 0o755)
        launcher_path = "chess"

    pisitools.dobin(launcher_path)

    # Desktop entry
    desktop_path = os.path.join(src_dir, "chess.desktop")
    if not os.path.isfile(desktop_path):
        desktop_path = "chess.desktop"
    if os.path.isfile(desktop_path):
        pisitools.insinto("/usr/share/applications", desktop_path)

    # App icon
    icon_path = os.path.join(src_dir, "chess.png")
    if not os.path.isfile(icon_path):
        icon_path = os.path.join("chess.png")
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/chess", icon_path, "chess.png")
    if os.path.isfile(icon_path):
        pisitools.insinto("/usr/share/icons/hicolor/128x128/apps", icon_path, "chess.png")

    license_path = os.path.join(src_dir, "LICENSE")
    if not os.path.isfile(license_path):
        license_path = "LICENSE"
    if os.path.isfile(license_path):
        pisitools.dodoc(license_path)

#!/usr/bin/env bash
# =============================================================================
#  install.sh — LupuS Games Installer
#  Directory: ~/.local/share/lupus-games/
#  Usage:
#    ./install.sh install
#    ./install.sh uninstall
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BASE="${HOME}/.local/share/lupus-games"
DESKTOP_DIR="${HOME}/.local/share/applications"
BIN_DIR="${HOME}/.local/bin"

declare -A GAME_SCRIPT=(
    [chess]="chess.py"
    [flappybird]="flappyman.py"
    [snake]="snake.py"
    [tictactoe]="tictactoe.py"
    [minesweeper]="minesweeper.py"
)

declare -A GAME_NAME=(
    [chess]="Chess"
    [flappybird]="FlappyBird"
    [snake]="Snake Game"
    [tictactoe]="TicTacToe"
    [minesweeper]="Minesweeper"
)

declare -A GAME_NAME_TR=(
    [chess]="Satranç"
    [flappybird]="FlappyBird"
    [snake]="Yılan Oyunu"
    [tictactoe]="TicTacToe"
    [minesweeper]="Mayın Tarlası"
)

declare -A GAME_COMMENT=(
    [chess]=""
    [flappybird]=""
    [snake]=""
    [tictactoe]=""
    [minesweeper]=""
)

declare -A GAME_CATEGORY=(
    [chess]="Game;BoardGame;LupuS;"
    [flappybird]="Game;ArcadeGame;LupuS;"
    [snake]="Game;ArcadeGame;LupuS;"
    [tictactoe]="Game;BoardGame;LupuS;"
    [minesweeper]="Game;ArcadeGame;LupuS;"
)

GAMES=(chess flappybird snake tictactoe minesweeper)

# ─── Yardımcı fonksiyonlar ────────────────────────────────────────────────────
info()    { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[HATA]${NC}  $*" >&2; }
header()  { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════${NC}"; \
            echo -e "${BOLD}${CYAN}  $*${NC}"; \
            echo -e "${BOLD}${CYAN}══════════════════════════════════════════${NC}\n"; }

check_python() {
    if command -v python3 &>/dev/null; then
        success "Python3 found: $(python3 --version)"
    else
        error "Python3 not found! Please install Python3 first."
        exit 1
    fi
}

check_pygame() {
    if python3 -c "import pygame" &>/dev/null; then
        success "pygame found."
    else
        warn "pygame not found. Do you want to install it? [E/h]"
        read -r answer
        if [[ "${answer,,}" != "h" ]]; then
            pip3 install pygame --user
            success "pygame installed."
        else
            warn "pygame not installed. Some games may not work."
        fi
    fi
}

# ─── KURULUM ─────────────────────────────────────────────────────────────────
install_games() {
    header "LupuS Games — Starting Installation"

    check_python
    check_pygame

    # Dizinleri oluştur
    mkdir -p "${INSTALL_BASE}"
    mkdir -p "${DESKTOP_DIR}"
    mkdir -p "${BIN_DIR}"

    for game in "${GAMES[@]}"; do
        local src="${SCRIPT_DIR}/${game}"
        local dst="${INSTALL_BASE}/${game}"
        local script="${GAME_SCRIPT[$game]}"
        local name="${GAME_NAME[$game]}"
        local name_tr="${GAME_NAME_TR[$game]}"
        local comment="${GAME_COMMENT[$game]}"
        local category="${GAME_CATEGORY[$game]}"
        local desktop_id="${game}"
        local icon_name="${desktop_id}"

        info "Installing: ${name}..."

        # Kaynak klasör var mı?
        if [[ ! -d "${src}" ]]; then
            warn "  Source directory not found: ${src} — skipping."
            continue
        fi

        # Oyun dosyalarını kopyala (varsa üzerine yaz)
        rm -rf "${dst}"
        cp -r "${src}" "${dst}"
        success "  File copied: ${dst}"

        # Başlatıcı wrapper script oluştur
        local launcher="${BIN_DIR}/${desktop_id}"
        cat > "${launcher}" <<-LAUNCHER
			#!/usr/bin/env bash
			cd "${dst}"
			exec python3 "${dst}/${script}" "\$@"
		LAUNCHER
        chmod +x "${launcher}"
        success "  Launcher created: ${launcher}"

        # .desktop dosyası oluştur
        local desktop_file="${DESKTOP_DIR}/${desktop_id}.desktop"
        cat > "${desktop_file}" <<-DESKTOP
			[Desktop Entry]
			Version=1.0
			Type=Application
			Name=${name}
			Name[tr]=${name_tr}
			Comment=${comment}
			Exec=${launcher}
			Icon=${INSTALL_BASE}/${game}/favicon.png
			Terminal=false
			Categories=${category}
			Keywords=game;${game};
			StartupNotify=true
		DESKTOP
        chmod +x "${desktop_file}"
        success "  .desktop file created: ${desktop_file}"
    done

    # İkon önbelleğini güncelle
    if command -v gtk-update-icon-cache &>/dev/null; then
        gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
    fi

    # KDE menüsünü yenile (kactivities veya kbuildsycoca)
    if command -v kbuildsycoca6 &>/dev/null; then
        kbuildsycoca6 --noincremental 2>/dev/null || true
        success "KDE menu updated (kbuildsycoca6)."
    elif command -v kbuildsycoca5 &>/dev/null; then
        kbuildsycoca5 --noincremental 2>/dev/null || true
        success "KDE menu updated (kbuildsycoca5)."
    else
        warn "kbuildsycoca not found; restart your session to see the menu."
    fi

    # xdg-desktop-menu ile zorla kaydet (opsiyonel, çoğu DE destekler)
    if command -v xdg-desktop-menu &>/dev/null; then
        for game in "${GAMES[@]}"; do
            xdg-desktop-menu install --novendor \
                "${DESKTOP_DIR}/${game}.desktop" 2>/dev/null || true
        done
    fi

    header "Installation Completed!"
    echo -e "  Games installed : ${BOLD}${INSTALL_BASE}/${NC}"
    echo -e "  Launchers    : ${BOLD}${BIN_DIR}/${NC}"
    echo -e "  .desktop files: ${BOLD}${DESKTOP_DIR}/${NC}"
    echo ""
    echo -e "${YELLOW}You can also start the games directly from the terminal:${NC}"
    for game in "${GAMES[@]}"; do
        echo -e "  ${CYAN}${game}${NC}"
    done
    echo ""
}

# ─── KALDIRMA ────────────────────────────────────────────────────────────────
remove_games() {
    header "LupuS Games — Starting Removal"

    rm -rf "${INSTALL_BASE}/" 2>/dev/null || true

    for game in "${GAMES[@]}"; do
        rm -f "${DESKTOP_DIR}/${game}.desktop"
    done

    success "Desktop files removed!"
}

# ─── ANA AKIŞ ────────────────────────────────────────────────────────────────
case "${1:-}" in
    uninstall)
        remove_games
        ;;
    reinstall)
        remove_games
        install_games
        ;;
    help)
        echo ""
        echo -e "${BOLD}Usage:${NC}"
        echo "  ./install.sh           → Install all games"
        echo "  ./install.sh uninstall  → Remove all games"
        echo "  ./install.sh help    → Show this help"
        echo ""
        echo -e "${BOLD}Installation path:${NC} ${INSTALL_BASE}"
        echo ""
        ;;
    install)
        install_games
        ;;
    *)
        error "Unknown argument: $1"
        echo "Usage: ./install.sh [install|uninstall|reinstall|help]"
        exit 1
        ;;
esac

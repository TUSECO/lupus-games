#!/usr/bin/env bash
# =============================================================================
#  install.sh — LupuS Games Installer
#  Oyunları ~/.local/share/lupus-games/ dizinine kurar ve KDE menüsüne ekler.
#  Kullanım:
#    ./install.sh          → Kurulum
#    ./install.sh --remove → Kaldırma
# =============================================================================

set -euo pipefail

# ─── Renkler ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ─── Sabitler ────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_BASE="${HOME}/.local/share/lupus-games"
DESKTOP_DIR="${HOME}/.local/share/applications"
BIN_DIR="${HOME}/.local/bin"

# ─── Oyun tanımları: "klasör|ana_script|görünen_ad|exec_args" ────────────────
declare -A GAME_SCRIPT=(
    [chess]="chess.py"
    [flappybird]="flappyman.py"
    [snake]="snake.py"
    [tictactoe]="tictactoe.py"
)

declare -A GAME_NAME=(
    [chess]="Chess"
    [flappybird]="Flappy Bird"
    [snake]="Snake"
    [tictactoe]="Tic-Tac-Toe"
)

declare -A GAME_COMMENT=(
    [chess]=""
    [flappybird]=""
    [snake]=""
    [tictactoe]=""
)

declare -A GAME_CATEGORY=(
    [chess]="Game;BoardGame;"
    [flappybird]="Game;ArcadeGame;"
    [snake]="Game;ArcadeGame;"
    [tictactoe]="Game;BoardGame;"
)

GAMES=(chess flappybird snake tictactoe)

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
        success "Python3 bulundu: $(python3 --version)"
    else
        error "Python3 bulunamadı! Lütfen önce Python3 kurun."
        exit 1
    fi
}

check_pygame() {
    if python3 -c "import pygame" &>/dev/null; then
        success "pygame bulundu."
    else
        warn "pygame bulunamadı. Kurmak istiyor musunuz? [E/h]"
        read -r answer
        if [[ "${answer,,}" != "h" ]]; then
            pip3 install pygame --user
            success "pygame kuruldu."
        else
            warn "pygame kurulmadı. Oyunlar çalışmayabilir."
        fi
    fi
}

# ─── KURULUM ─────────────────────────────────────────────────────────────────
install_games() {
    header "LupuS Games — Kurulum Başlıyor"

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
        local comment="${GAME_COMMENT[$game]}"
        local category="${GAME_CATEGORY[$game]}"
        local desktop_id="lupus-${game}"
        local icon_name="${desktop_id}"

        info "Kuruluyor: ${name}..."

        # Kaynak klasör var mı?
        if [[ ! -d "${src}" ]]; then
            warn "  Kaynak klasör bulunamadı: ${src} — atlanıyor."
            continue
        fi

        # Oyun dosyalarını kopyala (varsa üzerine yaz)
        rm -rf "${dst}"
        cp -r "${src}" "${dst}"
        success "  Dosyalar kopyalandı: ${dst}"

        # Başlatıcı wrapper script oluştur
        local launcher="${BIN_DIR}/${desktop_id}"
        cat > "${launcher}" <<-LAUNCHER
			#!/usr/bin/env bash
			cd "${dst}"
			exec python3 "${dst}/${script}" "\$@"
		LAUNCHER
        chmod +x "${launcher}"
        success "  Başlatıcı oluşturuldu: ${launcher}"

        # .desktop dosyası oluştur
        local desktop_file="${DESKTOP_DIR}/${desktop_id}.desktop"
        cat > "${desktop_file}" <<-DESKTOP
			[Desktop Entry]
			Version=1.0
			Type=Application
			Name=${name}
			Comment=${comment}
			Exec=${launcher}
			Icon=${INSTALL_BASE}/${game}/favicon.png
			Terminal=false
			Categories=${category}
			Keywords=game;oyun;${game};
			StartupNotify=true
		DESKTOP
        chmod +x "${desktop_file}"
        success "  .desktop dosyası oluşturuldu: ${desktop_file}"
    done

    # İkon önbelleğini güncelle
    if command -v gtk-update-icon-cache &>/dev/null; then
        gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
    fi

    # KDE menüsünü yenile (kactivities veya kbuildsycoca)
    if command -v kbuildsycoca6 &>/dev/null; then
        kbuildsycoca6 --noincremental 2>/dev/null || true
        success "KDE menüsü güncellendi (kbuildsycoca6)."
    elif command -v kbuildsycoca5 &>/dev/null; then
        kbuildsycoca5 --noincremental 2>/dev/null || true
        success "KDE menüsü güncellendi (kbuildsycoca5)."
    else
        warn "kbuildsycoca bulunamadı; menüyü görmek için oturumu yeniden başlatın."
    fi

    # xdg-desktop-menu ile zorla kaydet (opsiyonel, çoğu DE destekler)
    if command -v xdg-desktop-menu &>/dev/null; then
        for game in "${GAMES[@]}"; do
            xdg-desktop-menu install --novendor \
                "${DESKTOP_DIR}/lupus-${game}.desktop" 2>/dev/null || true
        done
    fi

    header "Kurulum Tamamlandı!"
    echo -e "  Oyunlar kuruldu : ${BOLD}${INSTALL_BASE}/${NC}"
    echo -e "  Başlatıcılar    : ${BOLD}${BIN_DIR}/${NC}"
    echo -e "  .desktop dosyaları: ${BOLD}${DESKTOP_DIR}/${NC}"
    echo ""
    echo -e "${YELLOW}Oyunları doğrudan terminalde de başlatabilirsiniz:${NC}"
    for game in "${GAMES[@]}"; do
        echo -e "  ${CYAN}lupus-${game}${NC}"
    done
    echo ""
}

# ─── KALDIRMA ────────────────────────────────────────────────────────────────
remove_games() {
    header "LupuS Games — Kaldırma Başlıyor"

    local removed=0

    for game in "${GAMES[@]}"; do
        local name="${GAME_NAME[$game]}"
        local desktop_id="lupus-${game}"

        info "Kaldırılıyor: ${name}..."

        # Oyun dosyalarını sil
        if [[ -d "${INSTALL_BASE}/${game}" ]]; then
            rm -rf "${INSTALL_BASE}/${game}"
            success "  Oyun dosyaları silindi."
            ((removed++))
        else
            warn "  Kurulu değil: ${INSTALL_BASE}/${game}"
        fi

        # Başlatıcı scripti sil
        if [[ -f "${BIN_DIR}/${desktop_id}" ]]; then
            rm -f "${BIN_DIR}/${desktop_id}"
            success "  Başlatıcı silindi: ${BIN_DIR}/${desktop_id}"
        fi

        # .desktop dosyasını sil
        if [[ -f "${DESKTOP_DIR}/${desktop_id}.desktop" ]]; then
            if command -v xdg-desktop-menu &>/dev/null; then
                xdg-desktop-menu uninstall "${DESKTOP_DIR}/${desktop_id}.desktop" 2>/dev/null || true
            fi
            rm -f "${DESKTOP_DIR}/${desktop_id}.desktop"
            success "  .desktop dosyası silindi."
        fi
    done

    # Boşsa ana dizini de sil
    if [[ -d "${INSTALL_BASE}" ]] && [[ -z "$(ls -A "${INSTALL_BASE}")" ]]; then
        rmdir "${INSTALL_BASE}"
        success "Ana dizin silindi: ${INSTALL_BASE}"
    fi

    # İkon önbelleğini güncelle
    if command -v gtk-update-icon-cache &>/dev/null; then
        gtk-update-icon-cache -f -t "${HOME}/.local/share/icons/hicolor" 2>/dev/null || true
    fi

    # KDE menüsünü yenile
    if command -v kbuildsycoca6 &>/dev/null; then
        kbuildsycoca6 --noincremental 2>/dev/null || true
    elif command -v kbuildsycoca5 &>/dev/null; then
        kbuildsycoca5 --noincremental 2>/dev/null || true
    fi

    if [[ $removed -gt 0 ]]; then
        header "Kaldırma Tamamlandı!"
        echo -e "  ${removed} oyun başarıyla kaldırıldı."
    else
        warn "Kaldırılacak kurulu oyun bulunamadı."
    fi
    echo ""
}

# ─── ANA AKIŞ ────────────────────────────────────────────────────────────────
case "${1:-}" in
    --remove|-r|--uninstall)
        remove_games
        ;;
    --help|-h)
        echo ""
        echo -e "${BOLD}Kullanım:${NC}"
        echo "  ./install.sh           → Tüm oyunları kur"
        echo "  ./install.sh --remove  → Tüm oyunları kaldır"
        echo "  ./install.sh --help    → Bu yardımı göster"
        echo ""
        echo -e "${BOLD}Kurulum yolu:${NC} ${INSTALL_BASE}"
        echo ""
        ;;
    "")
        install_games
        ;;
    *)
        error "Bilinmeyen argüman: $1"
        echo "Kullanım: ./install.sh [--remove|--help]"
        exit 1
        ;;
esac

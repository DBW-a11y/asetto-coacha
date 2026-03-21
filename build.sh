#!/usr/bin/env bash
set -euo pipefail

# ─────────────────────────────────────────────────────
# Racing Coach — One-stop build script
# Usage:
#   ./build.sh                         Build all (UI + Python + Electron)
#   ./build.sh --ui-only               Build frontend only
#   ./build.sh --py-only               PyInstaller backend only
#   ./build.sh --platform mac|win|linux  Specify Electron target platform
# ─────────────────────────────────────────────────────

ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT/build"
VENV_DIR="$ROOT/.venv"

# Colours
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}>>>${NC} $*"; }
ok()   { echo -e "${GREEN}✔${NC}  $*"; }
warn() { echo -e "${YELLOW}⚠${NC}  $*"; }
err()  { echo -e "${RED}✖${NC}  $*" >&2; }

# ── Parse arguments ──────────────────────────────────
BUILD_UI=true
BUILD_PY=true
BUILD_ELECTRON=true
PLATFORM=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ui-only)
      BUILD_UI=true; BUILD_PY=false; BUILD_ELECTRON=false; shift ;;
    --py-only)
      BUILD_UI=false; BUILD_PY=true; BUILD_ELECTRON=false; shift ;;
    --platform)
      PLATFORM="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--ui-only] [--py-only] [--platform mac|win|linux]"
      exit 0 ;;
    *)
      err "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Check dependencies ───────────────────────────────
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    err "Missing required command: $1"
    exit 1
  fi
}

log "Checking dependencies..."
check_cmd python3
check_cmd node
check_cmd npm
ok "All base dependencies found"

# ── Load .env if present ─────────────────────────────
if [[ -f "$ROOT/.env" ]]; then
  set -a
  source "$ROOT/.env"
  set +a
  ok "Loaded .env"
fi

# ── Virtualenv + Python deps ─────────────────────────
setup_venv() {
  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
  fi
  source "$VENV_DIR/bin/activate"
  log "Installing Python dependencies..."
  pip install --upgrade pip -q
  pip install -e "$ROOT[dev]" -q
  ok "Python environment ready ($(python3 --version))"
}

# ── Build UI ─────────────────────────────────────────
build_ui() {
  log "Building frontend..."
  cd "$ROOT/ui"
  npm install --silent 2>/dev/null || npm install
  npm run build
  # Sync built assets to backend static directory
  rm -rf "$ROOT/src/racing_coach/ui/dist"
  cp -r "$ROOT/ui/dist" "$ROOT/src/racing_coach/ui/dist"
  ok "Frontend built → ui/dist/"
  cd "$ROOT"
}

# ── PyInstaller backend ──────────────────────────────
build_python() {
  setup_venv
  # Ensure pyinstaller is available
  if ! command -v pyinstaller &>/dev/null; then
    log "Installing PyInstaller..."
    pip install pyinstaller -q
  fi

  log "Building Python backend with PyInstaller..."
  mkdir -p "$BUILD_DIR"
  cd "$ROOT"
  pyinstaller \
    --onefile \
    --name racing-coach-server \
    --distpath "$BUILD_DIR" \
    --workpath "$BUILD_DIR/pyinstaller-work" \
    --specpath "$BUILD_DIR" \
    --add-data "config/default.toml:config" \
    --add-data "src/racing_coach/coach/templates:racing_coach/coach/templates" \
    --hidden-import racing_coach \
    --hidden-import racing_coach.api \
    --hidden-import racing_coach.api.app \
    --hidden-import uvicorn \
    --hidden-import fastapi \
    --clean \
    src/racing_coach/main.py

  ok "Backend binary → $BUILD_DIR/racing-coach-server"
}

# ── Electron packaging ───────────────────────────────
build_electron() {
  log "Building Electron app..."
  cd "$ROOT/desktop"
  npm install --silent 2>/dev/null || npm install

  # Copy backend binary into desktop resources
  mkdir -p "$ROOT/desktop/resources"
  cp "$BUILD_DIR/racing-coach-server" "$ROOT/desktop/resources/" 2>/dev/null || true

  # Copy built UI into desktop resources
  rm -rf "$ROOT/desktop/resources/ui"
  cp -r "$ROOT/ui/dist" "$ROOT/desktop/resources/ui"

  # Determine platform flag
  local platform_flag=""
  case "${PLATFORM:-}" in
    mac|macos|darwin) platform_flag="--mac" ;;
    win|windows)      platform_flag="--win" ;;
    linux)            platform_flag="--linux" ;;
    "")
      case "$(uname -s)" in
        Darwin*)  platform_flag="--mac" ;;
        Linux*)   platform_flag="--linux" ;;
        MINGW*|MSYS*|CYGWIN*) platform_flag="--win" ;;
        *)        warn "Unknown OS, defaulting to current platform"; platform_flag="" ;;
      esac
      ;;
    *) err "Unknown platform: $PLATFORM"; exit 1 ;;
  esac

  npx electron-builder $platform_flag
  ok "Electron app built → desktop/dist/"
  cd "$ROOT"
}

# ── Execute build steps ──────────────────────────────
echo ""
echo "╔══════════════════════════════════════╗"
echo "║     Racing Coach — Build Script      ║"
echo "╚══════════════════════════════════════╝"
echo ""

if $BUILD_UI; then
  build_ui
fi

if $BUILD_PY; then
  build_python
fi

if $BUILD_ELECTRON; then
  build_electron
fi

echo ""
log "Build complete!"
echo ""

# ── Summary ──────────────────────────────────────────
if $BUILD_UI; then
  echo "  Frontend:  $ROOT/ui/dist/"
fi
if $BUILD_PY; then
  echo "  Backend:   $BUILD_DIR/racing-coach-server"
fi
if $BUILD_ELECTRON; then
  echo "  Electron:  $ROOT/desktop/dist/"
fi
echo ""

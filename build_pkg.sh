#!/bin/bash

# SuperStarTrail 构建未签名 PKG 安装包
# 使用方法: ./build_pkg.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

APP_NAME="SuperStarTrail"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
BUNDLE_ID="com.jamesphotography.superstartrail"
PYI_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-/tmp/pyinstaller-superstartrail}"
APPLE_APP_PASSWORD="${APPLE_APP_PASSWORD:-${APP_SPECIFIC_PASSWORD:-}}"

if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "${RED}❌ 未找到可用的虚拟环境 Python: $VENV_PYTHON${NC}"
    echo "请先创建虚拟环境并安装依赖。"
    exit 1
fi

VERSION="$("$VENV_PYTHON" -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('src').resolve())); from utils.settings import APP_VERSION; print(APP_VERSION)")"
PKG_NAME="${APP_NAME}-v${VERSION}-arm64.pkg"
UNSIGNED_PKG_NAME="${APP_NAME}-v${VERSION}-arm64-unsigned.pkg"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SuperStarTrail PKG 打包、签名、公证流程${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}[1/8] 检查必要工具...${NC}"
if ! "$VENV_PYTHON" -c "import PyInstaller" &> /dev/null; then
    echo -e "${RED}❌ 当前仓库的虚拟环境里未安装 PyInstaller${NC}"
    echo "请先执行:"
    echo "  ./.venv/bin/python -m pip install -r requirements-lock.txt -r requirements-dev.txt pyinstaller"
    exit 1
fi

if ! command -v pkgbuild &> /dev/null; then
    echo -e "${RED}❌ 未找到 pkgbuild${NC}"
    exit 1
fi

if ! command -v productsign &> /dev/null; then
    echo -e "${RED}❌ 未找到 productsign${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 所有工具已就绪${NC}"

echo -e "\n${YELLOW}[2/8] 清理之前的构建...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ 清理完成${NC}"

echo -e "\n${YELLOW}[3/8] 使用 PyInstaller 打包应用...${NC}"
PYINSTALLER_CONFIG_DIR="$PYI_CONFIG_DIR" \
    "$VENV_PYTHON" -m PyInstaller SuperStarTrail.spec --clean --noconfirm

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}❌ 打包失败，未找到 ${APP_NAME}.app${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 打包完成: ${APP_PATH}${NC}"

echo -e "\n${YELLOW}[4/8] 签名应用...${NC}"
if [ -n "${SIGNING_IDENTITY:-}" ]; then
    echo "使用应用签名身份: $SIGNING_IDENTITY"
    find "${APP_PATH}/Contents" -type f \( -name "*.dylib" -o -name "*.so" -o -perm -111 \) -print0 | \
        xargs -0 -I {} codesign --force --sign "$SIGNING_IDENTITY" \
            --timestamp \
            --options runtime \
            "{}"

    codesign --force --sign "$SIGNING_IDENTITY" \
        --options runtime \
        --timestamp \
        --entitlements entitlements.plist \
        "$APP_PATH"

    codesign --verify --deep --strict --verbose=2 "$APP_PATH"
    echo -e "${GREEN}✓ 应用签名完成${NC}"
else
    echo -e "${YELLOW}⚠️  未配置 SIGNING_IDENTITY，跳过应用签名${NC}"
fi

echo -e "\n${YELLOW}[5/8] 生成 PKG 安装包...${NC}"
rm -f "dist/${PKG_NAME}" "dist/${UNSIGNED_PKG_NAME}"
pkgbuild \
    --component "$APP_PATH" \
    --install-location "/Applications" \
    --identifier "$BUNDLE_ID" \
    --version "$VERSION" \
    "dist/${UNSIGNED_PKG_NAME}"

if [ ! -f "dist/${UNSIGNED_PKG_NAME}" ]; then
    echo -e "${RED}❌ PKG 生成失败，未找到 dist/${UNSIGNED_PKG_NAME}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 未签名 PKG 创建完成: dist/${UNSIGNED_PKG_NAME}${NC}"

echo -e "\n${YELLOW}[6/8] 签名 PKG...${NC}"
if [ -n "${INSTALLER_SIGNING_IDENTITY:-}" ]; then
    echo "使用安装包签名身份: $INSTALLER_SIGNING_IDENTITY"
    productsign \
        --sign "$INSTALLER_SIGNING_IDENTITY" \
        "dist/${UNSIGNED_PKG_NAME}" \
        "dist/${PKG_NAME}"
    pkgutil --check-signature "dist/${PKG_NAME}"
    rm -f "dist/${UNSIGNED_PKG_NAME}"
    echo -e "${GREEN}✓ PKG 签名完成${NC}"
else
    mv "dist/${UNSIGNED_PKG_NAME}" "dist/${PKG_NAME}"
    pkgutil --check-signature "dist/${PKG_NAME}" || true
    echo -e "${YELLOW}⚠️  未配置 INSTALLER_SIGNING_IDENTITY，输出未签名 PKG${NC}"
fi

echo -e "\n${YELLOW}[7/8] 上传公证...${NC}"
if [ -n "${APPLE_ID:-}" ] && [ -n "$APPLE_APP_PASSWORD" ] && [ -n "${TEAM_ID:-}" ]; then
    xcrun notarytool submit "dist/${PKG_NAME}" \
        --apple-id "$APPLE_ID" \
        --password "$APPLE_APP_PASSWORD" \
        --team-id "$TEAM_ID" \
        --wait
    echo -e "${GREEN}✓ 公证成功${NC}"

    echo -e "\n${YELLOW}[8/8] 装订公证票据...${NC}"
    xcrun stapler staple "dist/${PKG_NAME}"
    xcrun stapler validate "dist/${PKG_NAME}"
    echo -e "${GREEN}✓ 装订完成${NC}"
else
    echo -e "${YELLOW}⚠️  未配置 Apple 公证参数，跳过公证和装订${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 构建完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "生成的文件:"
echo "  应用: dist/${APP_NAME}.app"
echo "  PKG:  dist/${PKG_NAME}"
echo ""
echo "安装 PKG:"
echo "  open dist/${PKG_NAME}"

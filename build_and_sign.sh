#!/bin/bash

# SuperStarTrail 打包、签名、公证和装订脚本
# 使用方法: ./build_and_sign.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
APP_NAME="SuperStarTrail"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
PYI_CONFIG_DIR="${PYINSTALLER_CONFIG_DIR:-/tmp/pyinstaller-superstartrail}"

if [ ! -x "$VENV_PYTHON" ]; then
    echo -e "${RED}❌ 未找到可用的虚拟环境 Python: $VENV_PYTHON${NC}"
    echo "请先创建虚拟环境并安装依赖。"
    exit 1
fi

VERSION="$("$VENV_PYTHON" -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('src').resolve())); from utils.settings import APP_VERSION; print(APP_VERSION)")"
BUNDLE_ID="com.jamesphotography.superstartrail"
DMG_NAME="${APP_NAME}-v${VERSION}-arm64.dmg"
APPLE_APP_PASSWORD="${APPLE_APP_PASSWORD:-${APP_SPECIFIC_PASSWORD:-}}"
if [ -z "${SIGNING_IDENTITY:-}" ]; then
    SIGNING_IDENTITY="$(security find-identity -v -p codesigning | sed -n 's/.*"\\(Developer ID Application:.*\\)"/\\1/p' | head -n 1 || true)"
fi

# 签名和公证配置（需要从环境变量或钥匙串获取）
# 你需要先设置这些环境变量：
# export APPLE_ID="your-apple-id@email.com"
# export APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
# export TEAM_ID="XXXXXXXXXX"
# export SIGNING_IDENTITY="Developer ID Application: Your Name (XXXXXXXXXX)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SuperStarTrail 打包、签名、公证流程${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. 检查必要工具
echo -e "\n${YELLOW}[1/8] 检查必要工具...${NC}"
if ! "$VENV_PYTHON" -c "import PyInstaller" &> /dev/null; then
    echo -e "${RED}❌ 当前仓库的虚拟环境里未安装 PyInstaller${NC}"
    echo "请先执行:"
    echo "  ./.venv/bin/pip install -r requirements-lock.txt -r requirements-dev.txt pyinstaller"
    exit 1
fi

if ! command -v create-dmg &> /dev/null; then
    echo -e "${RED}❌ create-dmg 未安装${NC}"
    echo "请先安装: brew install create-dmg"
    exit 1
fi

echo -e "${GREEN}✓ 所有工具已就绪${NC}"

# 2. 清理之前的构建
echo -e "\n${YELLOW}[2/8] 清理之前的构建...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ 清理完成${NC}"

# 3. 使用 PyInstaller 打包
echo -e "\n${YELLOW}[3/8] 使用 PyInstaller 打包应用...${NC}"
PYINSTALLER_CONFIG_DIR="$PYI_CONFIG_DIR" \
    "$VENV_PYTHON" -m PyInstaller SuperStarTrail.spec --clean --noconfirm

if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo -e "${RED}❌ 打包失败，未找到 ${APP_NAME}.app${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 打包完成: dist/${APP_NAME}.app${NC}"

# 4. 签名应用（如果配置了签名证书）
echo -e "\n${YELLOW}[4/8] 签名应用...${NC}"
if [ -n "${SIGNING_IDENTITY:-}" ]; then
    echo "使用签名身份: $SIGNING_IDENTITY"

    # 先逐一签名所有动态库和可执行文件，再签名 bundle 本身
    find "dist/${APP_NAME}.app/Contents" -type f \( -name "*.dylib" -o -name "*.so" -o -perm -111 \) -print0 | \
        xargs -0 -I {} codesign --force --sign "$SIGNING_IDENTITY" \
            --timestamp \
            --options runtime \
            "{}"

    # 签名主应用，不使用 --deep，避免覆盖已签名组件
    codesign --force --sign "$SIGNING_IDENTITY" \
             --options runtime \
             --timestamp \
             --entitlements entitlements.plist \
             "dist/${APP_NAME}.app"

    # 验证签名
    codesign --verify --deep --strict --verbose=2 "dist/${APP_NAME}.app"
    spctl -a -vv "dist/${APP_NAME}.app" || echo "注：未公证的应用会显示 rejected，这是正常的"

    echo -e "${GREEN}✓ 应用签名完成${NC}"
else
    echo -e "${YELLOW}⚠️  未配置签名证书，跳过签名步骤${NC}"
    echo "要启用签名，请设置环境变量 SIGNING_IDENTITY"
fi

# 5. 创建 DMG
echo -e "\n${YELLOW}[5/8] 创建 DMG 安装包...${NC}"

# 创建临时目录
TMP_DMG_DIR="tmp_dmg"
rm -rf "$TMP_DMG_DIR"
mkdir -p "$TMP_DMG_DIR"

# 复制应用到临时目录
cp -R "dist/${APP_NAME}.app" "$TMP_DMG_DIR/"

# 复制 README 到 DMG
if [ -f "DMG_README.txt" ]; then
    cp "DMG_README.txt" "$TMP_DMG_DIR/README.txt"
    echo -e "${GREEN}✓ 已添加 README.txt 到 DMG${NC}"
fi

# 创建 DMG
rm -f "dist/${DMG_NAME}"
create-dmg \
  --volname "${APP_NAME} ${VERSION}" \
  --window-pos 200 120 \
  --window-size 580 380 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 140 180 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 440 180 \
  --no-internet-enable \
  "dist/${DMG_NAME}" \
  "$TMP_DMG_DIR" \
  || {
    echo -e "${YELLOW}⚠️  create-dmg 失败，尝试使用 hdiutil...${NC}"
    ln -s /Applications "$TMP_DMG_DIR/Applications"
    hdiutil create -volname "${APP_NAME}" -srcfolder "$TMP_DMG_DIR" -ov -format UDZO "dist/${DMG_NAME}"
  }

find dist -maxdepth 1 -name "rw*.${DMG_NAME}" -delete

# 清理临时目录
rm -rf "$TMP_DMG_DIR"

echo -e "${GREEN}✓ DMG 创建完成: dist/${DMG_NAME}${NC}"

# 6. 签名 DMG（如果配置了签名证书）
echo -e "\n${YELLOW}[6/8] 签名 DMG...${NC}"
if [ -n "${SIGNING_IDENTITY:-}" ]; then
    codesign --force --sign "$SIGNING_IDENTITY" --timestamp "dist/${DMG_NAME}"
    codesign --verify --verbose=2 "dist/${DMG_NAME}"
    echo -e "${GREEN}✓ DMG 签名完成${NC}"
else
    echo -e "${YELLOW}⚠️  未配置签名证书，跳过 DMG 签名${NC}"
fi

# 7. 上传公证（如果配置了 Apple ID）
echo -e "\n${YELLOW}[7/8] 上传公证...${NC}"
if [ -n "${APPLE_ID:-}" ] && [ -n "$APPLE_APP_PASSWORD" ] && [ -n "${TEAM_ID:-}" ]; then
    echo "上传到 Apple 进行公证..."

    # 使用 notarytool 上传
    xcrun notarytool submit "dist/${DMG_NAME}" \
        --apple-id "$APPLE_ID" \
        --password "$APPLE_APP_PASSWORD" \
        --team-id "$TEAM_ID" \
        --wait

    # 检查公证状态
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ 公证成功${NC}"

        # 8. 装订公证票据
        echo -e "\n${YELLOW}[8/8] 装订公证票据...${NC}"
        xcrun stapler staple "dist/${DMG_NAME}"

        # 验证装订
        xcrun stapler validate "dist/${DMG_NAME}"

        echo -e "${GREEN}✓ 装订完成${NC}"
    else
        echo -e "${RED}❌ 公证失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  未配置 Apple ID 和密码，跳过公证和装订${NC}"
    echo "要启用公证，请设置以下环境变量："
    echo "  export APPLE_ID=\"your-apple-id@email.com\""
    echo "  export APPLE_APP_PASSWORD=\"xxxx-xxxx-xxxx-xxxx\""
    echo "  export TEAM_ID=\"XXXXXXXXXX\""
fi

# 完成
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 构建完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "生成的文件:"
echo "  应用: dist/${APP_NAME}.app"
echo "  DMG:  dist/${DMG_NAME}"
echo ""

if [ -n "${SIGNING_IDENTITY:-}" ] && [ -n "${APPLE_ID:-}" ]; then
    echo -e "${GREEN}应用已完成签名、公证和装订，可以分发！${NC}"
else
    echo -e "${YELLOW}应用未签名或未公证，仅供测试使用。${NC}"
    echo "要创建可分发的版本，请配置签名证书和 Apple ID。"
fi

echo ""
echo "测试应用:"
echo "  open dist/${APP_NAME}.app"
echo ""
echo "安装 DMG:"
echo "  open dist/${DMG_NAME}"

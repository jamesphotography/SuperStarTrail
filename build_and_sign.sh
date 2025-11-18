#!/bin/bash

# SuperStarTrail 打包、签名、公证和装订脚本
# 使用方法: ./build_and_sign.sh

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
APP_NAME="SuperStarTrail"
VERSION="0.3.0"
BUNDLE_ID="com.jamesphotography.superstartrail"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"

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
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}❌ PyInstaller 未安装${NC}"
    echo "正在安装 PyInstaller..."
    pip install pyinstaller
fi

if ! command -v create-dmg &> /dev/null; then
    echo -e "${RED}❌ create-dmg 未安装${NC}"
    echo "正在安装 create-dmg..."
    brew install create-dmg
fi

echo -e "${GREEN}✓ 所有工具已就绪${NC}"

# 2. 清理之前的构建
echo -e "\n${YELLOW}[2/8] 清理之前的构建...${NC}"
rm -rf build dist
echo -e "${GREEN}✓ 清理完成${NC}"

# 3. 使用 PyInstaller 打包
echo -e "\n${YELLOW}[3/8] 使用 PyInstaller 打包应用...${NC}"
source .venv/bin/activate
pyinstaller SuperStarTrail.spec --clean

if [ ! -d "dist/${APP_NAME}.app" ]; then
    echo -e "${RED}❌ 打包失败，未找到 ${APP_NAME}.app${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 打包完成: dist/${APP_NAME}.app${NC}"

# 4. 签名应用（如果配置了签名证书）
echo -e "\n${YELLOW}[4/8] 签名应用...${NC}"
if [ -n "$SIGNING_IDENTITY" ]; then
    echo "使用签名身份: $SIGNING_IDENTITY"

    # 深度签名（先签名所有库和框架，再签名应用）
    find "dist/${APP_NAME}.app/Contents/MacOS" -type f -name "*.dylib" -o -name "*.so" | while read file; do
        codesign --force --verify --verbose --sign "$SIGNING_IDENTITY" \
                 --options runtime \
                 --timestamp \
                 "$file" || true
    done

    # 签名主应用
    codesign --force --deep --verify --verbose --sign "$SIGNING_IDENTITY" \
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

# 创建应用程序文件夹的符号链接
ln -s /Applications "$TMP_DMG_DIR/Applications"

# 创建 DMG
rm -f "dist/${DMG_NAME}"
create-dmg \
  --volname "${APP_NAME}" \
  --volicon "dist/${APP_NAME}.app/Contents/Resources/icon.icns" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 200 190 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 600 185 \
  "dist/${DMG_NAME}" \
  "$TMP_DMG_DIR" \
  || {
    echo -e "${YELLOW}⚠️  create-dmg 失败，尝试使用 hdiutil...${NC}"
    hdiutil create -volname "${APP_NAME}" -srcfolder "$TMP_DMG_DIR" -ov -format UDZO "dist/${DMG_NAME}"
  }

# 清理临时目录
rm -rf "$TMP_DMG_DIR"

echo -e "${GREEN}✓ DMG 创建完成: dist/${DMG_NAME}${NC}"

# 6. 签名 DMG（如果配置了签名证书）
echo -e "\n${YELLOW}[6/8] 签名 DMG...${NC}"
if [ -n "$SIGNING_IDENTITY" ]; then
    codesign --force --sign "$SIGNING_IDENTITY" --timestamp "dist/${DMG_NAME}"
    codesign --verify --verbose=2 "dist/${DMG_NAME}"
    echo -e "${GREEN}✓ DMG 签名完成${NC}"
else
    echo -e "${YELLOW}⚠️  未配置签名证书，跳过 DMG 签名${NC}"
fi

# 7. 上传公证（如果配置了 Apple ID）
echo -e "\n${YELLOW}[7/8] 上传公证...${NC}"
if [ -n "$APPLE_ID" ] && [ -n "$APP_SPECIFIC_PASSWORD" ] && [ -n "$TEAM_ID" ]; then
    echo "上传到 Apple 进行公证..."

    # 使用 notarytool 上传
    xcrun notarytool submit "dist/${DMG_NAME}" \
        --apple-id "$APPLE_ID" \
        --password "$APP_SPECIFIC_PASSWORD" \
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
    echo "  export APP_SPECIFIC_PASSWORD=\"xxxx-xxxx-xxxx-xxxx\""
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

if [ -n "$SIGNING_IDENTITY" ] && [ -n "$APPLE_ID" ]; then
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

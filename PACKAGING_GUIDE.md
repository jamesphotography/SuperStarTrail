# 彗星星轨 - 打包指南

## 📦 快速打包（推荐 DMG 格式）

### 方案 1：无签名版本（测试用）

**适合**: 自己使用或分享给信任的朋友

```bash
# 运行打包脚本
./build_and_sign.sh
```

**输出文件**:
- `dist/SuperStarTrail.app` - macOS 应用
- `dist/SuperStarTrail-0.3.0.dmg` - DMG 安装包

**安装方式**:
1. 打开 DMG 文件
2. 拖拽应用到 Applications 文件夹
3. 首次运行需要右键 → 打开（绕过 Gatekeeper）

---

### 方案 2：签名 + 公证版本（公开分发）

**适合**: 公开分发给所有用户

**前置要求**:
1. Apple Developer 账号（$99/年）
2. Developer ID Application 证书
3. App-specific password

**步骤 1: 设置环境变量**

```bash
# 你的 Apple ID
export APPLE_ID="James@jamesphotography.com.au"

# App-specific password（从 appleid.apple.com 生成）
export APP_SPECIFIC_PASSWORD="iocf-bcmw-xxgc-kkvp"

# Team ID
export TEAM_ID="JWR6FDB52H"

# 签名身份
export SIGNING_IDENTITY="Developer ID Application: James Zhen Yu (JWR6FDB52H)"
```

**步骤 2: 运行打包脚本**

```bash
./build_and_sign.sh
```

**流程**:
1. ✅ 清理之前的构建
2. ✅ PyInstaller 打包应用
3. ✅ 代码签名（所有 .dylib 和 .so 文件）
4. ✅ 创建 DMG
5. ✅ 签名 DMG
6. ✅ 上传到 Apple 公证
7. ✅ 装订公证票据

**公证时间**: 通常 5-15 分钟

---

## 🎯 DMG vs PKG 选择

| 特性 | DMG ⭐⭐⭐⭐⭐ | PKG ⭐⭐⭐ |
|-----|------------|---------|
| **安装方式** | 拖拽安装 | 安装向导 |
| **卸载** | 直接删除 .app | 需要卸载脚本 |
| **用户体验** | 简单直观 | 较复杂 |
| **适合场景** | 独立应用 ✅ | 系统级安装 |
| **流行度** | 90% Mac 应用使用 | 10% 使用 |

**推荐**: 彗星星轨使用 DMG 格式 ✅

---

## 🔧 手动打包步骤（了解细节）

### 1. 清理构建

```bash
rm -rf build dist
```

### 2. 激活虚拟环境

```bash
source .venv/bin/activate
```

### 3. 使用 PyInstaller 打包

```bash
pyinstaller SuperStarTrail.spec --clean
```

### 4. 验证应用

```bash
open dist/SuperStarTrail.app
```

### 5. 创建 DMG

#### 方法 A: 使用 create-dmg（推荐）

```bash
# 安装 create-dmg
brew install create-dmg

# 创建临时目录
mkdir tmp_dmg
cp -R dist/SuperStarTrail.app tmp_dmg/
ln -s /Applications tmp_dmg/Applications

# 创建 DMG
create-dmg \
  --volname "彗星星轨" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "SuperStarTrail.app" 200 190 \
  --hide-extension "SuperStarTrail.app" \
  --app-drop-link 600 185 \
  "彗星星轨-0.4.0.dmg" \
  tmp_dmg

# 清理
rm -rf tmp_dmg
```

#### 方法 B: 使用 hdiutil（系统自带）

```bash
# 创建临时目录
mkdir tmp_dmg
cp -R dist/SuperStarTrail.app tmp_dmg/
ln -s /Applications tmp_dmg/Applications

# 创建 DMG
hdiutil create -volname "彗星星轨" \
  -srcfolder tmp_dmg \
  -ov -format UDZO \
  "彗星星轨-0.4.0.dmg"

# 清理
rm -rf tmp_dmg
```

---

## 🔐 代码签名和公证

### 检查签名状态

```bash
# 查看签名信息
codesign -dvvv dist/SuperStarTrail.app

# 验证签名
codesign --verify --deep --strict --verbose=2 dist/SuperStarTrail.app

# 检查 Gatekeeper 状态
spctl -a -vv dist/SuperStarTrail.app
```

### 签名应用

```bash
# 深度签名
codesign --force --deep --verify --verbose \
  --sign "Developer ID Application: James Zhen Yu (JWR6FDB52H)" \
  --options runtime \
  --timestamp \
  dist/SuperStarTrail.app
```

### 公证流程

```bash
# 1. 压缩应用
ditto -c -k --keepParent dist/SuperStarTrail.app SuperStarTrail.zip

# 2. 上传公证
xcrun notarytool submit SuperStarTrail.zip \
  --apple-id "James@jamesphotography.com.au" \
  --password "iocf-bcmw-xxgc-kkvp" \
  --team-id "JWR6FDB52H" \
  --wait

# 3. 装订票据
xcrun stapler staple dist/SuperStarTrail.app

# 4. 验证装订
xcrun stapler validate dist/SuperStarTrail.app
```

---

## 📊 版本历史

### v0.4.0 (当前版本)
- ✨ 应用名称改为"彗星星轨"
- ✨ 标题优化为"一键生成星轨照片与延时视频"
- ✨ 银河延时视频功能（MilkyWayTimelapse）
- ✨ 预览区域弹性布局优化
- ✨ 自动预览第一张图片
- ✨ 进度预计时间提示优化
- 🐛 修复预览区域 3:2 比例问题
- 🐛 修复传统延时视频生成问题

### v0.3.0
- 彗星尾巴优化
- 延时视频功能
- 亮度拉伸

### v0.2.1
- 彗星星轨 Production Ready

---

## 🚀 快速命令

### 开发测试

```bash
# 激活环境并运行
source .venv/bin/activate
python src/main.py
```

### 打包测试版（无签名）

```bash
./build_and_sign.sh
```

### 打包发布版（签名+公证）

```bash
# 设置环境变量
export SIGNING_IDENTITY="Developer ID Application: James Zhen Yu (JWR6FDB52H)"
export APPLE_ID="James@jamesphotography.com.au"
export APP_SPECIFIC_PASSWORD="iocf-bcmw-xxgc-kkvp"
export TEAM_ID="JWR6FDB52H"

# 运行打包
./build_and_sign.sh
```

### 测试 DMG

```bash
open dist/SuperStarTrail-0.3.0.dmg
```

---

## ❓ 常见问题

### Q1: "无法打开，因为来自身份不明的开发者"

**A**: 右键点击应用 → 选择"打开" → 确认打开

### Q2: PyInstaller 找不到模块

**A**: 检查 `SuperStarTrail.spec` 中的 `hiddenimports` 列表

### Q3: DMG 创建失败

**A**: 使用备用方案 `hdiutil create`

### Q4: 公证失败

**A**: 检查环境变量是否正确设置，确认 App-specific password 有效

### Q5: 应用图标不显示

**A**: 确认 `logo.icns` 文件存在且格式正确

---

## 📝 打包检查清单

完成打包前的检查：

- [ ] 代码已提交到 Git
- [ ] 版本号已更新（spec 文件和脚本）
- [ ] Logo 图标已准备（logo.icns）
- [ ] 测试了所有主要功能
- [ ] 虚拟环境依赖已安装完整
- [ ] 签名证书有效（如需签名）
- [ ] Apple ID 密码已准备（如需公证）

---

## 🎯 推荐工作流程

### 日常开发

```bash
source .venv/bin/activate
python src/main.py
```

### 测试构建

```bash
./build_and_sign.sh
open dist/SuperStarTrail.app
```

### 发布版本

```bash
# 1. 更新版本号
# 编辑 SuperStarTrail.spec 和 build_and_sign.sh

# 2. 设置环境变量
export SIGNING_IDENTITY="..."
export APPLE_ID="..."
export APP_SPECIFIC_PASSWORD="..."
export TEAM_ID="..."

# 3. 打包
./build_and_sign.sh

# 4. 测试 DMG
open dist/彗星星轨-0.4.0.dmg

# 5. 分发
# 上传到网站或分享给用户
```

---

## 📦 输出文件说明

### dist/SuperStarTrail.app
- **类型**: macOS 应用包
- **用途**: 可以直接运行或拖拽到 Applications
- **大小**: 约 200-300 MB

### dist/SuperStarTrail-0.4.0.dmg
- **类型**: 磁盘映像
- **用途**: 分发给用户的安装包
- **大小**: 约 150-250 MB（压缩后）
- **特点**:
  - 双击打开
  - 拖拽安装
  - 专业外观

---

## 💡 提示

1. **首次打包**: 可能需要安装 `create-dmg`
   ```bash
   brew install create-dmg
   ```

2. **虚拟环境**: 确保在虚拟环境中打包
   ```bash
   source .venv/bin/activate
   ```

3. **图标**: 确认 `logo.icns` 存在且正确

4. **测试**: 打包后务必测试应用功能

5. **公证**: 公开分发建议进行公证，避免 Gatekeeper 警告

---

祝打包顺利！🚀

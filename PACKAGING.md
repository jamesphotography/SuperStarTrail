# SuperStarTrail 打包、签名、公证指南

## 快速开始

### 基本打包（无签名）

直接运行打包脚本：

```bash
./build_and_sign.sh
```

这将创建：
- `dist/SuperStarTrail.app` - macOS 应用程序
- `dist/SuperStarTrail-0.3.0.dmg` - DMG 安装包

### 完整打包（签名+公证）

要创建可分发的已签名和公证版本，需要 Apple Developer 账号。

## 前置要求

### 1. Apple Developer 账号

- 注册 Apple Developer Program ($99/年)
- 获取 Developer ID 证书

### 2. 创建 App-Specific Password

1. 访问 https://appleid.apple.com
2. 登录你的 Apple ID
3. 在"登录和安全"部分，点击"App-Specific Password"
4. 点击"生成密码"
5. 输入描述（如"SuperStarTrail Notarization"）
6. 保存生成的密码

### 3. 找到你的 Team ID

```bash
xcrun notarytool history --apple-id your-apple-id@email.com --password xxxx-xxxx-xxxx-xxxx
```

输出中会显示你的 Team ID。

## 签名和公证流程

### 步骤 1: 设置环境变量

```bash
# Apple ID（用于公证）
export APPLE_ID="your-apple-id@email.com"

# App-Specific Password（上面创建的）
export APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"

# Team ID（你的开发者团队 ID）
export TEAM_ID="XXXXXXXXXX"

# 签名身份（证书）
export SIGNING_IDENTITY="Developer ID Application: Your Name (XXXXXXXXXX)"
```

### 步骤 2: 查找签名证书

```bash
# 列出所有可用的签名证书
security find-identity -v -p codesigning

# 输出示例：
# 1) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX "Developer ID Application: Your Name (XXXXXXXXXX)"
```

使用引号中的完整字符串作为 `SIGNING_IDENTITY`。

### 步骤 3: 运行完整打包流程

```bash
./build_and_sign.sh
```

脚本会自动：
1. 使用 PyInstaller 打包应用
2. 深度签名所有库和应用
3. 创建 DMG
4. 签名 DMG
5. 上传到 Apple 进行公证（需要几分钟）
6. 装订公证票据到 DMG

### 步骤 4: 验证

```bash
# 验证应用签名
codesign --verify --deep --strict --verbose=2 dist/SuperStarTrail.app

# 验证公证状态
spctl -a -vv dist/SuperStarTrail.app

# 验证 DMG 装订
xcrun stapler validate dist/SuperStarTrail-0.3.0.dmg
```

## 文件说明

### 配置文件

- `SuperStarTrail.spec` - PyInstaller 打包配置
- `entitlements.plist` - macOS 应用权限配置
- `build_and_sign.sh` - 自动化打包脚本

### 生成的文件

- `build/` - PyInstaller 构建缓存
- `dist/SuperStarTrail.app` - 打包的应用（326MB）
- `dist/SuperStarTrail-0.3.0.dmg` - 安装包（136MB）

## 常见问题

### Q: 公证失败怎么办？

A: 检查公证状态：

```bash
xcrun notarytool log <submission-id> \
    --apple-id "$APPLE_ID" \
    --password "$APP_SPECIFIC_PASSWORD" \
    --team-id "$TEAM_ID"
```

常见问题：
- 未签名的库：使用 `--deep` 签名
- 缺少 hardened runtime：在 entitlements.plist 中添加权限
- 代码签名过期：更新证书

### Q: 应用太大了怎么优化？

A: 在 `SuperStarTrail.spec` 中：

1. 排除不需要的包：
```python
excludes=[
    'torch',
    'transformers',
    'matplotlib',
    'pandas',
    # 添加更多不需要的包
],
```

2. 使用 UPX 压缩：
```python
upx=True,
upx_exclude=[],
```

### Q: 如何创建通用二进制（Intel + Apple Silicon）？

A: PyInstaller 当前版本只支持创建单架构二进制。要创建通用二进制：

1. 在 Intel Mac 上打包一次
2. 在 Apple Silicon Mac 上打包一次
3. 使用 `lipo` 合并：

```bash
lipo -create \
    SuperStarTrail-arm64.app/Contents/MacOS/SuperStarTrail \
    SuperStarTrail-x86_64.app/Contents/MacOS/SuperStarTrail \
    -output SuperStarTrail-universal.app/Contents/MacOS/SuperStarTrail
```

## 测试

### 本地测试

```bash
# 直接运行应用
open dist/SuperStarTrail.app

# 挂载 DMG 测试
open dist/SuperStarTrail-0.3.0.dmg
```

### 模拟首次下载

```bash
# 添加隔离属性（模拟从网络下载）
xattr -w com.apple.quarantine "0081;$(date +%s);Safari" dist/SuperStarTrail-0.3.0.dmg

# 打开 DMG
open dist/SuperStarTrail-0.3.0.dmg
```

如果公证成功，macOS 会直接允许打开。如果未公证，会显示警告。

## 持续集成

可以在 GitHub Actions 中自动化打包：

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
          brew install create-dmg

      - name: Build
        env:
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APP_SPECIFIC_PASSWORD: ${{ secrets.APP_SPECIFIC_PASSWORD }}
          TEAM_ID: ${{ secrets.TEAM_ID }}
          SIGNING_IDENTITY: ${{ secrets.SIGNING_IDENTITY }}
        run: ./build_and_sign.sh

      - name: Upload Release
        uses: actions/upload-artifact@v2
        with:
          name: SuperStarTrail-macOS
          path: dist/SuperStarTrail-0.3.0.dmg
```

## 参考资料

- [PyInstaller 文档](https://pyinstaller.readthedocs.io/)
- [Apple Code Signing 指南](https://developer.apple.com/support/code-signing/)
- [Notarization 指南](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [create-dmg 文档](https://github.com/create-dmg/create-dmg)

## 支持

如有问题，请在 GitHub 提交 Issue：
https://github.com/jamesphotography/SuperStarTrail/issues

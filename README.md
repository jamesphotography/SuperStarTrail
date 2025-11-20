# 彗星星轨 (SuperStarTrail)

**一键生成星轨照片与延时视频**

![Version](https://img.shields.io/badge/version-0.5.0-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 项目简介

彗星星轨是一款功能强大的星轨照片合成与延时视频生成软件，专为天文摄影爱好者和专业摄影师设计。它提供原生 RAW 格式支持，让你能够在合成星轨的同时保持最高的图像质量。

### ✨ 核心特性

#### 星轨合成
- **原生 RAW 支持**: 支持所有主流相机的 RAW 格式（NEF, CR2, ARW, RAF, DNG 等）
- **多种堆栈模式**:
  - Lighten（最大值）- 标准星轨模式
  - Comet（彗星模式）- 创建渐变尾迹效果，可调节尾巴长度
  - Average（平均值）- 降噪模式
  - Darken（最小值）- 去除光污染
- **实时预览**: 在合成过程中实时查看结果，带亮度自动拉伸
- **专业调控**: RAW 参数调整（白平衡：相机、日光、自动）
- **间隔填充**: 自动填充照片间隔，创造更平滑的星轨

#### 延时视频
- **星轨延时** ⭐（默认开启）: 展示星轨形成过程，从第一张到最后一张的变化
- **银河延时** ⭐（默认开启）: 直接将原始照片合成延时视频，展示银河移动和天空运动
- **4K 分辨率**: 输出 3840×2160 高清视频
- **可调帧率**: 默认 25 FPS，100张照片约生成 4秒视频
- **智能命名**: 自动生成包含参数信息的文件名

#### 用户体验
- **现代化界面**: PyQt5 打造的美观界面，支持中文
- **智能文件管理**: 支持文件排除、预览、一键打开输出目录
- **进度提示**: 实时显示处理进度和预计剩余时间
- **日志输出**: 完整的操作日志，方便排查问题

### 📸 功能演示

1. **选择照片** → 2. **配置参数** → 3. **一键合成** → 4. **获得结果**

输出文件：
- 星轨照片（TIFF/JPEG）
- 星轨延时视频（MP4）
- 银河延时视频（MP4）

## 🚀 快速开始

### macOS 安装（推荐）

1. 下载 `SuperStarTrail-0.5.0.dmg`
2. 双击打开 DMG 文件
3. 拖拽应用到 Applications 文件夹
4. 首次运行：右键 → 打开（绕过 Gatekeeper）

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/yourusername/SuperStarTrail.git
cd SuperStarTrail

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行程序
python src/main.py
```

## 📖 使用指南

### 基础工作流程

1. **选择照片目录**
   - 点击"选择目录"按钮
   - 选择包含 RAW 文件的文件夹
   - 支持的格式：NEF, CR2, ARW, DNG, ORF, RW2, RAF, CRW, CR3

2. **配置参数**
   - 堆栈模式：Lighten（星轨）或 Comet（彗星效果）
   - 白平衡：相机 / 日光 / 自动
   - 彗星尾巴：短 / 中 / 长（仅彗星模式）

3. **选择功能**（默认全部开启）
   - ✅ 星轨延时：展示星轨形成过程
   - ✅ 银河延时：展示天空运动
   - 间隔填充：可选，填充照片间隔

4. **开始处理**
   - 点击"开始合成"
   - 实时预览合成结果
   - 查看处理日志

5. **获取结果**
   - 默认保存到源文件夹的 `SuperStarTrail` 子目录
   - 点击"打开输出目录"快速查看

### 输出文件命名规则

#### 星轨照片
```
StarTrail_开始-结束_白平衡_堆栈模式_日期时间.tif
示例: StarTrail_DSC0001-DSC0100_CameraWB_Lighten_20250119.tif
```

#### 星轨延时视频
```
StarTrailTimelapse_开始-结束_白平衡_帧率.mp4
示例: StarTrailTimelapse_DSC0001-DSC0100_CameraWB_25FPS.mp4
```

#### 银河延时视频
```
MilkyWayTimelapse_开始-结束_白平衡_帧率.mp4
示例: MilkyWayTimelapse_DSC0001-DSC0100_CameraWB_25FPS.mp4
```

## 🛠️ 技术栈

- **GUI**: PyQt5 - 跨平台界面框架
- **RAW 处理**: rawpy (LibRaw) - 专业 RAW 图像解码
- **图像计算**: numpy + numba - 高性能数值计算
- **图像处理**:
  - Pillow - 图像 I/O 和基础操作
  - OpenCV (cv2) - 视频编码
  - tifffile - TIFF 格式支持
- **视频处理**: imageio + imageio-ffmpeg - 视频编码
- **科学计算**: scipy - 图像插值和滤波

## 📦 打包与分发

### macOS DMG 打包

```bash
# 运行打包脚本
./build_and_sign.sh

# 输出文件
dist/SuperStarTrail.app
dist/SuperStarTrail-0.5.0.dmg
```

详见 [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md)

## 🔧 已知问题与解决方案

### cv2 递归加载问题

PyInstaller 打包时 OpenCV 会触发递归检测。已通过以下方式修复：

1. **补丁脚本** (`patch_cv2.py`): 禁用 cv2 的递归检测
2. **运行时修复** (`hook-cv2.py`): PyInstaller runtime hook
3. **main.py 修复**: 启动时清理 `sys.OpenCV_LOADER`

使用前运行：
```bash
python patch_cv2.py  # 补丁虚拟环境中的 cv2
```

## 📝 更新日志

### v0.5.0 (2025-01-19)

#### 新增功能
- ✨ 完成后自动打开输出目录
- 📄 默认预览背景图（银河星空）
- 📋 日志区域显示快速开始指南
- ✨ 开始按钮图标改为星星（✨ 开始合成）

#### 改进
- 🎨 优化用户体验流程
- 🎨 提升首次使用的引导性
- 📦 DMG 安装包包含 README 文件

### v0.4.0 (2025-01-19)

#### 新增功能
- ✨ 应用名称改为"彗星星轨"
- ✨ 标题优化为"一键生成星轨照片与延时视频"
- ✨ 银河延时视频功能（MilkyWayTimelapse）
- ✨ 星轨延时和银河延时默认开启
- ✨ 预览区域弹性布局优化
- ✨ 自动预览第一张图片
- ✨ 进度预计时间提示优化（显示后期处理）
- ✨ Logo 显示在标题中间

#### 改进
- 🎨 "星迹延时"更名为"星轨延时"
- 🎨 预览区域 3:2 比例，可随窗口放大
- 🎨 日志区域固定高度 120px
- 🐛 修复预览区域比例问题
- 🐛 修复 cv2 递归加载问题
- 🐛 修复 PyInstaller 打包依赖问题

### v0.3.0

- 彗星尾巴优化
- 延时视频功能
- 亮度拉伸

### v0.2.1

- 彗星星轨 Production Ready

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [StarStaX](https://markus-enzweiler.de/software/starstax/) - 灵感来源
- [LibRaw](https://www.libraw.org/) - RAW 图像处理库
- [PyInstaller](https://pyinstaller.org/) - Python 打包工具

## 📧 联系方式

- 作者: James Photography
- Email: James@jamesphotography.com.au
- 项目主页: https://github.com/yourusername/SuperStarTrail

---

**开发语言**: Python 3.12+
**平台支持**: macOS (已测试), Windows, Linux
**状态**: ✅ 生产就绪

Made with ❤️ for astrophotography enthusiasts

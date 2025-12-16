# 彗星星轨 (SuperStarTrail)

**一键生成星轨照片与延时视频**

![Version](https://img.shields.io/badge/version-0.5.1-blue)
![Python](https://img.shields.io/badge/python-3.12+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 项目简介

彗星星轨是一款功能强大的星轨照片合成与延时视频生成软件，专为天文摄影爱好者和专业摄影师设计。它不仅支持原生 RAW 格式，现在还支持 JPEG 格式，让你能够在合成星轨的同时保持最高的图像质量。

🎬 **视频教程**: [YouTube 完整教程](https://www.youtube.com/watch?v=torSH5w1wH4)

### ✨ 核心特性

#### 星轨合成
- **全格式支持**: 支持 RAW (NEF, CR2, ARW 等) 和 JPEG 格式
- **智能文件识别**: 自动检测同名的 RAW+JPG 文件，让用户灵活选择
- **多种堆栈模式**:
  - Lighten（最大值）- 标准星轨模式
  - Comet（彗星模式）- 创建渐变尾迹效果，可调节尾巴长度
  - Average（平均值）- 降噪模式
  - Darken（最小值）- 去除光污染
- **实时预览**: 在合成过程中实时查看结果，带亮度自动拉伸
- **间隔填充**: 自动填充照片间隔，创造更平滑的星轨

#### 延时视频
- **双模式延时**: 同时生成"星轨形成延时"和"银河运动延时"
- **4K 高画质**: 输出 3840×2160 高清 MP4 视频
- **智能命名**: 自动生成包含拍摄参数的文件名

#### 用户体验
- **现代化界面**: 美观的深色模式界面，完全支持中文
- **日志记录**: 自动保存详细的操作日志，方便回溯
- **MacOS 优化**: 经过 Apple 公证，安装运行无障碍

## 🚀 下载与安装

### macOS 用户 (推荐)

1. 在 [Releases](https://github.com/jamesphotography/SuperStarTrail/releases) 页面下载 `SuperStarTrail-0.5.1.dmg`
2. 双击打开 DMG 文件
3. 将图标拖入 Applications 文件夹即可
4. **无需额外设置**: 软件已通过 Apple 签名和公证，可直接打开运行

### Windows 用户

1. 下载 Windows 版本安装包 (如有)
2. 直接运行安装程序

## 📖 使用指南

1. **选择照片**: 点击"选择目录"，选择包含照片的文件夹。如果有 RAW+JPG，软件会询问使用哪种格式。
2. **配置参数**: 设置堆栈模式（推荐 Comet）和彗星尾巴长度。
3. **开始处理**: 点击"开始合成"，软件将自动处理照片并预览。
4. **获取结果**: 完成后，点击"打开输出目录"查看生成的照片和视频。

### 输出文件示例
- **星轨图**: `StarTrail_DSC0001-DSC0100_Comet_20251216.tif`
- **星轨延时**: `StarTrailTimelapse_..._.mp4`
- **银河延时**: `MilkyWayTimelapse_..._.mp4`
- **运行日志**: `SuperStarTrail_20251216_103000.log`

## 📝 更新日志

### v0.5.1 (2025-12-16)
- ✨ **JPEG 格式支持**: 全面支持 .jpg/.jpeg 格式，支持 RAW+JPG 智能筛选
- 🪟 **Windows 修复**: 彻底解决了 Windows 中文路径下延时视频 0 字节的问题
- 📝 **日志系统**: 新增自动保存日志文件功能
- 🔒 **安全增强**: macOS 版本已完成签名和公证

### v0.5.0
- ✨ 完成后自动打开输出目录
- ✨ 新增默认预览背景图
- 🎨 UI 交互体验优化

## 📧 联系与支持

- 作者: James Photography
- Email: James@jamesphotography.com.au
- 项目主页: [GitHub](https://github.com/jamesphotography/SuperStarTrail)

---
Made with ❤️ for astrophotography enthusiasts

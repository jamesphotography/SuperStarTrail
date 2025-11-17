# SuperStarTrail

专业级星轨照片合成工具 - 原生支持 RAW 格式

![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## 项目简介

SuperStarTrail 是一款功能强大的星轨照片合成软件，专为天文摄影爱好者和专业摄影师设计。它提供原生 RAW 格式支持，让你能够在合成星轨的同时保持最高的图像质量。

### 核心特性

- **原生 RAW 支持**: 支持所有主流相机的 RAW 格式（NEF, CR2, ARW, RAF 等）
- **多种堆栈模式**: Lighten（星轨）、Average（降噪）、Darken、Comet（彗星效果）等
- **实时预览**: 在合成过程中实时查看结果
- **专业调控**: RAW 参数调整（白平衡、曝光、对比度等）
- **高性能**: 多核 CPU 优化，高效处理大量图像
- **跨平台**: 支持 macOS、Windows 和 Linux

### 与 StarStaX 对比

| 特性 | SuperStarTrail | StarStaX |
|------|----------------|----------|
| RAW 格式支持 | ✅ 原生支持 | ❌ 不支持 |
| RAW 参数调整 | ✅ 支持 | ❌ 不支持 |
| 堆栈模式 | 6+ 种模式 | 6 种模式 |
| 实时预览 | ✅ 支持 | ✅ 支持 |
| 开源 | ✅ MIT License | ❌ 闭源 |

## 快速开始

### 环境要求

- Python 3.9 或更高版本
- 8GB RAM（推荐 16GB）
- 支持的操作系统：macOS 10.15+、Windows 10+、Linux

### 安装

#### 方式 1: 使用虚拟环境（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/SuperStarTrail.git
cd SuperStarTrail

# 创建虚拟环境
python3 -m venv .venv

# 激活虚拟环境
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 方式 2: 下载可执行文件（即将推出）

直接下载适用于你操作系统的可执行文件，无需安装 Python。

### 运行程序

```bash
# 确保虚拟环境已激活
python src/main.py
```

## 使用方法

### 基础工作流程

1. **选择文件**: 点击"选择目录"按钮，选择包含星轨照片的文件夹
2. **配置参数**:
   - 选择堆栈模式（Lighten 用于星轨）
   - 调整 RAW 参数（白平衡、曝光等）
3. **开始合成**: 点击"开始合成"按钮
4. **实时预览**: 在预览窗口中查看合成进度
5. **保存结果**: 合成完成后，选择输出格式并保存

### 堆栈模式说明

- **Lighten（最大值）**: 标准星轨模式，取每个像素的最大值
- **Average（平均值）**: 降噪模式，适合长曝光
- **Darken（最小值）**: 去除光污染
- **Comet（彗星模式）**: 创建渐变尾迹效果
- **Addition（叠加）**: 累积曝光效果

### RAW 参数调整

- **白平衡**: 日光、阴天、自定义色温（2000-10000K）
- **曝光补偿**: -3 到 +3 EV
- **对比度**: 调整图像对比度
- **饱和度**: 调整色彩饱和度

## 开发状态

当前版本：**0.1.0-alpha**

### 已完成功能 ✅

- [x] 项目架构设计
- [x] 基础项目结构
- [x] 依赖管理

### 开发中功能 🚧

- [ ] RAW 文件读取和解码
- [ ] 基础 GUI 界面
- [ ] Lighten 堆栈模式
- [ ] 实时预览

### 计划中功能 📋

- [ ] 彗星模式
- [ ] 暗帧减除
- [ ] 图像自动对齐
- [ ] 批量处理
- [ ] GPU 加速

详细开发计划请查看 [PROJECT_SPEC.md](PROJECT_SPEC.md)

## 项目结构

```
SuperStarTrail/
├── src/                    # 源代码
│   ├── core/              # 核心处理模块
│   ├── ui/                # 用户界面
│   ├── utils/             # 工具函数
│   └── resources/         # 资源文件
├── tests/                 # 测试代码
├── docs/                  # 文档
└── scripts/               # 构建脚本
```

## 开发指南

### 设置开发环境

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black src/

# 代码检查
pylint src/
```

### 贡献指南

我们欢迎所有形式的贡献！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

详细的开发规范请查看 [PROJECT_SPEC.md](PROJECT_SPEC.md#7-开发规范)

## 技术栈

- **GUI**: PyQt5
- **RAW 处理**: rawpy (LibRaw)
- **图像计算**: numpy + numba
- **图像处理**: Pillow
- **测试**: pytest

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 致谢

- [StarStaX](https://markus-enzweiler.de/software/starstax/) - 灵感来源
- [LibRaw](https://www.libraw.org/) - RAW 图像处理库
- 所有贡献者和测试者

## 联系方式

- 项目主页: https://github.com/yourusername/SuperStarTrail
- 问题反馈: https://github.com/yourusername/SuperStarTrail/issues
- 讨论区: https://github.com/yourusername/SuperStarTrail/discussions

## 更新日志

### v0.1.0-alpha (2025-10-12)

- 项目初始化
- 完成项目架构设计
- 创建基础项目结构
- 编写开发文档

---

**注意**: 本项目目前处于早期开发阶段，功能尚不完整。欢迎测试和反馈！

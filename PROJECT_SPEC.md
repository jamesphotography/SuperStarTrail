# SuperStarTrail - 项目开发文档

## 1. 项目概述

### 1.1 项目名称
**SuperStarTrail** - 专业级星轨合成工具

### 1.2 项目愿景
创建一个功能强大、易于使用的星轨照片合成软件，超越现有的 StarStaX，提供原生 RAW 格式支持和更多专业功能。

### 1.3 核心目标
- 支持所有主流相机的 RAW 格式文件（NEF, CR2, ARW, RAF 等）
- 提供实时预览和多种堆栈合成模式
- 实现彗星效果、间隙填充等特色功能
- 提供直观的图形用户界面
- 跨平台支持（macOS, Windows, Linux）
- 高性能处理（多核 CPU 优化）

### 1.4 目标用户
- 天文摄影爱好者
- 专业摄影师
- 延时摄影创作者
- 光绘艺术家

---

## 2. 技术架构

### 2.1 技术栈选型

#### 核心技术
```
编程语言: Python 3.9+
GUI 框架: PyQt5 / PySide6
RAW 处理: rawpy (LibRaw)
图像计算: numpy + numba (JIT 加速)
图像处理: Pillow + OpenCV
输出格式: imageio, tifffile
```

#### 可选优化
```
GPU 加速: CuPy (CUDA)
图像对齐: OpenCV (SIFT/ORB)
并行计算: multiprocessing
```

### 2.2 系统架构

```
┌─────────────────────────────────────────┐
│          GUI Layer (PyQt5)              │
│  ┌──────────┬──────────┬──────────┐    │
│  │ 文件选择 │  参数面板 │  预览区  │    │
│  └──────────┴──────────┴──────────┘    │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│      Business Logic Layer               │
│  ┌──────────────────────────────────┐  │
│  │   StarTrailProcessor (核心引擎)  │  │
│  │   - 图像堆栈算法                  │  │
│  │   - RAW 解码控制                  │  │
│  │   - 预览生成                      │  │
│  └──────────────────────────────────┘  │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│       Data Layer                        │
│  ┌─────────┬─────────┬──────────┐      │
│  │RAW Reader│Stacker  │ Exporter │      │
│  │(rawpy)  │(numpy)  │(imageio) │      │
│  └─────────┴─────────┴──────────┘      │
└─────────────────────────────────────────┘
```

### 2.3 核心模块

#### A. RAW 处理模块 (`raw_processor.py`)
- RAW 文件读取和解码
- 白平衡、曝光调整
- 颜色空间转换
- 元数据提取

#### B. 堆栈引擎模块 (`stacking_engine.py`)
- 最大值堆栈（Lighten）
- 最小值堆栈（Darken）
- 平均值堆栈（Average）
- 彗星模式（Comet）
- 间隙填充（Gap Filling）
- 累积模式（Cumulative）

#### C. 图像处理模块 (`image_processor.py`)
- 图像对齐（防抖）
- 热像素去除
- 暗帧减除
- 直方图均衡化

#### D. GUI 模块 (`ui/`)
- 主窗口（MainWindow）
- 文件浏览器（FileExplorer）
- 参数面板（ParameterPanel）
- 预览窗口（PreviewWidget）
- 进度指示器（ProgressDialog）

#### E. 导出模块 (`exporter.py`)
- TIFF (8/16/32-bit)
- JPEG
- PNG
- 批量导出

---

## 3. 功能需求

### 3.1 核心功能（MVP - 最小可行产品）

#### 优先级 P0（必须有）
- [x] 目录选择和 RAW 文件扫描
- [x] RAW 文件读取和基本解码
- [x] Lighten 模式堆栈（最大值）
- [x] 实时预览（缩略图）
- [x] 进度条显示
- [x] 保存为 TIFF/JPEG
- [x] 基础 GUI 界面

### 3.2 高级功能（Version 1.0）

#### 优先级 P1（重要）
- [ ] 多种堆栈模式切换
  - Lighten（星轨）
  - Average（降噪）
  - Darken（去光污染）
  - Addition（叠加曝光）
- [ ] 彗星模式（渐变尾迹效果）
- [ ] 暗帧减除
- [ ] RAW 参数调整
  - 白平衡（日光/阴天/自定义色温）
  - 曝光补偿（-3 到 +3 EV）
  - 对比度/饱和度
- [ ] 批量处理队列
- [ ] 快捷键支持

#### 优先级 P2（期望有）
- [ ] 间隙填充算法
- [ ] 累积模式（保存每一步）
- [ ] 图像自动对齐
- [ ] 热像素检测和去除
- [ ] 实时直方图
- [ ] 缩放和平移预览
- [ ] 导出视频（延时）

### 3.3 专业功能（Version 2.0）

#### 优先级 P3（锦上添花）
- [ ] 智能去除飞机/卫星轨迹
- [ ] HDR 星轨（32-bit 浮点）
- [ ] 多图层导出（PSD）
- [ ] GPU 加速（CUDA）
- [ ] 插件系统
- [ ] 批处理脚本
- [ ] 云存储集成

---

## 4. 开发路线图

### Phase 1: 基础框架（预计 1 周）

**目标**: 搭建项目骨架，实现基础 RAW 读取和简单 GUI

#### Week 1 - Day 1-2: 项目初始化
- [x] 创建项目结构
- [ ] 配置开发环境
- [ ] 编写 `requirements.txt`
- [ ] 创建 Git 仓库
- [ ] 编写基础文档

#### Week 1 - Day 3-4: RAW 处理核心
- [ ] 实现 `RawProcessor` 类
- [ ] 测试读取各种 RAW 格式
- [ ] 实现基础参数调整（白平衡、曝光）
- [ ] 单元测试

#### Week 1 - Day 5-7: 基础 GUI
- [ ] 创建主窗口布局
- [ ] 实现文件选择对话框
- [ ] 显示文件列表
- [ ] 简单的预览窗口

**交付物**:
- 能够选择目录并显示 RAW 文件列表
- 能够读取并预览单张 RAW 照片

---

### Phase 2: 核心堆栈功能（预计 1-2 周）

**目标**: 实现完整的星轨合成核心算法

#### Week 2 - Day 1-3: 堆栈引擎
- [ ] 实现 `StackingEngine` 类
- [ ] Lighten 模式（最大值）
- [ ] Average 模式（平均值）
- [ ] 内存优化（逐张处理）
- [ ] 性能测试

#### Week 2 - Day 4-5: 实时预览
- [ ] 后台线程处理
- [ ] 定期更新预览
- [ ] 进度条集成
- [ ] 取消操作支持

#### Week 2 - Day 6-7: 导出功能
- [ ] 实现 `Exporter` 类
- [ ] TIFF 16-bit 导出
- [ ] JPEG 导出
- [ ] 文件命名和路径选择

**交付物**:
- MVP 版本，能够合成星轨并保存结果
- 处理 100 张 RAW 文件的完整流程

---

### Phase 3: 增强功能（预计 2 周）

**目标**: 添加彗星模式、暗帧减除等高级功能

#### Week 3-4: 高级堆栈模式
- [ ] Comet 模式实现
- [ ] Darken 模式
- [ ] Addition 模式
- [ ] 暗帧减除算法
- [ ] 参数调节 UI

#### Week 3-4: UI/UX 优化
- [ ] 参数面板美化
- [ ] 快捷键绑定
- [ ] 拖拽文件支持
- [ ] 错误处理和提示
- [ ] 多语言支持（中英文）

**交付物**:
- Version 1.0 Beta
- 功能完整，可供测试

---

### Phase 4: 专业功能（预计 2-3 周）

**目标**: 实现图像对齐、智能处理等专业功能

#### Week 5-6: 图像对齐
- [ ] OpenCV 特征检测
- [ ] 图像配准算法
- [ ] 用户界面集成

#### Week 6-7: 智能处理
- [ ] 热像素检测
- [ ] 飞机轨迹去除
- [ ] 间隙填充算法
- [ ] HDR 合成

**交付物**:
- Version 1.0 Release Candidate

---

### Phase 5: 优化与发布（预计 1 周）

**目标**: 性能优化、测试、打包发布

#### Week 8: 最终优化
- [ ] 性能剖析和优化
- [ ] 多核并行处理
- [ ] 内存使用优化
- [ ] 全面测试（单元测试、集成测试）
- [ ] 用户手册编写
- [ ] 打包为可执行文件（PyInstaller）

**交付物**:
- Version 1.0 正式版
- macOS / Windows / Linux 安装包

---

## 5. 项目结构

```
SuperStarTrail/
├── README.md                  # 项目说明
├── PROJECT_SPEC.md            # 本文档
├── requirements.txt           # 依赖列表
├── setup.py                   # 安装配置
├── LICENSE                    # 许可证
│
├── src/                       # 源代码
│   ├── __init__.py
│   ├── main.py               # 应用入口
│   │
│   ├── core/                 # 核心逻辑
│   │   ├── __init__.py
│   │   ├── raw_processor.py      # RAW 处理
│   │   ├── stacking_engine.py    # 堆栈引擎
│   │   ├── image_processor.py    # 图像处理
│   │   └── exporter.py           # 导出模块
│   │
│   ├── ui/                   # 用户界面
│   │   ├── __init__.py
│   │   ├── main_window.py        # 主窗口
│   │   ├── file_explorer.py      # 文件浏览器
│   │   ├── parameter_panel.py    # 参数面板
│   │   ├── preview_widget.py     # 预览窗口
│   │   └── progress_dialog.py    # 进度对话框
│   │
│   ├── utils/                # 工具函数
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   ├── logger.py             # 日志
│   │   └── validators.py         # 验证函数
│   │
│   └── resources/            # 资源文件
│       ├── icons/                # 图标
│       ├── styles/               # 样式表
│       └── translations/         # 翻译文件
│
├── tests/                    # 测试代码
│   ├── __init__.py
│   ├── test_raw_processor.py
│   ├── test_stacking_engine.py
│   └── test_data/                # 测试数据
│
├── docs/                     # 文档
│   ├── user_manual.md           # 用户手册
│   ├── developer_guide.md       # 开发指南
│   └── api_reference.md         # API 文档
│
└── scripts/                  # 构建脚本
    ├── build_mac.sh
    ├── build_windows.bat
    └── package.py
```

---

## 6. 技术实现细节

### 6.1 核心算法

#### Lighten 模式（最大值堆栈）
```python
def stack_lighten(images):
    """星轨合成 - 取每个像素的最大值"""
    result = images[0].copy().astype(np.float32)
    for img in images[1:]:
        result = np.maximum(result, img)
    return result
```

#### Comet 模式（彗星效果）
```python
def stack_comet(images, fade_factor=0.98):
    """彗星效果 - 每张图逐渐衰减"""
    result = images[0].copy().astype(np.float32)
    for img in images[1:]:
        result = result * fade_factor + img * (1 - fade_factor)
    return result
```

#### Gap Filling（间隙填充）
```python
def gap_filling(images, gap_size=5):
    """填充星轨间的间隙"""
    # 使用形态学膨胀操作
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (gap_size, gap_size))
    result = cv2.dilate(stacked_image, kernel)
    return result
```

### 6.2 性能优化策略

#### 内存管理
```python
# 方案1: 逐张处理，只保留中间结果
result = None
for i, path in enumerate(image_paths):
    img = load_image(path)
    if result is None:
        result = img
    else:
        result = np.maximum(result, img)
    del img  # 立即释放内存

# 方案2: 使用 memory-mapped files
import numpy as np
result = np.memmap('temp_result.dat', dtype='float32',
                   mode='w+', shape=(height, width, 3))
```

#### 多核加速
```python
from multiprocessing import Pool

def process_batch(image_batch):
    """处理一批图像"""
    return np.maximum.reduce(image_batch)

# 分批并行处理
with Pool(cpu_count()) as pool:
    batch_results = pool.map(process_batch, image_batches)
    final_result = np.maximum.reduce(batch_results)
```

#### JIT 加速（Numba）
```python
from numba import jit

@jit(nopython=True)
def fast_lighten(img1, img2):
    """JIT 编译的最大值运算"""
    return np.maximum(img1, img2)
```

### 6.3 RAW 参数控制

```python
import rawpy

class RawProcessor:
    def __init__(self):
        self.params = {
            'use_camera_wb': True,
            'output_bps': 16,
            'output_color': rawpy.ColorSpace.sRGB,
            'gamma': (1, 1),  # 线性
            'no_auto_bright': True,
            'exp_shift': 1.0,  # 曝光补偿
        }

    def process(self, raw_path, **kwargs):
        """处理 RAW 文件"""
        params = {**self.params, **kwargs}
        with rawpy.imread(raw_path) as raw:
            rgb = raw.postprocess(**params)
        return rgb

    def set_white_balance(self, temp=6500, tint=0):
        """设置色温"""
        # 自定义白平衡实现
        pass
```

---

## 7. 开发规范

### 7.1 代码风格
- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 使用 pylint/flake8 进行代码检查
- 类型提示（Type Hints）

### 7.2 命名规范
```python
# 类名：大驼峰
class StackingEngine:
    pass

# 函数/变量：小写下划线
def process_raw_image():
    image_path = "/path/to/file"

# 常量：大写下划线
MAX_IMAGE_SIZE = 8192
DEFAULT_GAMMA = (1, 1)
```

### 7.3 文档规范
```python
def stack_images(images: List[np.ndarray], mode: str = 'lighten') -> np.ndarray:
    """
    堆栈多张图像

    Args:
        images: 图像数组列表
        mode: 堆栈模式 ('lighten', 'average', 'darken')

    Returns:
        堆栈后的图像数组

    Raises:
        ValueError: 当 mode 不支持时
    """
    pass
```

### 7.4 Git 工作流
- `main` 分支：稳定版本
- `develop` 分支：开发版本
- `feature/*` 分支：新功能
- `bugfix/*` 分支：Bug 修复

提交信息格式：
```
<type>(<scope>): <subject>

[optional body]

<type>: feat, fix, docs, style, refactor, test, chore
```

示例：
```
feat(stacking): 添加彗星模式支持

- 实现 comet_mode 算法
- 添加 fade_factor 参数控制
- 更新 UI 添加彗星模式选项
```

---

## 8. 测试策略

### 8.1 单元测试
```python
# tests/test_stacking_engine.py
import unittest
import numpy as np
from src.core.stacking_engine import StackingEngine

class TestStackingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = StackingEngine()
        self.test_images = [
            np.random.randint(0, 65535, (100, 100, 3), dtype=np.uint16)
            for _ in range(10)
        ]

    def test_lighten_mode(self):
        result = self.engine.stack(self.test_images, mode='lighten')
        # 验证结果的每个像素都是最大值
        expected = np.maximum.reduce(self.test_images)
        np.testing.assert_array_equal(result, expected)
```

### 8.2 集成测试
- 测试完整的 RAW 文件处理流程
- 测试 GUI 交互
- 测试文件导出

### 8.3 性能测试
```python
import time

def benchmark_stacking(num_images=100):
    images = generate_test_images(num_images)

    start = time.time()
    result = stack_images(images)
    duration = time.time() - start

    print(f"处理 {num_images} 张图像耗时: {duration:.2f} 秒")
    print(f"平均每张: {duration/num_images*1000:.2f} 毫秒")
```

---

## 9. 依赖管理

### 9.1 核心依赖
```
# requirements.txt
PyQt5>=5.15.0
rawpy>=0.18.0
numpy>=1.21.0
Pillow>=9.0.0
imageio>=2.15.0
tifffile>=2022.0.0
numba>=0.55.0
```

### 9.2 可选依赖
```
# requirements-dev.txt
opencv-python>=4.5.0    # 图像对齐
cupy-cuda11x>=10.0.0    # GPU 加速
pytest>=7.0.0           # 测试
black>=22.0.0           # 代码格式化
pylint>=2.12.0          # 代码检查
PyInstaller>=5.0.0      # 打包
```

---

## 10. 发布计划

### 10.1 版本规划

#### v0.1.0 - Alpha（Week 2）
- 基础 RAW 读取
- Lighten 模式
- 简单预览

#### v0.5.0 - Beta（Week 4）
- 多种堆栈模式
- 完整 UI
- 导出功能

#### v1.0.0 - Release（Week 8）
- 所有核心功能
- 性能优化
- 完整测试
- 用户文档

#### v1.5.0 - Enhanced（Week 12）
- 图像对齐
- 智能处理
- 批量操作

#### v2.0.0 - Professional（Week 16）
- GPU 加速
- 插件系统
- 高级导出

### 10.2 打包发布

#### macOS
```bash
pyinstaller --windowed --onefile \
    --icon=resources/icons/app.icns \
    --name=SuperStarTrail \
    src/main.py
```

#### Windows
```bash
pyinstaller --windowed --onefile \
    --icon=resources/icons/app.ico \
    --name=SuperStarTrail.exe \
    src/main.py
```

---

## 11. 风险评估

### 11.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| RAW 格式兼容性问题 | 高 | 中 | 广泛测试，使用 LibRaw 最新版本 |
| 内存占用过高 | 高 | 高 | 实现流式处理，优化算法 |
| 处理速度慢 | 中 | 中 | 多核优化，考虑 GPU 加速 |
| GUI 跨平台问题 | 中 | 低 | 使用成熟的 PyQt5 |

### 11.2 开发风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| 开发时间超期 | 中 | 中 | 采用敏捷开发，MVP 优先 |
| 需求变更 | 低 | 低 | 模块化设计，保持灵活性 |
| 依赖库更新 | 低 | 低 | 固定版本号，定期更新 |

---

## 12. 成功指标

### 12.1 功能指标
- [ ] 支持至少 10 种主流相机 RAW 格式
- [ ] 处理 100 张 24MP RAW 文件 < 5 分钟
- [ ] 内存占用 < 4GB
- [ ] GUI 响应时间 < 100ms

### 12.2 质量指标
- [ ] 代码测试覆盖率 > 80%
- [ ] 无严重 Bug
- [ ] 用户满意度 > 4.5/5

### 12.3 发布指标
- [ ] 完整的用户文档
- [ ] macOS / Windows / Linux 可执行文件
- [ ] GitHub Star > 100（6个月内）

---

## 13. 参考资源

### 13.1 技术文档
- [rawpy Documentation](https://letmaik.github.io/rawpy/)
- [PyQt5 Tutorial](https://doc.qt.io/qtforpython/)
- [NumPy User Guide](https://numpy.org/doc/stable/)

### 13.2 竞品分析
- [StarStaX](https://markus-enzweiler.de/software/starstax/)
- [Sequator](https://sites.google.com/site/sequatorglobal/)
- [StarTrails](http://www.startrails.de/)

### 13.3 算法参考
- Image Stacking Algorithms
- Astrophotography Processing Techniques
- HDR Imaging

---

## 14. 更新日志

### 2025-10-12
- 创建项目开发文档
- 定义技术栈和架构
- 制定开发路线图

---

**文档维护**: 本文档随项目进展持续更新
**负责人**: James Zhenyu
**最后更新**: 2025-10-12

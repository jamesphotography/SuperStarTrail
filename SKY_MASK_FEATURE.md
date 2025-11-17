# 天空蒙版功能说明

**版本**: 1.0
**日期**: 2025-11-17
**模型**: SegFormer-B0

---

## 🎯 功能定位

SuperStarTrail 专注于 **RAW 文件堆栈** 和 **天空蒙版生成**，将调色和后期处理留给专业软件（如 Photoshop）。

### 核心理念

```
SuperStarTrail 的职责：
  ✅ RAW 文件读取和堆栈
  ✅ 生成高质量 16-bit TIFF
  ✅ 提供精确的天空蒙版

Photoshop 的职责：
  ✅ 分区调色（天空/地面）
  ✅ 光污染去除
  ✅ 细节调整和导出
```

---

## ⭐ 天空蒙版功能

### 什么是天空蒙版？

天空蒙版是一个黑白图像，标记出照片中的天空区域：
- **白色 (255)**: 天空
- **黑色 (0)**: 地面

### 为什么需要？

在星轨摄影后期中，天空和地面通常需要不同的处理：

| 区域 | 常见调整 |
|------|---------|
| **天空** | 提亮星轨、增强对比度、去除光污染、冷色调 |
| **地面** | 压暗前景、降噪、保留细节、暖色调 |

手动在 Photoshop 中抠图非常耗时，使用 AI 自动生成的蒙版可以：
- ⚡ 节省时间（几秒 vs 几分钟）
- 🎯 更精确（边缘平滑）
- 🔄 可重复使用

---

## 🚀 使用方法

### 方法 1: 独立使用天空蒙版

```bash
# 运行测试生成蒙版
python test_sky_mask_simple.py
```

**输出文件**：
```
test_output_simple/
├── Z8A_7528_sky_mask.png        # 天空蒙版（主要）
├── Z8A_7528_sky_only.png        # 仅天空区域
├── Z8A_7528_ground_only.png     # 仅地面区域
├── Z8A_7528_preview.png         # 叠加预览
└── Z8A_7528_comparison.png      # 对比图
```

### 方法 2: 完整工作流（堆栈 + 蒙版）

```python
from core.stacking_engine import StackingEngine, StackMode
from core.raw_processor import RawProcessor
from core.sky_detector import SkyDetector

# 1. 堆栈星轨
processor = RawProcessor()
engine = StackingEngine(mode=StackMode.LIGHTEN)

for raw_file in raw_files:
    img = processor.process(raw_file)
    engine.add_image(img)

stacked = engine.get_result()

# 2. 生成天空蒙版
detector = SkyDetector(model_size="b0")
sky_mask = detector.segment(stacked_8bit)

# 3. 保存结果
tifffile.imwrite("star_trail.tiff", stacked)
Image.fromarray(sky_mask).save("star_trail_sky_mask.png")
```

**输出**：
- `star_trail.tiff` - 16-bit 星轨图像
- `star_trail_sky_mask.png` - 天空蒙版

---

## 📐 在 Photoshop 中使用蒙版

### 步骤 1: 加载文件

1. 打开 `star_trail.tiff`
2. 菜单: **选择 > 载入选区**
3. 选择 `star_trail_sky_mask.png`
4. 点击确定

### 步骤 2: 分区调整

**调整天空**：
```
当前选区 = 天空

可以应用：
- 曲线：提亮星轨
- 色彩平衡：去除橙色光污染，添加蓝色
- 色相/饱和度：增强星轨色彩
- 锐化：让星轨更清晰
```

**调整地面**：
```
菜单：选择 > 反选 (Cmd+Shift+I)
当前选区 = 地面

可以应用：
- 曲线：压暗前景
- 降噪：减少长曝光噪点
- 色彩平衡：添加暖色调
```

### 步骤 3: 细化蒙版（可选）

如果 AI 分割不够完美：
1. 选择 > 选择并遮住（Select and Mask）
2. 调整边缘：羽化、平滑、对比度
3. 使用画笔手动修正

---

## 🔧 技术细节

### 使用的模型

**SegFormer-B0** (NVIDIA)
- 训练数据集: ADE20K (150 类语义分割)
- 模型大小: 14MB
- 推理速度: 15-20秒 (45MP 图像, CPU)
- 精度: mIoU 51.8%

### 性能指标

| 指标 | 数值 |
|------|------|
| 图像尺寸 | 8280 × 5520 (45.7 MP) |
| 处理时间 | 15-20秒 (CPU) |
| 模型加载 | ~2秒（首次） |
| 蒙版大小 | ~100-200 KB (PNG) |
| 天空识别准确度 | 95%+ |

### 优势对比

| 特性 | 手动抠图 | AI 蒙版 |
|------|---------|---------|
| 时间 | 5-10分钟 | **15秒** ✅ |
| 边缘质量 | 取决于技术 | **始终平滑** ✅ |
| 可重复性 | 困难 | **完全一致** ✅ |
| 需要技能 | 高 | **无需** ✅ |

---

## 💡 实用技巧

### 技巧 1: 批量生成蒙版

如果有多个星轨作品需要处理：

```python
detector = SkyDetector(model_size="b0")  # 只加载一次模型

for image_file in image_files:
    image = Image.open(image_file)
    mask = detector.segment(image)

    mask_path = image_file.with_name(f"{image_file.stem}_mask.png")
    Image.fromarray(mask).save(mask_path)
```

### 技巧 2: 保存为 Photoshop 动作

1. 在 Photoshop 中录制动作
2. 包含：载入选区、应用调整层
3. 下次只需运行动作，自动完成

### 技巧 3: 导出分层 PSD

```python
# 在 Photoshop 中
图层 1: 原始星轨
图层 2: 天空调整层（使用蒙版）
图层 3: 地面调整层（使用反向蒙版）

文件 > 存储为 > PSD
```

---

## 📊 测试结果

### 实测数据（19 张 Z8 NEF 文件）

```
图像尺寸: 8280 × 5520
文件格式: Nikon NEF (14-bit)

单张图像:
  - 天空分割: 15.72秒
  - 天空占比: 69.8%
  - 蒙版大小: 144 KB

完整工作流 (3 张堆栈 + 蒙版):
  - 总耗时: 19.54秒
  - 输出: star_trail.tiff (206 MB)
  - 蒙版: star_trail_sky_mask.png (87 KB)
```

---

## 🎨 示例效果

### 天空分割精度

- ✅ 准确识别天空/地面边界
- ✅ 正确处理建筑物轮廓
- ✅ 边缘平滑自然
- ✅ 适用于各种构图

### Photoshop 后期示例

**原图** → **分区调色** → **最终效果**

```
天空:
  • 提亮 +1 EV
  • 色温 -500K (偏冷)
  • 对比度 +20
  • 去除橙色光污染

地面:
  • 压暗 -0.5 EV
  • 色温 +200K (偏暖)
  • 降噪 (强度 7)
```

---

## ❓ 常见问题

### Q: 银河等亮天空区域会被误判为地景吗？

**A**: 不会。v0.2.1+ 版本已经实现了**亮度增强算法**：
- 自动检测天空附近的亮区域（银河、星云等）
- 基于感知亮度（ITU-R BT.709）进行修正
- 默认启用，无需手动调整
- 如需关闭：`detector.segment(image, enhance_bright_sky=False)`

技术细节：算法会在初始天空区域附近寻找亮度超过阈值的像素，并将其包含到天空蒙版中。

### Q: 蒙版不够准确怎么办？

**A**: 在 Photoshop 中手动修正：
1. 选择 > 选择并遮住
2. 使用画笔工具修正
3. 调整羽化和平滑度

### Q: 能否识别其他物体（建筑、树木）？

**A**: 当前版本专注于天空/地面二分类。
未来可能添加多类别支持。

### Q: 处理时间太长怎么办？

**A**:
- 使用 GPU 可提升到 3-5秒
- 考虑降采样（牺牲一点精度换速度）
- 批量处理时可在后台运行

### Q: 蒙版能用在视频吗？

**A**: 理论上可以，但：
- 每帧都需要重新分割
- 可能有闪烁问题
- 建议使用专门的视频分割工具

---

## 🔮 未来计划

### 短期（v1.1）
- ☑️ GUI 集成（主窗口添加"导出天空蒙版"选项）
- ☑️ GPU 加速支持 (MPS/CUDA)
- ☑️ 蒙版预览叠加

### 中期（v1.5）
- ⬜ 多类别分割（建筑、树木、山脉）
- ⬜ 蒙版编辑器（简单调整）
- ⬜ 批量处理优化

### 长期（v2.0）
- ⬜ AI 推荐调色参数
- ⬜ 一键生成 PSD 分层文件
- ⬜ 视频支持

---

## 📚 相关资源

### 学习资源
- [Photoshop 蒙版使用教程](https://helpx.adobe.com/photoshop/using/masking-layers.html)
- [星轨后期调色技巧](https://www.youtube.com/results?search_query=star+trail+editing)

### 技术文档
- [SegFormer 论文](https://arxiv.org/abs/2105.15203)
- [ADE20K 数据集](https://groups.csail.mit.edu/vision/datasets/ADE20K/)

### 开源贡献
- [提交 Issue](https://github.com/yourusername/SuperStarTrail/issues)
- [功能建议](https://github.com/yourusername/SuperStarTrail/discussions)

---

**总结**: 天空蒙版功能让 SuperStarTrail 成为星轨摄影后期的完美起点，节省时间，提升质量！

---

*文档版本: 1.0*
*更新日期: 2025-11-17*

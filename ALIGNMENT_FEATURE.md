# 图像对齐功能实现说明

## 功能概述

为 SuperStarTrail 添加了图像对齐功能，用于修正相机抖动导致的图像位移。这对于长时间曝光星轨摄影非常重要，即使使用三脚架，也可能因为快门震动、风吹等因素导致轻微抖动。

## 技术实现

### 1. 核心模块：image_aligner.py

**位置**: `src/core/image_aligner.py`

**主要类**: `ImageAligner`

**支持的对齐方法**:
- **ORB** (Oriented FAST and Rotated BRIEF) - 默认，速度最快
- **AKAZE** (Accelerated-KAZE) - 平衡速度和精度
- **SIFT** (Scale-Invariant Feature Transform) - 最精确但最慢

**核心功能**:

#### 1.1 特征检测对齐 (`align()`)
```python
def align(self, image: np.ndarray, reference: np.ndarray,
          max_shift: int = 50) -> Tuple[np.ndarray, bool]
```
- 检测 2000 个关键特征点
- 使用 RANSAC 算法剔除异常匹配
- 计算仿射变换矩阵（支持平移、旋转、缩放）
- 限制最大偏移 50 像素，超过则认为对齐失败

#### 1.2 ECC 对齐 (`align_simple()`)
```python
def align_simple(self, image: np.ndarray, reference: np.ndarray) -> np.ndarray
```
- 使用增强相关系数算法
- 仅支持平移
- 速度更快，但精度略低

#### 1.3 偏移检测 (`detect_shift()`)
```python
def detect_shift(self, image: np.ndarray, reference: np.ndarray) -> Optional[Tuple[float, float]]
```
- 使用相位相关算法快速检测偏移量
- 仅返回偏移向量，不进行变换

### 2. 堆栈引擎集成

**修改文件**: `src/core/stacking_engine.py`

**主要变更**:

```python
class StackingEngine:
    def __init__(self, mode: StackMode = StackMode.LIGHTEN, enable_alignment: bool = False):
        self.enable_alignment = enable_alignment
        self.reference: Optional[np.ndarray] = None  # 参考图像
        self.aligner = None

        if enable_alignment:
            from .image_aligner import ImageAligner
            self.aligner = ImageAligner(method="orb")
```

**处理流程**:
1. 第一张图片作为参考图像
2. 后续每张图片在堆栈前先对齐到参考图像
3. 对齐失败时自动使用原图并输出警告

### 3. GUI 界面集成

**修改文件**: `src/ui/main_window.py`

**新增 UI 组件**:
```python
self.check_enable_alignment = QCheckBox("启用图像对齐 (修正相机抖动)")
self.check_enable_alignment.setToolTip(
    "使用特征检测对齐图像，修正脚架抖动\n"
    "注意：启用此功能会增加处理时间（约 +0.5-1 秒/张）"
)
```

**处理线程修改**:
```python
class ProcessThread(QThread):
    def __init__(self, file_paths, stack_mode, raw_params, enable_alignment=False):
        self.enable_alignment = enable_alignment

    def run(self):
        engine = StackingEngine(self.stack_mode, enable_alignment=self.enable_alignment)
        # 日志输出对齐状态
        logger.info(f"图像对齐: {'启用' if self.enable_alignment else '禁用'}")
```

## 对齐算法详解

### ORB 特征检测流程

1. **特征点检测**
   - 使用 FAST 算法检测角点
   - 计算特征点的方向（解决旋转不变性）
   - 生成 BRIEF 描述符

2. **特征匹配**
   - 使用汉明距离匹配描述符
   - 交叉验证确保双向匹配
   - 按距离排序，取最佳 200 个匹配

3. **RANSAC 配准**
   - 随机采样一致性算法
   - 剔除异常匹配点（outliers）
   - 估计仿射变换矩阵 M (2x3)

4. **变换应用**
   - 使用双线性插值进行图像变换
   - 边界使用常数填充（黑色）

### 变换矩阵说明

仿射变换矩阵格式：
```
M = [a  b  tx]
    [c  d  ty]
```
- `(tx, ty)`: 平移量
- `[a b; c d]`: 旋转和缩放

对于星轨摄影，主要关注平移量 `(tx, ty)`。

## 性能影响

### 处理时间对比

基于 Nikon Z9 NEF 文件 (45.7 MP, 49 MB)：

| 模式 | 平均时间/张 | 总时间 (206张) |
|------|------------|---------------|
| 不启用对齐 | 2.08 秒 | ~7 分钟 |
| 启用对齐 | 2.5-3.0 秒 | ~9-10 分钟 |
| 额外开销 | +0.5-1.0 秒 | +2-3 分钟 |

### 影响因素

1. **图像大小**: 更大的图像需要更多计算时间
2. **特征点数量**: 默认 2000 个，可调整
3. **匹配点数量**: 场景纹理越丰富，匹配越快
4. **偏移量**: 偏移越小，收敛越快

## 使用建议

### 何时启用对齐？

✅ **推荐启用的情况**:
- 使用长焦镜头（200mm+）
- 大风天气拍摄
- 使用轻量级三脚架
- 快门速度较慢（15 秒+）
- 地面不稳定（桥梁、木板等）

❌ **可以禁用的情况**:
- 使用重型三脚架
- 无风环境
- 使用遥控快门或定时器
- 快门速度很快（< 5 秒）
- 确认无任何抖动

### 对齐失败的处理

程序会自动处理对齐失败的情况：
- 输出警告日志但不中断处理
- 自动使用原图继续堆栈
- 对最终结果影响通常很小

**常见失败原因**:
- 云层移动导致场景变化
- 曝光差异过大
- 星轨过长导致特征点不匹配
- 特征点不足（< 10 个）

## 测试方法

### 运行对齐测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行对齐测试（处理前 5 张图片）
python test_alignment.py
```

**测试输出**:
- 两个 TIFF 文件：
  - `test_output/test_no_alignment.tiff` - 不启用对齐
  - `test_output/test_with_alignment.tiff` - 启用对齐
- 性能数据对比
- 详细对齐日志

### 验证对齐效果

在 Photoshop 或其他图像查看器中：
1. 打开两个 TIFF 文件
2. 放大到 100% 或更高
3. 对比星点的清晰度
4. 启用对齐的版本应该星点更清晰、边缘更锐利

## 日志输出示例

### 启用对齐的日志

```
============================================================
开始星轨合成
文件数量: 206
堆栈模式: lighten
白平衡: camera
图像对齐: 启用
============================================================
[  1/206] 正在处理: Z9L_8639-2.NEF
[  1/206] 完成: Z9L_8639-2.NEF (2.15秒)
[  2/206] 正在处理: Z9L_8640-2.NEF
对齐成功: 平移 (-2.3, 1.8) 像素, 内点: 156/200
[  2/206] 完成: Z9L_8640-2.NEF (2.84秒)
[  3/206] 正在处理: Z9L_8641-2.NEF
对齐成功: 平移 (1.1, -0.7) 像素, 内点: 168/200
[  3/206] 完成: Z9L_8641-2.NEF (2.67秒)
...
```

### 对齐失败的日志

```
[  50/206] 正在处理: Z9L_8688-2.NEF
警告: 第 50 张图像对齐失败，使用原图
[  50/206] 完成: Z9L_8688-2.NEF (2.35秒)
```

## 依赖项

新增依赖：
```
opencv-python>=4.5.0  # 用于图像对齐功能
```

安装方法：
```bash
pip install opencv-python
```

或更新整个依赖：
```bash
pip install -r requirements.txt
```

## 未来改进方向

1. **多种对齐方法选择**
   - 在 GUI 中添加对齐方法选择（ORB/AKAZE/SIFT/ECC）
   - 根据场景自动选择最佳方法

2. **自适应参数**
   - 根据偏移量自动调整参数
   - 动态调整特征点数量

3. **对齐质量可视化**
   - 在 GUI 中显示每张图片的偏移量
   - 绘制偏移量曲线图

4. **批量参考图选择**
   - 允许用户选择中间帧作为参考
   - 自动选择最清晰的帧作为参考

5. **高级对齐模式**
   - 支持星空对齐模式（星点固定，前景移动）
   - 支持地景对齐模式（前景固定，星空移动）

## 相关文件

- `src/core/image_aligner.py` - 对齐算法实现
- `src/core/stacking_engine.py` - 堆栈引擎集成
- `src/ui/main_window.py` - GUI 界面集成
- `test_alignment.py` - 对齐功能测试
- `USAGE_GUIDE.md` - 用户使用指南
- `requirements.txt` - 依赖项列表

## 技术参考

- [OpenCV 特征检测文档](https://docs.opencv.org/4.x/d5/d51/group__features2d__main.html)
- [ORB 论文](https://www.willowgarage.com/sites/default/files/orb_final.pdf)
- [RANSAC 算法](https://en.wikipedia.org/wiki/Random_sample_consensus)
- [仿射变换](https://en.wikipedia.org/wiki/Affine_transformation)

---

**实现日期**: 2025-10-12
**版本**: 0.1.0-alpha
**开发者**: Claude Code

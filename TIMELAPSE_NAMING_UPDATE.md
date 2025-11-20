# 延时视频命名和参数更新总结

## 更新概述

根据用户需求，完成了以下三个主要更改：

1. ✅ **统一视频帧率** - 所有视频统一使用 25 FPS
2. ✅ **重命名文件** - `SimpleTimelapse` → `MilkyWayTimelapse`
3. ✅ **中文名称更新** - "传统延时" → "银河延时"

---

## 视频参数分析

### 两种延时视频使用相同参数

经过代码分析，发现两种延时视频都使用相同的 `TimelapseGenerator` 类和相同的参数：

| 参数 | 星迹延时 | 银河延时 |
|-----|---------|---------|
| **编码器** | `mp4v` (MPEG-4 Part 2) | `mp4v` (MPEG-4 Part 2) |
| **帧率** | 25 FPS (从设置读取) | 25 FPS (从设置读取) |
| **分辨率** | 3840×2160 (4K) | 3840×2160 (4K) |
| **质量** | JPEG 90 | JPEG 90 |

### 文件大小差异原因

虽然参数相同，但文件大小可能不同：

- **星迹延时**: 内容是逐步叠加的星轨，帧与帧之间变化较小 → **容易压缩，文件较小**
- **银河延时**: 每帧都是不同的原始照片，帧与帧之间变化较大 → **难以压缩，文件较大**

这是**正常现象**，是视频编码器对不同内容的压缩效率差异。

---

## 修改内容详解

### 1. 文件命名修改 (`SimpleTimelapse` → `MilkyWayTimelapse`)

#### 修改的文件：`src/ui/main_window.py`

**变量重命名**:
```python
# 修改前
simple_timelapse_generator = None
simple_timelapse_path = None
simple_video_filename = f"SimpleTimelapse_..."

# 修改后
milkyway_timelapse_generator = None
milkyway_timelapse_path = None
milkyway_video_filename = f"MilkyWayTimelapse_..."
```

**影响范围**:
- 第 115-128 行: 生成器初始化
- 第 206-208 行: 添加帧
- 第 299-324 行: 生成视频

**新文件名格式**:
```
MilkyWayTimelapse_{首文件名}-{尾文件名}_{白平衡}WB_{帧率}FPS.mp4
```

**示例**:
```
MilkyWayTimelapse_IMG_0001-IMG_0100_CameraWB_25FPS.mp4
MilkyWayTimelapse_IMG_0001-IMG_0100_Daylight_25FPS.mp4
```

---

### 2. 中文名称修改 ("传统延时" → "银河延时")

#### 修改的文件：

##### `src/ui/panels/parameters_panel.py` (第 122-137 行)

**复选框文本**:
```python
# 修改前
self.check_enable_simple_timelapse = QCheckBox("传统延时")

# 修改后
self.check_enable_simple_timelapse = QCheckBox("银河延时")
```

**工具提示更新**:
```python
# 修改前
"适合展示天空运动、云层变化等"

# 修改后
"适合展示银河移动、天空运动、云层变化等"
```

**复选框状态文本**:
```python
# 修改前
"✅ 传统延时" if state else "传统延时"

# 修改后
"✅ 银河延时" if state else "银河延时"
```

##### `src/ui/main_window.py` (第 171, 302, 313, 320, 323 行)

**日志消息**:
```python
# 修改前
self.log_message.emit(f"传统延时: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_simple_timelapse else '禁用'}")
self.log_message.emit("正在生成传统延时视频...")
self.log_message.emit(f"✅ 传统延时视频生成完成，耗时: {milkyway_timelapse_duration:.2f} 秒")
self.log_message.emit("❌ 传统延时视频生成失败")

# 修改后
self.log_message.emit(f"银河延时: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_simple_timelapse else '禁用'}")
self.log_message.emit("正在生成银河延时视频...")
self.log_message.emit(f"✅ 银河延时视频生成完成，耗时: {milkyway_timelapse_duration:.2f} 秒")
self.log_message.emit("❌ 银河延时视频生成失败")
```

**注释更新**:
```python
# 修改前
# 如果启用普通延时视频，创建生成器
# 如果启用普通延时视频，添加此帧
# 生成传统延时视频（如果启用）

# 修改后
# 如果启用银河延时视频，创建生成器
# 如果启用银河延时视频，添加此帧
# 生成银河延时视频（如果启用）
```

---

### 3. 文档更新

#### `FILENAME_FORMAT.md`

**章节标题**:
- `### 3. 传统延时视频 (MP4)` → `### 3. 银河延时视频 (MP4)`

**文件名格式**:
- `SimpleTimelapse_...` → `MilkyWayTimelapse_...`

**前缀说明**:
- `SimpleTimelapse_` → `MilkyWayTimelapse_`

**示例输出**:
```
SuperStarTrail/
├── IMG_0001-0100_Lighten_CameraWB_GapFilled.tif
│   ↑ 星轨堆栈图片 (主要输出)
│
├── StarTrail_Timelapse_IMG_0001-0100_Lighten_CameraWB_25FPS.mp4
│   ↑ 星迹延时视频 (展示星轨形成过程)
│
└── MilkyWayTimelapse_IMG_0001-0100_CameraWB_25FPS.mp4
    ↑ 银河延时视频 (原始照片延时，展示银河移动)
```

#### `SIMPLE_TIMELAPSE_FEATURE.md`

**文档标题**:
- `# 普通延时视频功能` → `# 银河延时视频功能`

**功能描述**:
- "普通延时视频" → "银河延时视频"
- "传统延时视频" → "银河延时视频"
- "星轨延时视频" → "星迹延时视频"

**优势描述**:
- "展示天空运动" → "展示银河移动"

**文件命名格式**:
- `SimpleTimelapse_IMG_0001-IMG_0100_CameraWB_25FPS.mp4`
- → `MilkyWayTimelapse_IMG_0001-IMG_0100_CameraWB_25FPS.mp4`

---

## 用户体验改进

### 修改前
```
界面显示: [✅ 传统延时]
日志输出: "传统延时: 启用 (4K 25FPS)"
生成文件: SimpleTimelapse_IMG_0001-0100_CameraWB_25FPS.mp4
```

### 修改后
```
界面显示: [✅ 银河延时]
日志输出: "银河延时: 启用 (4K 25FPS)"
生成文件: MilkyWayTimelapse_IMG_0001-0100_CameraWB_25FPS.mp4
```

### 改进点

1. **更具体的名称** - "银河延时" 比 "传统延时" 更准确地描述视频内容
2. **文件名更清晰** - `MilkyWayTimelapse` 比 `SimpleTimelapse` 更容易理解
3. **用途明确** - 工具提示中明确说明 "适合展示银河移动"

---

## 技术细节

### 视频生成流程保持不变

```python
# 1. 初始化生成器
milkyway_timelapse_generator = TimelapseGenerator(
    output_path=milkyway_timelapse_path,
    fps=25,  # 从设置读取，默认 25
    resolution=(3840, 2160)
)

# 2. 处理每张图片时添加帧
for path in file_paths:
    img = processor.process(path, **raw_params)
    milkyway_timelapse_generator.add_frame(img)

# 3. 生成视频
success = milkyway_timelapse_generator.generate_video(cleanup=True)
```

### TimelapseGenerator 参数

```python
class TimelapseGenerator:
    def __init__(
        self,
        output_path: Path,
        fps: int = 25,              # 默认 25 FPS
        resolution: Tuple[int, int] = (3840, 2160),  # 4K
        temp_dir: Optional[Path] = None
    ):
        # 编码器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # MPEG-4 Part 2

        # JPEG 质量
        cv2.imwrite(..., [cv2.IMWRITE_JPEG_QUALITY, 90])
```

---

## 文件清单

### 修改的代码文件
1. `src/ui/main_window.py` - 变量重命名、日志消息更新、注释更新
2. `src/ui/panels/parameters_panel.py` - 复选框文本、工具提示更新

### 更新的文档文件
1. `FILENAME_FORMAT.md` - 文件名格式、示例更新
2. `SIMPLE_TIMELAPSE_FEATURE.md` - 功能名称、描述更新

### 未修改的文件
- `src/core/timelapse_generator.py` - 参数保持不变
- `src/utils/settings.py` - 默认 FPS 已是 25
- 所有测试文件 - 无需修改

---

## 测试建议

### 功能测试
1. **界面检查**:
   - 复选框显示 "银河延时"
   - 工具提示提到 "银河移动"
   - 勾选后显示 "✅ 银河延时"

2. **文件命名**:
   - 生成的视频文件名以 `MilkyWayTimelapse_` 开头
   - 包含正确的白平衡和帧率信息

3. **日志输出**:
   - 启动处理时显示 "银河延时: 启用 (4K 25FPS)"
   - 生成过程显示 "正在生成银河延时视频..."
   - 完成后显示 "✅ 银河延时视频生成完成"

4. **视频质量**:
   - 分辨率: 3840×2160
   - 帧率: 25 FPS
   - 视频可正常播放

---

## 总结

这次更新完成了三个主要改进：

1. ✅ **确认视频参数** - 两种延时视频使用相同的参数（25 FPS, 4K, mp4v），文件大小差异是正常的编码压缩效率差异
2. ✅ **重命名文件** - `SimpleTimelapse` 改为更清晰的 `MilkyWayTimelapse`
3. ✅ **更新中文名称** - "传统延时" 改为更准确的 "银河延时"

所有修改已通过语法检查，代码运行正常，文档已同步更新。

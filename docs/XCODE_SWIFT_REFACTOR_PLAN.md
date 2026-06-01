# SuperStarTrail Xcode / Swift 重构蓝图

## 1. 目标

将当前基于 Python + PyQt5 的 macOS 桌面应用，迁移为基于 Xcode 的原生 macOS 应用，核心目标如下：

- 提升 macOS 原生体验、签名、公证、打包和后续维护效率
- 保留现有产品核心能力：RAW/JPEG/TIFF 读取、星轨堆栈、预览、导出、延时视频
- 以稳定性优先，避免一次性大爆炸重写造成算法回归
- 将当前 Python 版本保留为迁移期“参考实现”和结果真值基线

本方案明确不建议一次性全部迁完。建议采用“先建立 Swift 新架构，再逐步替换核心链路”的方式。

## 2. 当前系统概览

当前项目可粗分为四层：

### 2.1 UI 层

- `src/main.py`
- `src/ui/main_window.py`
- `src/ui/panels/file_list_panel.py`
- `src/ui/panels/parameters_panel.py`
- `src/ui/panels/control_panel.py`
- `src/ui/panels/preview_panel.py`

职责：

- 主窗口和三栏式桌面 UI
- 文件选择、参数设置、进度控制
- 预览显示、日志显示
- 处理线程与 UI 状态同步

### 2.2 图像处理核心层

- `src/core/raw_processor.py`
- `src/core/stacking_engine.py`
- `src/core/exporter.py`
- `src/core/timelapse_generator.py`
- `src/core/gap_filler.py`
- `src/core/satellite_filter.py`

职责：

- 读取 RAW/TIFF/JPEG/PNG
- 三种堆栈算法：`lighten` / `average` / `comet`
- 16-bit 图像处理与导出
- MP4 延时视频生成
- 间隔填充和划痕去除等增强能力

### 2.3 配置与基础设施层

- `src/utils/settings.py`
- `src/utils/file_naming.py`
- `src/utils/logger.py`
- `src/i18n/*`

职责：

- 用户设置和最近目录
- 文件命名
- 日志
- 语言切换

### 2.4 测试层

- `tests/test_stacking_engine.py`
- `tests/test_raw_processor_unit.py`
- `tests/test_exporter.py`
- `tests/test_timelapse_generator.py`
- 其余 UI/设置类测试

职责：

- 验证核心行为
- 作为 Swift 重构期间的参考真值

## 3. 迁移原则

### 3.1 不做 Big Bang Rewrite

不建议：

- 先全部删掉 Python 再开始写 Swift
- 先重做 UI，再回头补算法
- 第一版就追求所有边缘功能 100% 对齐

建议：

- Python 版本继续作为可运行参考
- Swift 版本先做主线能力
- 每迁完一个核心模块，就和 Python 输出做一致性对比

### 3.2 优先迁移主线价值

第一优先级：

- 文件扫描
- RAW/JPEG/TIFF 输入
- 旋转
- 预览
- `Lighten / Average / Comet`
- TIFF 导出
- 星轨延时视频
- 银河延时视频

第二优先级：

- 间隔填充
- 划痕去除
- 蒙版功能
- 复杂语言系统

### 3.3 Swift 版本先追求稳定，不追求功能膨胀

建议 Swift `v1` 暂不包含：

- 蒙版功能
- 间隔填充
- 划痕去除

原因：

- 这几项当前就属于高复杂度/高不稳定区
- 它们不应成为迁移阻塞项
- 先把主线图像处理能力迁稳更关键

## 4. 目标技术架构

## 4.1 UI 框架建议

建议使用：

- `AppKit` 作为主 UI 框架
- 局部可引入 `SwiftUI` 做简单设置页或关于页

不建议第一版纯 SwiftUI，原因：

- 当前应用是典型桌面工具结构，不是移动端单页应用
- 需要稳定的文件对话框、分栏布局、进度控制、日志视图、菜单栏
- AppKit 在 macOS 原生桌面工具里更直接、更稳

### 4.2 并发模型建议

当前 Python 模型：

- `QThread`
- `signal / slot`
- `threading.Event` 取消

目标 Swift 模型：

- `async/await`
- `Task`
- `AsyncStream<ProcessingEvent>`
- `actor` 保护共享状态

建议结构：

- `ProcessingCoordinator`
- `PreviewCoordinator`
- `ExportCoordinator`
- `SettingsStore`

### 4.3 图像计算建议

当前 Python 技术：

- `numpy`
- `numba`
- `opencv`
- `scipy.ndimage`

目标 Swift 技术：

- `Accelerate`：`vDSP` / `vImage`
- `CoreGraphics` / `ImageIO`
- 需要时再引入 `Metal`

迁移原则：

- 第一版不要先上 Metal
- 先用纯 Swift + Accelerate 跑通
- 只有在性能热点明确时再下沉到 Metal

### 4.4 视频导出建议

当前：

- `cv2.VideoWriter`

目标：

- `AVAssetWriter`
- `CVPixelBufferPool`
- `AVAssetWriterInputPixelBufferAdaptor`

这是原生 macOS 最合适的路径。

## 5. Swift 工程拆分建议

建议使用 Xcode Workspace + Swift Package 的方式拆分。

### 5.1 顶层工程结构

```text
SuperStarTrail.xcworkspace
├── SuperStarTrailApp                # macOS App target
├── Packages
│   ├── StarTrailDomain
│   ├── StarTrailImaging
│   ├── StarTrailRAW
│   ├── StarTrailVideo
│   ├── StarTrailPersistence
│   └── StarTrailTestingSupport
└── Tests
```

### 5.2 模块职责

#### `SuperStarTrailApp`

职责：

- macOS 窗口
- 菜单栏
- 分栏布局
- 用户交互
- 任务触发
- 订阅处理事件并更新 UI

建议组件：

- `MainWindowController`
- `FileSidebarController`
- `ParametersViewController`
- `PreviewViewController`
- `LogViewController`

#### `StarTrailDomain`

职责：

- 领域模型
- 任务参数
- 枚举和错误定义
- 文件命名规则

建议类型：

- `StackMode`
- `ProcessingJob`
- `ProcessingOptions`
- `ProcessingEvent`
- `OutputArtifact`
- `RecentDirectory`
- `AppError`

#### `StarTrailImaging`

职责：

- 图像数据结构
- 亮度拉伸
- 旋转、缩放
- 堆栈算法
- 导出前位深和色彩转换

建议类型：

- `ImageFrame16`
- `PreviewImage`
- `StackingEngine`
- `StretchRenderer`
- `ImageResizer`
- `RotationTransformer`

#### `StarTrailRAW`

职责：

- RAW/TIFF/JPEG/PNG 输入抽象
- 相机 RAW 解码适配

建议协议与实现(经 M0 验证后修订):

- `ImageDecoder`(统一协议)
- `LibRawDecoder`(**主处理路径**,与 Python 版严格一致,C/C++ bridge)
- `CoreImageDecoder`(**预览路径**,原生快,视觉差异可接受)
- `TIFFDecoder` / `StandardImageDecoder`(TIFF / JPEG / PNG 走 ImageIO)
- `DecoderPipeline`(根据调用场景选择 A 或 B 管线)

#### `StarTrailVideo`

职责：

- 延时视频帧管理
- MP4 导出

建议类型：

- `TimelapseEncoder`
- `FrameToneMapper`
- `VideoRenderSettings`

#### `StarTrailPersistence`

职责：

- 设置读写
- 最近目录
- 运行日志
- 任务历史（如未来需要）

建议类型：

- `SettingsStore`
- `RecentDirectoryStore`
- `LogStore`

## 6. RAW 读取方案

这是整个重构里最关键的技术决策点。

### 6.1 现状

当前 Python 使用 `rawpy`，底层依赖 LibRaw。优点：

- 支持格式广
- 成熟
- 输出质量可控

问题：

- Python 打包复杂
- 原生 macOS 集成感弱
- 后续跨语言维护成本高

### 6.2 目标方案(经 M0 第一轮验证后的修订版)

> **重要**:原方案建议"Apple 原生优先 + LibRaw fallback"的双层策略。M0 第一轮(2026-04-21,Nikon Z9 星空 20 张)验证结果**推翻了这一顺序**:Core Image 即使全参数中性化,仍附加不可关闭的 S 形 tone curve(p50 偏移 +3.54%,通道均值比 1.45-1.54×,远超 0.5% 阈值)。详见 `M0_RAW_COMPATIBILITY_REPORT.md` §8-§11。
> 本节已修订为**双管线共存**模型。

建议采用**双管线共存**策略,两条路径并行存在、分工明确:

#### 管线 A:主处理管线(LibRaw)

用于星轨堆栈、最终 TIFF 导出、视频帧渲染 —— 所有需要与 Python 版**像素级一致**的场景。

- 技术:LibRaw(与当前 Python + rawpy 同底层)+ Swift C/C++ bridge 封装
- 优点:输出与现有 Python 版严格一致,老用户感知不到差异
- 约束:引入 C/C++ 依赖,对 App Sandbox / Notarization 带来额外验证成本

#### 管线 B:预览管线(Core Image)

用于缩略图、实时预览、参数调节 —— 对"科学精度"不敏感但对**响应速度**敏感的场景。

- 技术:`CIRAWFilter`(系统自带)
- 优点:速度快(~0.9 s / 45.7 MP)、原生集成、无额外依赖
- 约束:UI 必须明示"预览与最终导出可能有视觉差异",避免用户误判

#### 为什么不是"Apple 原生优先 + LibRaw fallback"

M0 验证证明:Core Image 对 Z9 NEF 的**解码**完美(100% 成功),但**渲染**带有不可关闭的 Apple tone curve。这是 Apple 设计定位问题(面向"所见即所得的用户友好输出"),不是 bug,也不会在未来版本关闭。因此:

- 不能"默认走 Core Image,不足时补 LibRaw" —— 因为 Core Image 在我们的主场景下**始终**不足
- 必须"堆栈和导出走 LibRaw,预览走 Core Image" —— 职责分离而非优先级

### 6.3 实施建议

LibRaw 必须从 **M0.5 阶段**起就落地,不推迟。

建议顺序:

1. **M0.5**:LibRaw 静态库集成(arm64 + x86_64)、Swift C/C++ bridge 跑通、Notarization 小样验证
2. **M0.5**:选型 Swift wrapper —— 自封装 C API 或采用成熟的开源 Swift-LibRaw 包
3. **M1**:设计 `ImageDecoder` 协议,至少两个实现:`LibRawDecoder`(精确)+ `CoreImageDecoder`(预览)
4. **M2**:预览链路接 `CoreImageDecoder`;主处理链路接 `LibRawDecoder`
5. **第二轮 M0**(可推迟):扩充 Canon / Sony / Fuji 样本,验证 LibRaw 在这些品牌的输出与当前 Python 版一致(预期 OK,因为同一底层库)

M0 报告 `M0_RAW_COMPATIBILITY_REPORT.md` 的 §10.3 / §10.5 给出了 `StarTrailRAW` 模块的目标目录结构,M1 直接照搬。

## 7. 图像数据模型建议

当前 Python 基本以 `numpy.ndarray` 作为一切图像载体。Swift 里不建议继续这样散传,但也不建议直接用 `[UInt16]` Array。

Swift `Array<UInt16>` 不保证与 `Accelerate`/`vImage`/`vDSP` 要求的 aligned contiguous buffer 完全兼容,且在循环中增长会触发重分配。图像缓冲必须一次性分配、按 `rowBytes` 对齐、可零拷贝传给 C API。

### 7.1 统一图像数据结构

```swift
enum PixelFormat {
    case rgb16       // 3 通道,每通道 16-bit
    case rgba16      // 4 通道,每通道 16-bit
    case rgbF32      // 3 通道,每通道 Float32(计算阶段)
}

struct ImageBuffer16 {
    let width: Int
    let height: Int
    let channels: Int            // 通常为 3
    let rowBytes: Int            // ≥ width * channels * MemoryLayout<UInt16>.size,按 16 字节上取整
    let pixelFormat: PixelFormat
    var data: Data               // 连续缓冲,长度 = rowBytes * height
}

struct ImageBufferF32 {
    let width: Int
    let height: Int
    let channels: Int
    let rowBytes: Int            // 单位:字节
    var data: Data               // Float32 计算缓冲
}
```

使用原则:

- 读取阶段直接分配 `Data(count: rowBytes * height)`,避免 `[UInt16]` 渐进增长
- 通过 `data.withUnsafeMutableBytes { ... }` 构造 `vImage_Buffer` 或传给 `vDSP`,全程零拷贝
- `rowBytes` 必须显式存储:vImage 所有 API 均按 stride 工作,不能假设 `width * bytesPerPixel`
- 对齐边界(16 / 32 字节)由读取层决定并记录,下游 API 不再自行调整

### 7.2 处理阶段流水

- 输入 → `ImageBuffer16`(RGB 16-bit,统一色彩空间)
- 堆栈 / 拉伸计算 → `ImageBufferF32`
- 导出 → 转回 `ImageBuffer16` 或直接写入目标容器(TIFF / CVPixelBuffer)

### 7.3 值语义与生命周期

- `ImageBuffer16` 是 `struct` + `Data`,Swift 的 COW 机制会在写入时复制。对 > 50 MB 的大图像,建议再包一层 `final class ImageFrameStore` 以显式管理引用,避免无意拷贝
- 传给后台任务的 buffer 用 `let` + 不可变 `Data`;需要就地修改时走 `inout` 或显式 class 引用
- 释放依赖 ARC,大缓冲不要缓存在全局 store,避免峰值内存膨胀

### 7.4 好处

- 逻辑与 numpy 行为一致(都按 stride)
- 便于做像素级对比测试(golden test)
- Accelerate / vImage / Metal 路径均可零拷贝接入
- 行对齐需求明确,后续若上 GPU 不必返工数据布局

## 8. 算法迁移方案

### 8.1 第一阶段必须迁的算法

#### `Lighten`

现状：

- 逐像素最大值

Swift 实现建议：

- 纯循环先实现
- 再用 `vDSP_vmax` 优化

#### `Average`

现状：

- 增量平均

Swift 实现建议：

- `Float32` 累积缓冲
- 单独维护 `count`

#### `Comet`

现状：

- `result * fade + image * (1 - fade)`

Swift 实现建议：

- 纯 `Float32` 计算
- 用 `vDSP` 批量做乘加

### 8.2 第二阶段再迁的算法

#### Gap Filling

现状依赖：

- `scipy.ndimage`
- 形态学/方向性填充

建议：

- `v1` 先不迁
- `v2` 再看是否用 `vImage morphology` 或 `Metal`

#### Satellite Removal

现状依赖：

- OpenCV
- Hough 直线检测

建议：

- `v1` 不做
- `v2` 再决定是否引入 OpenCV for macOS、Vision、或自研检测

#### Mask

建议：

- 当前先不进入 Swift `v1`
- 待主线稳定后重新设计，而不是照抄现有实现

## 9. 预览系统迁移方案

当前预览链路的核心是：

1. 缩图
2. 亮度拉伸
3. 转 8-bit
4. 显示

Swift 版必须保留这个顺序。

### 9.1 预览渲染建议

- 后台处理始终使用 16-bit / Float32
- 预览单独走轻量管线
- 缩图优先于拉伸
- 最后输出 `CGImage` / `NSImage`

### 9.2 拉伸策略建议

当前 Python 有：

- percentile stretch
- 可选 astropy 风格拉伸

Swift `v1` 建议：

- 只实现 `percentile + asinh`
- 不追求与 astropy 完全一致
- 只要求视觉结果稳定、可控

## 10. 导出系统迁移方案

### 10.1 TIFF 导出

Swift `v1` 的硬性要求：

- 能输出 16-bit RGB TIFF
- Photoshop / Lightroom / macOS Preview 可正常打开

建议：

- 第一阶段接受无压缩 TIFF
- 不要一开始就追求复杂压缩和所有元数据保真

### 10.2 JPEG / PNG 导出

属于次级需求，第一版可后补。

### 10.3 视频导出

用 `AVAssetWriter` 实现：

- 星轨形成延时
- 银河运动延时

验收点：

- 帧数正确
- 时长正确
- 输出文件可播放

## 11. 设置与日志迁移方案

### 11.1 设置

建议分层：

- 简单偏好：`UserDefaults`
- 复杂结构：`Codable + JSON`

不建议一开始引入：

- Core Data
- SQLite

### 11.2 日志

建议：

- 统一日志门面
- UI 日志和文件日志分流
- 输出目录保留运行日志

### 11.3 i18n 迁移

当前 Python 使用 `src/i18n/*` 的 JSON 键值结构。Swift 目标:

- 采用 macOS 原生 `.xcstrings`(Xcode 15+)统一管理,编译期校验 key 完整性
- 过渡期可先用 `.strings`(按语言目录)+ `NSLocalizedString`,成本低但缺编译期检查
- 写一个一次性脚本把现有 JSON 键值导出为 `.xcstrings`,避免手工搬运遗漏

注意:

- Python 侧动态拼接的翻译(`"已处理 {n} 张"`)需要改用 `String(format:)` + `%@`/`%lld`,复数形式用 `.stringsdict`
- App 内语言切换在 Swift 下需要重启或手动切换 `Bundle`,先确定要给终端用户哪种体验

### 11.4 历史数据迁移

现有 Python 版写在用户目录下的 JSON(设置、最近目录、窗口布局等),Swift 版必须能读。

策略:

- Swift 首次启动时检测旧 JSON 是否存在
  - 存在 → 解析为对应 `Codable` 结构,写入 Swift 版持久化位置,然后把旧文件重命名为 `*.migrated` 防止重复读取
  - 不存在 → 走全新用户流程
- 优先迁移:最近目录、窗口位置、上次使用的堆栈参数
- 迁移逻辑写成可单测的纯函数,不要在 `AppDelegate` 里混写

注意:

- 若 Swift 版启用 App Sandbox,只能访问 `~/Library/Containers/<bundle-id>/...`,迁移脚本需要覆盖"旧路径在沙盒外"这种场景,必要时引导用户重新授权目录
- Security-scoped bookmark 要在第一次选择目录时生成并存起来,下次启动恢复授权

## 12. 测试策略

## 12.1 Python 作为参考实现

迁移期间，Python 版本不是包袱，而是基准。

建议建立 golden dataset：

- 3 组小样本素材
- 每组 5-20 张
- 包含 RAW / JPEG / TIFF
- 固定参数运行
- 保存标准输出 TIFF 和视频元数据

### 12.2 Swift 需要新增三类测试

#### 单元测试

- `StackMode`
- `StackingEngine`
- `FileNaming`
- `SettingsStore`
- `Preview stretch`

#### Golden Image 测试

对比：

- 尺寸
- 位深
- 像素差异阈值
- 百分位统计

#### 集成测试

对一整组输入文件执行：

- 导入
- 处理
- 导出
- 校验结果文件

### 12.3 Golden 比对的具体容差

像素级比对不能用"肉眼差不多"当标准。建议硬性门槛:

- **无损路径**(TIFF 16-bit,同一 demosaic 源,例如 Swift vs Python 都以 LibRaw 解码)
  - 每通道像素差 ≤ `1/65535`(四舍五入误差上限)
  - 差异像素数占比 ≤ 0.01%
- **允许差异路径**(Swift + Core Image RAW vs Python + rawpy)
  - 每通道像素差 ≤ `256/65535`(≈ 0.4%)
  - 亮度直方图在 P10 / P50 / P90 三个分位的偏差 ≤ 0.5%
  - 全图均值 / 中位数偏差 ≤ 0.5%
- **视频帧**
  - 帧数必须严格相等
  - 同参数输入下 PSNR ≥ 40 dB

容差数字在 M0 阶段需基于一组真实样本校准后**冻结**,后续所有 golden test 以此为回归门槛,避免"阈值跟着结果一起放宽"。

## 13. 迁移阶段

## 阶段 M0：规格冻结与可行性前置验证

目标：

- 冻结 Python 版本功能边界
- 确定 Swift `v1` 范围
- 建立 golden dataset
- **RAW 视觉一致性前置验证**:对比 Core Image RAW 与 rawpy 输出在色调、白平衡、动态范围、demosaic 细节四个维度的差异
- 根据验证结果决定 v1 是否允许视觉差异,或必须经 LibRaw fallback 对齐

**第一轮执行情况(2026-04-21,已完成)**:

- 实际样本:20 张 Nikon Z9 星空 NEF(取自用户 315JMSZ9 序列,参数完全一致)
- 跨品牌验证推迟到"第二轮 M0"(不阻塞 M1)
- 决策结论:**Core Image 不能作主路径**,必须双管线 → 详见 `M0_RAW_COMPATIBILITY_REPORT.md`
- 本文档 §6.2 / §6.3 / 本 §13 M0.5 / §14 / §15 已根据结论更新

产出:

- 迁移功能清单
- 不迁功能清单
- 验收指标(含 12.3 的具体容差数字)
- ✅ **RAW 兼容性结论**:Core Image 渲染一致性不达标,Swift v1 必须走 LibRaw 主处理 + Core Image 预览的双管线架构

## 阶段 M0.5:发布基础设施 + LibRaw 集成

目标:

- 先把"能发布"的能力搭好,避免到 M5 才发现缺证书、缺 entitlement、沙盒 block 了关键功能
- **新增**:由于 M0 确认必须用 LibRaw 主路径,本阶段同时完成 C/C++ bridge 的基础验证,不推迟到 M3

发布基础设施任务:

- 申请 / 核对 Apple Developer 账号与 Developer ID Application 证书
- 建立空壳 Xcode App target,启用 Hardened Runtime
- 明确 App Sandbox 策略:
  - 用户选择目录读写:`com.apple.security.files.user-selected.read-write`
  - 是否需要 Downloads / Pictures 额外 entitlement
  - 视频导出目录的 security-scoped bookmark 持久化方案
- 注册导入 UTI(RAW / TIFF / JPEG / PNG 类型声明),供 Finder / 拖拽集成
- 配置 `notarytool` 流水线,跑通一次空壳的 `build → sign → notarize → staple` 全流程
- CI 上把上述流水线写成可重复脚本,与后续 M5 直接复用

**LibRaw 集成任务(M0 结果触发)**:

- LibRaw 源码获取与静态库编译(支持 `arm64` + `x86_64` fat binary)
- Swift Package Manager 下 C/C++ interop 配置(`CSources/libraw-bridge/`)
- Swift wrapper 选型:
  - **选项 1**:自封装薄层 C API(可控、可定制默认参数以对齐现有 Python 版输出)
  - **选项 2**:采用成熟的开源 Swift-LibRaw 包(快,但需验证质量和维护状态)
- 跑通最小示例:一张 NEF → LibRaw 解码 → 16-bit sRGB TIFF,与现有 Python 版输出做 pixel-level 对比,确认"同底层 → 结果一致"
- **关键风险验证**:LibRaw 静态链接后的 App 通过 Notarization 全流程,无 Hardened Runtime / Sandbox 报错

验收:

- 空壳 App 通过 notarization
- 在干净 macOS 上双击运行无 Gatekeeper 警告
- 拖拽一个 RAW 文件进 App,UTI 能识别
- **LibRaw bridge 跑通一张 Z9 NEF,与 `baseline_rawpy/Z9A_4294__rawpy.tif` 像素级一致**
- **带 LibRaw 静态链接的 App 通过 notarization**

## 阶段 M1：Xcode 工程搭建

目标：

- 建立 Workspace
- 建立 Swift Package 模块
- 跑通空壳窗口、菜单、设置存储、日志

验收：

- App 可启动
- 可选择目录
- 可保存最近目录
- 可显示空预览和日志

## 阶段 M2:输入与预览

目标:

- 跑通 JPEG/TIFF 输入
- 实现双管线 RAW 架构:**预览走 Core Image,主处理走 LibRaw**
- 跑通单图预览和旋转

任务拆分:

- `ImageDecoder` 协议定稿
- `LibRawDecoder` 从 M0.5 的 bridge 扩展,补齐批量解码、错误处理、EXIF 提取
- `CoreImageDecoder` 新建,仅用于预览,调用 `CIRAWFilter` 并做 downscale(`scaleFactor`)提速
- `DecoderPipeline` 按调用方用途(预览 / 堆栈 / 导出)路由到对应 decoder
- UI 层对用户明示"预览图与最终导出可能有轻微视觉差异",避免用户误判

验收:

- 能打开样本图
- 预览显示稳定,响应 < 500 ms @ 45.7 MP 缩略图
- 旋转行为正确
- **预览用 Core Image,导出用 LibRaw,两条路径独立可测**

## 阶段 M3：核心堆栈引擎

目标：

- 实现 `Lighten`
- 实现 `Average`
- 实现 `Comet`

验收：

- 与 Python 输出在容差内一致
- 可处理真实样本
- 进度和取消机制可用

## 阶段 M4：导出与视频

目标：

- TIFF 导出
- 星轨延时导出
- 银河延时导出

验收：

- TIFF 可读
- MP4 可播放
- 输出命名正确

## 阶段 M5：UI 收口与上线准备

目标：

- 参数面板完善
- 错误提示完善
- 设置迁移
- 打包、签名、公证

验收：

- 新版本可供小范围真实使用
- 主线功能稳定

## 阶段 M6：高级功能回迁

候选功能：

- Gap Filling
- Satellite Removal
- Mask

原则：

- 逐项重新评估价值和稳定性
- 不做简单照搬

## 14. 风险清单

> M0 验证后更新(详见 `docs/M0_RAW_COMPATIBILITY_REPORT.md` §10.6)。

### 高风险

- **LibRaw C/C++ bridge 对 App Sandbox 与 Notarization 的额外不确定性** — 第三方原生库需额外审核 entitlements、hardened runtime、dSYM、动态库签名;M0.5 必须把这条链路跑通,否则 M3 之后才发现会造成级联返工
- 16-bit TIFF 写出细节与现有结果不一致(色彩空间标记、压缩、字节序)
- 把 OpenCV / scipy 依赖太早强行迁入
- App Sandbox / notarization 到 M5 才发现 block 问题 → 已由 M0.5 前置规避,但仍需严格执行
- `ImageBuffer16` 数据模型若退化成 `[UInt16]` 或忽略 rowBytes,会引入隐性拷贝,Accelerate 性能收益被抵消

### 中风险

- **双管线正确性维护成本**(LibRaw 处理 + Core Image 预览):预览与导出结果不一致属于设计上的已知行为,需要 UI 文案明示、golden dataset 对两条管线分别回归,否则易被误报成 bug
- RAW 兼容性与 `rawpy` 的残差(经 M0 量化为 p50 ≈ 3.6%、高光区 ≈ 31% 异常、通道比 1.5×):已通过切换到 LibRaw 主管线规避,但若未来 LibRaw 构建受阻、被迫暂时落回 Core Image,差异会直接打到用户交付产物上
- 纯 SwiftUI 在复杂桌面交互下的可控性不足
- 没有 golden dataset 导致"重构成功"无法量化
- 处理链内部位深和颜色转换细节漂移(sRGB / Display P3 / Linear 之间)
- 旧用户设置数据无法无缝迁移(降级为"首次启动引导"可接受,但需提前决定)
- i18n 键值搬运遗漏,某些语言出现原样 key 字串
- Swift Concurrency 下取消语义与当前 `threading.Event` 不完全等价,进度/取消链要重新设计

### 低风险

- 文件命名迁移
- UI 样式重建
- 单语言字符串补齐

## 15. 时间预估

按一个熟悉 macOS / Swift 的工程师节奏估算(M0 实跑之后更新):

- `M0`(规格冻结 + RAW 前置验证):1-2 周 ✅ 首轮已完成,详见 M0 报告
- `M0.5`(签名 / 公证 / 沙盒基础设施 + **LibRaw 集成**):**1.5-2 周**(较原 1 周上调,增量覆盖 SwiftPM C++ interop、libraw 动态库签名与 sandbox entitlements 验证)
- `M1`(Xcode 工程搭建):1-2 周
- `M2`(输入与预览,**双管线接入**):2-3 周
- `M3`(核心堆栈引擎):3-5 周
- `M4`(导出与视频):2-3 周
- `M5`(UI 收口 + 发布):2-3 周

总计:

- 保守可交付主线版本:**12.5-20 周(≈ 3-5 个月)**
- 原方案 6-12 周估算偏乐观,未计入 RAW 兼容性调优、AVAssetWriter 色彩管线调试、App Sandbox 反复验证、golden dataset 持续对齐的实际成本
- M0 验证把"Core Image 单一管线"证伪后,多出的 LibRaw 集成与双管线一致性维护成本已分别吸收到 M0.5 与 M2 的区间上沿

如果第一版强行包含高级功能(gap filling / satellite removal / mask):

- 预估扩展到 **18-26 周**,且发布质量风险陡增

执行建议:

- 锁死 v1 范围,不因"再加一点"让交付时间持续滑动
- 每个里程碑结束做一次 golden dataset 回归,不要累积到 M5 才发现漂移
- `M0` 与 `M0.5` 的产出若结论为"不可行",果断止损比带病推进更便宜

## 16. 推荐结论

建议采用以下策略：

- 用 Xcode + AppKit + Swift Concurrency 作为新主架构
- 用 Swift Package 拆核心模块
- 用 Python 版本作为迁移期真值参考
- Swift `v1` 只做主线功能，不带蒙版、间隔填充、划痕去除
- 主线稳定后，再决定哪些高级功能值得重新设计并回迁

这不是“把 Python 改写成 Swift”。

正确目标应该是：

- 用 Swift 重建一个更稳定、更原生、可长期维护的 macOS 产品
- 只迁真正有价值、能稳定交付的能力

## 17. 下一步建议

在本蓝图基础上,建议按以下顺序推进配套文档:

1. **`M0 RAW 兼容性验证报告`** — 先跑起来,决定 LibRaw fallback 策略
2. **`M0.5 发布基础设施 checklist`** — 证书 / 沙盒 / notarize 流水线
3. `Swift v1 功能冻结清单` — 根据 M0 结果最终确定
4. `Xcode 工程目录与类图设计`
5. `第一阶段(M1-M3)开发任务清单`

顺序背后的原因:

- `M0` 与 `M0.5` 的结论会反过来决定后面所有设计细节(要不要 LibRaw、沙盒下日志文件写哪、bookmark 怎么存),不能跳过
- 类图设计只有在功能冻结清单确定后才有意义,提前做会反复返工


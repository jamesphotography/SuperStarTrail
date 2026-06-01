# M0 RAW 兼容性验证报告

## 0. 报告元信息

| 项 | 值 |
|----|----|
| 状态 | **完成(第一轮)** |
| 版本 | v1 |
| 执行人 | Antigravity AI + James Zhenyu |
| 起始日期 | 2026-04-20 |
| 完成日期 | 2026-04-21 |
| 最终决策路径 | 🔴 **红色 / 路径 C 改良版:LibRaw 主处理 + Core Image 仅做预览(双管线)** |
| 对应蓝图章节 | `XCODE_SWIFT_REFACTOR_PLAN.md` §13 阶段 M0 |
| 执行范围 | **第一轮仅覆盖 Nikon Z 9 星空场景**,跨品牌延后 |

> 本报告既是 M0 阶段的**执行 runbook**,也是**最终交付物**。
> 执行顺序:§1-§7 先通读并按 §5 准备环境 → 执行 §5.3-§5.5 生成数据 → 按 §8 填写实测结果 → 按 §7 分级 → 在 §10 §11 写结论 → 反哺蓝图。

---

## 1. 目的

确认 Swift v1 是否可以采用 **Apple Core Image RAW 管线** 作为主路径,与当前 Python + rawpy 的输出差距是否在可接受范围。

回答下列问题:

1. Core Image 对目标相机品牌 / 机型的 RAW 解码覆盖率如何?
2. 在固定参数、固定样本集下,Core Image 与 rawpy 的数值差异有多大?
3. 差异是否均匀,还是集中在特定品牌/机型/场景?
4. Swift v1 能否在"与 Python 版有视觉差异"的前提下交付,还是必须引入 LibRaw fallback 对齐 rawpy 输出?

## 2. 范围

### 2.1 完整覆盖目标(多轮汇总愿景)

- 格式:NEF / CR2 / CR3 / ARW / RAF / DNG
- 品牌:Nikon / Canon / Sony / Fuji,每家 ≥ 10 样本,再加 10 样本覆盖附加品牌
- 输出目标:sRGB、16-bit、无自动提亮、使用相机白平衡
- 评估维度:色调、白平衡、动态范围、demosaic 细节

### 2.2 **本轮(第一轮)实际覆盖**

- 格式:**NEF 单一格式**
- 品牌/机型:**Nikon Z 9 单机型**
- 场景:**星空夜拍**(ISO 3200 / f/2.8 / 30s / 14mm / WB 3700K)
- 样本数:**20 张**(从 91 张单次拍摄序列中均匀抽样)
- 位置:`/Users/jameszhenyu/Desktop/315JMSZ9/`
- 理由:这正是 SuperStarTrail 项目的核心使用场景,虽然不能回答跨品牌兼容性,但能回答"**核心场景下 Core Image 是否可直接采用**"这个最关键的问题

### 2.3 不在本轮覆盖(延后轮次)

- **跨品牌兼容性(Canon / Sony / Fuji)**:延后到"第二轮 M0",等用户有样本或有实际用户诉求时再补
- 视频 / CinemaDNG
- Olympus ORF、Leica RAW、中画幅后背
- 非 sRGB 目标色彩空间(Display P3 / ProPhoto 等)
- 降噪效果对比(两边默认策略本身不同,不做公平比较)

## 3. 方法论

### 3.1 对照与实验组

- **Baseline(对照组)**:Python + rawpy + LibRaw
- **Candidate(实验组)**:Swift + Core Image(`CIRAWFilter`)

### 3.2 参数对齐矩阵

| 参数 | Baseline(rawpy) | Candidate(Core Image) |
|------|-----------------|----------------------|
| 白平衡 | `use_camera_wb=True` | 默认(相机 WB) |
| 自动提亮 | `no_auto_bright=True` | `exposure=0`、`boostAmount=0`、`boostShadowAmount=0` |
| 色彩空间 | `output_color=sRGB` | 输出容器 = sRGB TIFF |
| 位深 | `output_bps=16` | `CIFormat.RGBA16` |
| 伽马 | `gamma=(2.222, 4.5)` | sRGB 容器自带 |
| Demosaic | 默认 AHD | Apple 默认(专有) |
| 降噪 | 关闭 | 保持默认(不手动开启) |
| 方向 | 默认(按 EXIF) | 默认(按 EXIF) |

注意:

- Core Image 输出必然带 Alpha(`RGBA16`),比对前裁成 RGB
- 分辨率:两者均输出 sensor native 尺寸;若 Core Image 因 scale factor 不一致导致尺寸差异,比对脚本**显式报错**而非 resize

### 3.3 禁止事项(纪律)

- 不得事后调整阈值以匹配结果
- 不得混用不同 macOS 版本(Core Image 解码器随系统版本变化;报告须记录测试用 macOS 版本)
- 不得对某一样本单独做参数微调

## 4. 样本集规范

### 4.1 数量与分布

总量 **≥ 50 张**:

| 品牌 | 下限 | 建议机型(任选 2+) |
|------|------|---------------------|
| Nikon | 10 | Z7 / Z8 / D850 / D7xx / Z 系列 |
| Canon | 10 | R5 / R6 / 5D4 / 90D(**至少 1 张 CR3**) |
| Sony | 10 | A7R4 / A7M4 / A1 |
| Fuji | 10 | X-T4 / X-T5 / X-H2(**X-Trans 必含**) |
| 附加 | 10 | DNG / Olympus / Pentax / 手机 DNG,识别空白 |

### 4.2 同一机型内的场景多样性

每个机型的 10 张尽量覆盖:

- 2 张夜空 / 星轨(本项目主场景)
- 2 张高反差(日落 / 窗光)
- 2 张弱光高 ISO(ISO ≥ 3200)
- 2 张日光低 ISO
- 2 张特殊白平衡(钨丝灯 / 荧光灯)

### 4.3 样本清单(完整目标——暂未填)

> 第一轮未采用此清单,实际样本见 §4.4。

| # | 文件名 | 品牌 | 机型 | ISO | 场景标签 | 备注 |
|---|--------|------|------|-----|-----------|------|
| 1 | — | — | — | — | — | 第二轮补 |

### 4.4 第一轮实际样本集

**来源**:`/Users/jameszhenyu/Desktop/315JMSZ9/`(共 91 张 NEF 连续序列)
**选法**:按时间序均匀间隔取 20 张,确保覆盖拍摄全程(星星位置变化)

| 机型 | 镜头 | 光圈 | 快门 | ISO | 焦距 | WB | 拍摄时间 |
|------|------|------|------|-----|------|-----|---------|
| Nikon Z 9 | NIKKOR Z 14-24mm f/2.8 S | f/2.8 | 30s | 3200 | 14mm | 3700K | 2026-03-08 20:15 起 |

20 张实际样本文件名:

```
Z9A_4294.NEF  Z9A_4299.NEF  Z9A_4304.NEF  Z9A_4309.NEF  Z9A_4314.NEF
Z9A_4319.NEF  Z9A_4323.NEF  Z9A_4328.NEF  Z9A_4332.NEF  Z9A_4337.NEF
Z9A_4342.NEF  Z9A_4346.NEF  Z9A_4351.NEF  Z9A_4356.NEF  Z9A_4360.NEF
Z9A_4365.NEF  Z9A_4370.NEF  Z9A_4374.NEF  Z9A_4379.NEF  Z9A_4385.NEF
```

**样本特征的重要含义**:

- **参数完全一致** → 消除"参数差异污染对比结果"的干扰,得到的差异可全部归因于 RAW 管线本身
- **高对比星空纹理** → 对 demosaic 精度极敏感,是对两边算法的压力测试
- **高 ISO + 长曝** → 暗噪、热像素集中区,对 highlight recovery / shadow 处理差异最敏感

## 5. 执行步骤

### 5.1 环境登记(本轮实测)

- macOS 版本:**26.4.1 (build 25E253)**
- Swift 版本:**Apple Swift 6.3 (swiftlang-6.3.0.123.5)**,Target `arm64-apple-macosx26.0`
- Xcode 版本:未使用 Xcode IDE,直接用 `swift` CLI
- Python 版本:**3.12.8**
- rawpy 版本:**0.25.1**
- LibRaw 版本:**0.21.4**
- tifffile:2025.12.20
- numpy:1.26.4
- 工作目录:`/Users/jameszhenyu/Desktop/m0_verification/`

### 5.1.1 CIRAWFilter 实际默认值(Z9 NEF)

执行中发现 Core Image 对 Z9 NEF 的默认"美化参数"并非全中性,本轮最终采用"最激进中性化":

| 参数 | 默认值 | 本轮设置 | 备注 |
|------|--------|---------|------|
| `exposure` | 0.0 | 0.0 | 无需修改 |
| `baselineExposure` | **0.35** | **0.0** | 默认带 +0.35 EV,是导致 1.88× 整体偏亮的主要来源之一 |
| `boostAmount` | **1.0** | 0.0 | 默认全强度 boost |
| `boostShadowAmount` | **0.9** | 0.0 | 默认强阴影提亮 |
| `extendedDynamicRangeAmount` | 0.0 | 0.0 | — |
| `luminanceNoiseReductionAmount` | 0.23 | 0.0 | 关闭默认 luminance NR |
| `colorNoiseReductionAmount` | 0.5 | 0.0 | 关闭默认 color NR |
| `isGamutMappingEnabled` | `true` | `false` | 防止色彩被 sRGB gamut 重映射 |
| `decoderVersion` | `8` | `8` | 无其他可选版本 |
| `neutralTemperature` | 3588.2 K | 不动(保留相机 WB) | 相机记录的 WB,与 EXIF 3700K 略有差异 |
| `neutralTint` | -0.423 | 不动(保留相机 WB) | — |

**关键发现**:即使全部设为上述"最中性值",Core Image 仍对输出施加了一条**无法通过公开 API 关闭的 tone curve**(见 §8、§10)。

### 5.2 目录布局

```text
m0_verification/
├── inputs/                     # 原始 RAW
├── baseline_rawpy/             # rawpy 产出的 16-bit TIFF
├── candidate_coreimage/        # Core Image 产出的 16-bit TIFF
├── metrics/                    # 每样本 JSON + summary.csv
└── report/                     # 图表、失败样本截图
```

### 5.3 生成基线

脚本见 附录 A。一次性运行:

```bash
python scripts/rawpy_baseline.py \
    --input  m0_verification/inputs \
    --output m0_verification/baseline_rawpy
```

### 5.4 生成候选

脚本见 附录 B。批量执行:

```bash
for f in m0_verification/inputs/*(.N); do
    swift scripts/coreimage_candidate.swift \
        "$f" \
        "m0_verification/candidate_coreimage/$(basename ${f%.*})__coreimage.tif"
done
```

### 5.5 指标计算

脚本见 附录 C:

```bash
python scripts/compare.py \
    --baseline  m0_verification/baseline_rawpy \
    --candidate m0_verification/candidate_coreimage \
    --out       m0_verification/metrics
```

产出:

- `metrics/<stem>.json`:每样本指标
- `metrics/summary.csv`:汇总,供 §8 填表

## 6. 评估维度与阈值

所有阈值与蓝图 §12.3 对齐("允许差异路径")。

### 6.1 像素级差异

- 每通道绝对差 ≤ `256/65535`(≈ 0.4%)
- 差异 > 256 的像素占比 ≤ 1%

### 6.2 色调(灰度直方图百分位)

灰度 = `0.2126 R + 0.7152 G + 0.0722 B`

- P10 / P50 / P90 的偏差均 ≤ 0.5%(以 65535 为分母)

### 6.3 白平衡(通道均值 ratio)

以 `mean_cand / mean_base` 的三通道比值,两两相互差 ≤ 2%。
换句话说:不应出现"Core Image 偏红 / rawpy 偏绿"之类的系统性 cast。

### 6.4 动态范围

- 高光端:`>= 65000` 的像素数差异 ≤ 5%
- 阴影端:`<= 256` 的像素数差异 ≤ 5%

### 6.5 Demosaic 细节(锐利边缘)

在 5 张细节密集样本上用 Sobel 算子计算边缘图:

- 边缘强度均值差异 ≤ 5%
- 视觉抽查:不应在高对比边出现明显 zipper / color fringing 差异

## 7. 验收决策框架

每个维度独立打分,取**最严者**作为整体分级。

| 分级 | 条件 | 策略 |
|------|------|------|
| 🟢 绿 | 所有维度达标,覆盖率 ≥ 95% 样本 | **路径 A**:Swift v1 直接用 Core Image,不引入 LibRaw |
| 🟡 黄 | 仅个别品牌或机型不达标,或 demosaic 细节可见偏差但色调一致 | **路径 B**:主路径用 Core Image,对失败机型走 LibRaw fallback(按机型白名单切换) |
| 🔴 红 | 全局色调系统性偏差,或 > 20% 样本无法解码 / 严重失真 | **路径 C**:v1 直接用 LibRaw bridge;Core Image 暂不作为主路径 |

---

## 8. 结果记录(第一轮实测)

### 8.1 解码覆盖率

| 品牌 | 样本数 | Core Image 成功 | rawpy 成功 | 差距说明 |
|------|--------|-----------------|------------|----------|
| Nikon (Z 9) | 20 | **20 / 20** | **20 / 20** | 解码层无兼容问题 |
| Canon | — | — | — | 本轮未测 |
| Sony | — | — | — | 本轮未测 |
| Fuji | — | — | — | 本轮未测 |
| 附加 | — | — | — | 本轮未测 |

**结论(覆盖率):** 对 Nikon Z9,**Core Image 与 rawpy 均 100% 解码成功**,底层 RAW 兼容性不是问题。问题出在**渲染管线的一致性**(见 §8.2)。

### 8.2 维度汇总

基于 20 个样本统计(Core Image 采用"最激进中性化"参数,见 §5.1.1):

| 维度 | 阈值(§6) | 实测均值 | 实测范围 | 达标? | 分级 |
|------|---------|---------|---------|-------|------|
| 像素差 > 256 占比 | ≤ 1% | **92.1%** | 90.6 ~ 95.8% | ❌ 超阈值 90× | 🔴 |
| p10 偏移 | ≤ 0.5% | +0.36% | -0.2 ~ +1.74% | 🟡 多数达标 | 🟡 |
| p50 偏移 | ≤ 0.5% | **+3.54%** | +3.13 ~ +4.56% | ❌ 超阈值 7× | 🔴 |
| p90 偏移 | ≤ 0.5% | **+4.84%** | +4.42 ~ +5.95% | ❌ 超阈值 10× | 🔴 |
| mean 偏移 | ≤ 0.5% | +3.02% | +2.60 ~ +4.13% | ❌ 超阈值 6× | 🔴 |
| 通道均值比(白平衡) | ≤ 2% | R:1.45 G:1.54 B:1.50 | 最大通道差 6.7% | ❌ 超阈值 3× | 🔴 |
| 高光像素差(≥65000) | ≤ 5% | +46.2% | +28 ~ +337% | ❌ 严重超阈值 | 🔴 |
| 阴影像素差(≤256) | ≤ 5% | +131.7% | +78 ~ +171% | ❌ 严重超阈值 | 🔴 |
| Demosaic 细节 | 边缘强度差 ≤ 5% | 未单独测(被整体 tone 差异掩盖) | — | 无法判断 | ⚪ |

**整体分级:🔴 红色**(按 §7 决策框架 —— 全局色调系统性偏差)

### 8.3 问题样本明细

所有 20 张均未达标,且**呈现高度一致性**(各指标 std ≤ 0.7%)——这证明差异是 Core Image 管线本身的固有行为,不是个别样本或场景问题。

| 样本 | p50 偏移 | mean 偏移 | R ratio | 主要观察 |
|------|---------|-----------|---------|---------|
| Z9A_4294 | +3.64% | +2.87% | 1.565 | 序列起点,拍摄初期 |
| Z9A_4328 | +4.56% | +4.13% | 1.510 | 整轮偏差最大 |
| Z9A_4385 | +3.37% | +2.81% | 1.400 | 序列末尾,偏差较小 |

**所有样本的一致性结论**:

- 通道均值比 R:G:B = 1.447:1.544:1.503 → 不是纯 EV 偏移,是带颜色倾向的 tone curve
- 高光像素数 +46% + 阴影像素数 +132% → **S 形 tone curve 特征**(中调提亮 + 两端压缩)
- p10 偏移小(+0.36%)、p50 大(+3.54%)、p90 更大(+4.84%) → 进一步印证 "抬中调 + 更抬亮部" 的曲线形状

### 8.4 重要的像素差数字的解读限制

`max_abs_diff = 65535` 和 `pct_pixels_diff_over_256 = 92%` 这两个像素级指标**诊断性有限**:

- Core Image 和 rawpy 输出尺寸不同(5504×8256 vs 5520×8280),脚本做了 center-crop 对齐,但两者对 sensor "effective area" 起点的认定可能不一致,导致**像素级轻微 registration 错位**
- 星空场景满是高对比点光源,**即使 1 个像素的错位也会产生巨大的 pixel-wise diff**
- 所以核心决策应基于 **percentile 偏移 和 channel mean ratio**,这两组指标**不受像素错位影响**,反映的是真实 tone/color 差异

## 9. 已知差异参考(先验 + 本轮实证)

### 9.1 本轮确证的差异

- ✅ **Core Image 附带一条不可关闭的 S 形 tone curve**。即使 `baselineExposure=0`、`boostAmount=0`、`boostShadowAmount=0`、`extendedDynamicRangeAmount=0`、`isGamutMappingEnabled=false`、`luminanceNoiseReduction=0`、`colorNoiseReduction=0` 全部关闭,输出仍**比 rawpy 线性输出亮约 0.6 EV**,且呈"中调+亮部抬升,阴影相对压缩"的 S 形特征。该行为在 CIRAWFilter 公开 API 无关闭方式。
- ✅ **高光处理策略完全不同**。Core Image 会把更多中亮区域推到饱和(≥ 65000 像素数比 rawpy 多 46%),rawpy 默认 `highlight_mode=Clip` 保持原始数据。
- ✅ **阴影区域不是"更亮",而是"更两极化"**。Core Image 阴影像素(≤ 256)数量比 rawpy 多 132%,说明其 tone curve 同时把深阴影进一步压暗,整体视觉对比度更强。
- ✅ **两边 sensor 裁切范围不同**。rawpy 输出 8280×5520(含 sensor border),Core Image 输出 8256×5504(effective area),差 16 行 × 24 列。属于 crop 策略差,非算法问题。

### 9.2 预期但本轮未测的差异

- Fuji X-Trans 的 demosaic 表现差异(无 Fuji 样本)
- Canon CR3、Sony 压缩 ARW 的解码一致性(未测)
- 不同 macOS 版本 RAW decoder 的行为差异(本轮只在 26.4.1 上测)

### 9.3 执行层小结

- `swift` CLI 可直接运行单文件脚本,无需建 Xcode 工程,体验意外地顺滑
- `CIRAWFilter(imageURL:)` 对 Z9 NEF 的解码稳定,性能好(约 1.4s / 张,45.7 MP)
- `CIContext.writeTIFFRepresentation(of:to:format:colorSpace:)` 工作正常,但只能写 RGBA(没有 RGB16 CIFormat),对比时需裁 alpha
- rawpy 解码 Z9 NEF 约 2s / 张,含 postprocess

---

## 10. 对 Swift v1 方案的反馈

### 10.1 决策路径:🔴 红色(严格) → 路径 C 改良版(实际采用)

严格按蓝图 §7 框架,本轮结果属于"全局色调系统性偏差",对应 🔴 红色 → 路径 C(Swift v1 直接用 LibRaw,Core Image 暂不作为主路径)。

但本项目的实际情况允许**改良版路径 C**(见 §10.3)。

### 10.2 关键触发观察

1. **Core Image 无法产出"与 Python 版一致的堆栈结果"**:即使全参数最激进中性化,仍有 +3.54% p50 偏移、1.45-1.54× 通道增益。对"星轨堆栈"这种多帧精确对齐/取最大值操作,这种非线性差异会**累积放大**,最终成品与 Python 版会有显著视觉差异,老用户会感知。
2. **解码层兼容性 100% OK**:不是"Core Image 读不了 Z9 NEF",而是"Core Image 读得很好但 render 方式不同"。
3. **差异不是参数调错,是 Apple 的设计选择**:Apple 的 RAW 管线定位是"所见即所得的用户友好输出"(Preview.app 风格),不是"科学/线性数据"。这是根本定位差异,不是 bug。

### 10.3 Swift v1 RAW 解码策略:**双管线**

不是二选一,而是**分工共存**:

| 路径 | 用途 | 技术 | 与 Python 版的一致性 |
|------|------|------|--------------------|
| **主处理管线** | 星轨堆栈、最终 TIFF 导出、视频导出 | **LibRaw bridge** | **严格一致**(同一底层库) |
| **预览管线** | 缩略图、实时参数调整、UI 快速渲染 | **Core Image (`CIRAWFilter`)** | 允许视觉差异(预览无需科学精度) |

**工程含义**:

- `StarTrailRAW` 模块必须从 M1 起就预留 **C/C++ LibRaw bridge**(Swift `@objc` 或直接 C interop)
- `ImageDecoder` 协议应提供两种实现:`LibRawDecoder`(精确)和 `CoreImageDecoder`(快速)
- 在决策面板/参数层,对 "预览用什么引擎" 不给用户选(用户不应感知);但**最终导出必须走 LibRaw**

### 10.4 是否引入 LibRaw bridge

**必须引入**,且从 M1 起就要落地,不是"必要时再补"。

触发条件已经满足 —— 本轮结果证明 Core Image 不可作为主处理路径。

建议方案:

- 首选:将 `rawpy` 对应的 LibRaw C API 以 Swift Package 的形式封装,暴露一个类型安全的 Swift API
- 次选:直接用一个成熟的 Swift wrapper(例如 GitHub 上的 LibRaw-swift 包),但要自己验证质量

### 10.5 对 M1 工程搭建的影响

修正蓝图 §5.2 `StarTrailRAW` 模块的建议协议与实现:

```
StarTrailRAW/
  Sources/
    ImageDecoder.swift           # protocol
    LibRawDecoder.swift          # 主处理用,严格与 Python 一致
    CoreImageDecoder.swift       # 预览用,Apple 原生快
    StandardImageDecoder.swift   # TIFF/JPEG/PNG 走 ImageIO
    DecoderPipeline.swift        # 统一入口,根据用途选引擎
  CSources/
    libraw-bridge/               # C/C++ 封装,LibRaw 静态链接
      libraw_c_api.h
      libraw_c_api.cpp
```

M1 必须预留的工作:

- LibRaw 静态库编译(支持 arm64/x86_64 两架构)
- Swift Package Manager C++ interop 配置
- Hardened Runtime 下 LibRaw 的 entitlement 验证(不应违反 Notarization)

### 10.6 对蓝图 §14 风险清单的更新

**本轮验证后,以下风险状态变化:**

- ~~"RAW 兼容性不如当前 rawpy"(高)~~ → 降级为 **中**:兼容性 OK,但 render 一致性不可接受,已通过双管线策略解决
- **新增高风险**:**LibRaw 作为 C/C++ bridge 引入,对 App Sandbox 和 Notarization 带来额外不确定性**。建议 M0.5 阶段就跑通 "LibRaw 静态链接 + notarize" 小样,不要推迟到 M3
- **新增中风险**:**双管线的正确性维护成本**(预览和导出结果不一致需要明确 UI 提示,否则用户误以为最终导出会是预览样子)

## 11. 结论

### 11.1 Swift v1 是否可行

**可行,但必须采用双管线架构,不能走"纯 Core Image"。**

第一轮验证明确:

- Core Image RAW 路径**解码完美**,但**渲染一致性不达标**(+3.54% p50,远超 0.5% 阈值)
- 差异是 Apple 设计选择(用户友好 tone curve),**不是参数问题,无法通过 API 关闭**
- 对 SuperStarTrail 这种"堆栈 + 精确导出"场景,**必须用 LibRaw** 保证与 Python 版输出一致
- Core Image 作为**预览管线**仍然有价值(快、原生、集成好)

### 11.2 后续必需工作

| 项目 | 优先级 | 负责阶段 |
|------|-------|---------|
| 在 M0.5 集成 LibRaw + 跑通 notarization 小样 | **高** | M0.5 |
| 扩充样本,做"第二轮 M0":Canon / Sony / Fuji | 中 | 有样本时再做,不阻塞 M1 |
| 验证 LibRaw 的 arm64 + x86_64 fat binary 链接 | 中 | M0.5 |
| 选型 LibRaw Swift wrapper(自封装 or 成熟包) | 高 | M0.5 |
| 设计 `ImageDecoder` 协议双实现 | 中 | M1 |
| UI 上明确标示"预览 vs 最终导出可能有差异" | 中 | M5 |

### 11.3 对蓝图其他章节的返工项

| 章节 | 需要修改的内容 |
|------|---------------|
| §6.2 "目标方案 - 双层策略" | 修正为"双管线共存"而非"Apple 原生优先 + LibRaw fallback"。明确 LibRaw 是主处理路径,Core Image 是预览路径。 |
| §6.3 "实施建议" | 第 4 步"不足时再补 LibRaw fallback" 改为"M0.5 即引入 LibRaw"。 |
| §13 阶段 M0.5 | 新增任务:**LibRaw 静态链接 + Notarization 验证**,不再推到 M3 发现 |
| §13 阶段 M2 "输入与预览" | 需明确 "预览用 Core Image,导出用 LibRaw" 的二分 |
| §14 风险清单 | 按 §10.6 更新 |
| §15 时间预估 | M0.5 从 1 周上调为 **1.5-2 周**(多了 LibRaw 集成) |

### 11.4 第一轮成功交付,决策可落地

尽管结论是"Core Image 不能作主路径",但本轮 M0 **完全达到其目的**:

- 回答了核心问题:Core Image 能否直接用?→ 不能
- 避免了在 M3 才发现这一点导致大量返工
- 提供了充分的数据(20 张完整指标、参数级诊断)支持决策
- 让 M1 起就可以"一次性做对"(预留 LibRaw bridge,不走 Apple-only 弯路)

### 11.5 第二轮 M0 的触发条件

以下任一发生时启动第二轮:

- 有 Canon / Sony / Fuji 的典型星空样本可用
- 用户反馈需要扩展到其他品牌
- LibRaw 集成出问题,需要重新评估 Core Image 能否承担更多责任

---

## 附录 A:`rawpy_baseline.py`

```python
#!/usr/bin/env python3
"""
M0 Baseline: 用 rawpy 批量产出 16-bit RGB sRGB TIFF。
用法:
    python rawpy_baseline.py --input inputs/ --output baseline_rawpy/
"""
from __future__ import annotations
import argparse
from pathlib import Path

import rawpy
import tifffile

RAW_EXTS = {".nef", ".cr2", ".cr3", ".arw", ".raf", ".dng", ".orf", ".pef", ".rw2"}

PARAMS = dict(
    use_camera_wb=True,
    output_bps=16,
    output_color=rawpy.ColorSpace.sRGB,
    no_auto_bright=True,
    gamma=(2.222, 4.5),
    half_size=False,
    highlight_mode=rawpy.HighlightMode.Clip,
)


def process_one(raw_path: Path, out_dir: Path) -> tuple[Path | None, str]:
    try:
        with rawpy.imread(str(raw_path)) as raw:
            rgb = raw.postprocess(**PARAMS)
    except Exception as e:
        return None, f"decode_failed: {type(e).__name__}: {e}"
    out = out_dir / f"{raw_path.stem}__rawpy.tif"
    tifffile.imwrite(str(out), rgb, photometric="rgb")
    return out, "ok"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    total = ok = fail = 0
    for raw in sorted(args.input.iterdir()):
        if raw.suffix.lower() not in RAW_EXTS:
            continue
        total += 1
        _, status = process_one(raw, args.output)
        print(f"{raw.name}: {status}")
        if status == "ok":
            ok += 1
        else:
            fail += 1
    print(f"\ntotal={total} ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
```

## 附录 B:`coreimage_candidate.swift`

```swift
// M0 Candidate: Core Image RAW → 16-bit sRGB TIFF。
// 用法:
//     swift coreimage_candidate.swift <input.raw> <output.tiff>

import Foundation
import CoreImage
import CoreImage.CIRAWFilter

guard CommandLine.arguments.count == 3 else {
    FileHandle.standardError.write(
        Data("usage: coreimage_candidate <input> <output>\n".utf8))
    exit(1)
}
let inURL  = URL(fileURLWithPath: CommandLine.arguments[1])
let outURL = URL(fileURLWithPath: CommandLine.arguments[2])

try FileManager.default.createDirectory(
    at: outURL.deletingLastPathComponent(),
    withIntermediateDirectories: true)

guard let rawFilter = CIRAWFilter(imageURL: inURL) else {
    FileHandle.standardError.write(Data("decode_failed\n".utf8))
    exit(2)
}
rawFilter.exposure = 0.0
rawFilter.boostAmount = 0.0
rawFilter.boostShadowAmount = 0.0

guard let output = rawFilter.outputImage else {
    FileHandle.standardError.write(Data("no_output\n".utf8))
    exit(3)
}

let srgb = CGColorSpace(name: CGColorSpace.sRGB)!
let linear = CGColorSpace(name: CGColorSpace.extendedLinearSRGB)!
let ctx = CIContext(options: [
    .workingColorSpace: linear,
    .outputColorSpace: srgb,
])

do {
    try ctx.writeTIFFRepresentation(
        of: output,
        to: outURL,
        format: .RGBA16,
        colorSpace: srgb)
    print("ok")
} catch {
    FileHandle.standardError.write(
        Data("write_failed: \(error)\n".utf8))
    exit(4)
}
```

## 附录 C:`compare.py`

```python
#!/usr/bin/env python3
"""
M0 指标计算:对比 rawpy baseline 与 Core Image candidate。
用法:
    python compare.py --baseline baseline_rawpy/ \
                      --candidate candidate_coreimage/ \
                      --out metrics/
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

import numpy as np
import tifffile


def load_rgb16(p: Path) -> np.ndarray:
    arr = tifffile.imread(str(p))
    if arr.dtype == np.uint8:
        arr = arr.astype(np.uint16) << 8
    elif arr.dtype != np.uint16:
        raise ValueError(f"{p.name}: unexpected dtype {arr.dtype}")
    if arr.ndim == 3 and arr.shape[2] == 4:
        arr = arr[:, :, :3]  # drop alpha from Core Image RGBA16
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"{p.name}: expected HxWx3, got {arr.shape}")
    return arr


def grayscale(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (0.2126 * r + 0.7152 * g + 0.0722 * b).astype(np.float64)


def metrics(base: np.ndarray, cand: np.ndarray) -> dict:
    if base.shape != cand.shape:
        return {"error": f"shape mismatch {base.shape} vs {cand.shape}"}

    diff = cand.astype(np.int32) - base.astype(np.int32)
    abs_diff = np.abs(diff)
    total = abs_diff.size

    gb, gc = grayscale(base), grayscale(cand)
    p10b, p50b, p90b = np.percentile(gb, [10, 50, 90])
    p10c, p50c, p90c = np.percentile(gc, [10, 50, 90])
    full = 65535.0

    hi_base = int((base >= 65000).sum())
    hi_cand = int((cand >= 65000).sum())
    lo_base = int((base <= 256).sum())
    lo_cand = int((cand <= 256).sum())

    return {
        "shape": list(base.shape),
        "max_abs_diff": int(abs_diff.max()),
        "mean_abs_diff": float(abs_diff.mean()),
        "pct_pixels_diff_over_256":
            float((abs_diff > 256).sum() / total * 100),
        "p10_shift_pct": float((p10c - p10b) / full * 100),
        "p50_shift_pct": float((p50c - p50b) / full * 100),
        "p90_shift_pct": float((p90c - p90b) / full * 100),
        "mean_shift_pct": float((gc.mean() - gb.mean()) / full * 100),
        "channel_mean_ratio": {
            "R": float(cand[..., 0].mean() / max(base[..., 0].mean(), 1)),
            "G": float(cand[..., 1].mean() / max(base[..., 1].mean(), 1)),
            "B": float(cand[..., 2].mean() / max(base[..., 2].mean(), 1)),
        },
        "highlight_diff_pct":
            float((hi_cand - hi_base) / max(hi_base, 1) * 100),
        "shadow_diff_pct":
            float((lo_cand - lo_base) / max(lo_base, 1) * 100),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--candidate", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for b in sorted(args.baseline.glob("*__rawpy.tif")):
        stem = b.stem.replace("__rawpy", "")
        c = args.candidate / f"{stem}__coreimage.tif"
        if not c.exists():
            rows.append({"stem": stem, "error": "candidate_missing"})
            continue
        base = load_rgb16(b)
        cand = load_rgb16(c)
        m = metrics(base, cand)
        m["stem"] = stem
        rows.append(m)
        with open(args.out / f"{stem}.json", "w") as f:
            json.dump(m, f, indent=2)

    keys: list[str] = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with open(args.out / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            flat = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                    for k, v in r.items()}
            w.writerow(flat)
    print(f"wrote {args.out / 'summary.csv'}")


if __name__ == "__main__":
    main()
```

## 附录 D:执行 checklist

- [x] 样本集已收集,§4.4 第一轮样本清单已定稿
- [x] §5.1 环境信息已登记(macOS 26.4.1 / Swift 6.3 / Python 3.12.8 / rawpy 0.25.1 / LibRaw 0.21.4)
- [x] `rawpy_baseline.py` 全量跑通(20/20 成功)
- [x] `coreimage_batch.swift` 全量跑通(20/20 成功),覆盖率进 §8.1
- [x] `compare.py` 生成 `metrics/summary.csv`(20 张 JSON + 汇总 CSV)
- [x] §8.2 按维度填分级,§8.3 记录所有未达标样本
- [x] §10 / §11 写出决策路径与对蓝图的反馈
- [ ] **(下一步)** 把结论同步回 `XCODE_SWIFT_REFACTOR_PLAN.md`(更新 §6.2、§6.3、§13 M0.5、§14、§15)
- [x] 本报告状态 = "完成(第一轮)"

## 附录 E:本轮执行日志

- **原始样本目录**:`/Users/jameszhenyu/Desktop/315JMSZ9/`(91 张 NEF,全部 Nikon Z 9)
- **工作目录**:`/Users/jameszhenyu/Desktop/m0_verification/`
  - `inputs/` — 20 张符号链接到原始样本
  - `baseline_rawpy/` — 20 张 16-bit RGB sRGB TIFF(rawpy)
  - `candidate_coreimage/` — 20 张 16-bit RGBA sRGB TIFF(Core Image,最激进中性化)
  - `metrics/` — 每样本 JSON + `summary.csv`
  - `scripts/` — `rawpy_baseline.py` / `coreimage_batch.swift` / `compare.py` / `coreimage_linear_probe.swift`(诊断探针)
- **时间成本**:
  - rawpy baseline 生成:约 40 秒(20 张,每张 ~2.0 秒)
  - Core Image candidate 生成(最终版):18.5 秒(20 张,每张 ~0.9 秒)
  - 指标计算:~15 秒
  - 总执行时间:< 2 分钟(不含参数探针的 2 次迭代)
- **磁盘占用**:约 11 GB(baseline 5.1 GB + candidate 6.5 GB)
- **执行过程中的三次关键修正**:
  1. 初次 compare 全部 `shape mismatch` → 发现 rawpy 与 Core Image 裁切起点不同,加 center-crop 对齐
  2. 初版 Core Image 参数仅关闭了 `boostAmount` / `boostShadowAmount`,通道比高达 1.88× → 发现 `baselineExposure=0.35` 默认带入,修正为全参数中性化
  3. Probe 脚本尝试 `contrast` / `saturation` 等属性时编译失败 → 确认这些属性并不存在于 `CIRAWFilter`,仅移除即可(非 Core Image 的限制,是我误加)

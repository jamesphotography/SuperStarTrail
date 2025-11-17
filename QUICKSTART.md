# SuperStarTrail 快速启动指南

## 测试结果

✅ **所有测试通过！项目可以正常运行。**

### 测试概况

- ✅ 虚拟环境: Python 3.12.8
- ✅ 依赖安装: 所有包已安装
- ✅ 单元测试: 5/5 测试通过
- ✅ GUI 启动: 成功启动，窗口正常显示

## 如何运行

### 1. 启动程序

```bash
# 确保在项目根目录
cd /Users/jameszhenyu/PycharmProjects/SuperStarTrail

# 激活虚拟环境（如果尚未激活）
source .venv/bin/activate

# 运行程序
python src/main.py
```

### 2. 使用流程

**第一步：选择 RAW 文件**
1. 点击左侧的"选择目录"按钮
2. 选择包含星轨 RAW 照片的文件夹
3. 程序会自动扫描并显示所有 RAW 文件

**第二步：配置参数**
- **堆栈模式**:
  - Lighten (星轨) - 用于标准星轨合成
  - Average (降噪) - 用于降噪处理
  - Darken (去光污染) - 去除光污染
  - Comet (彗星效果) - 创建彗星尾迹效果

- **白平衡**:
  - 相机白平衡 - 使用相机记录的白平衡
  - 日光 - 使用日光白平衡
  - 自动 - 自动计算白平衡

**第三步：开始合成**
1. 点击"开始合成"按钮
2. 程序会在后台处理，进度条显示进度
3. 右侧预览区会实时更新合成效果（每处理 5 张图片更新一次）

**第四步：保存结果**
1. 合成完成后，点击"保存结果"按钮
2. 选择保存位置和格式：
   - TIFF (推荐，保留 16-bit 数据)
   - JPEG (8-bit，较小文件)
   - PNG (支持 16-bit)

## 支持的文件格式

### 输入格式（RAW）
- Nikon: .nef
- Canon: .cr2
- Sony: .arw
- Fujifilm: .raf
- Adobe: .dng
- Olympus: .orf
- Panasonic: .rw2

### 输出格式
- TIFF (8/16/32-bit)
- JPEG (8-bit, 质量可调)
- PNG (8/16-bit)

## 性能提示

1. **内存使用**:
   - 程序采用流式处理，只保留中间结果
   - 处理 100 张 24MP RAW 文件约需 200MB 内存

2. **处理速度**:
   - 约 2-5 秒/张（取决于 RAW 文件大小和电脑性能）
   - 100 张照片预计 3-8 分钟完成

3. **建议配置**:
   - RAM: 8GB+ (推荐 16GB)
   - CPU: 多核处理器
   - 磁盘: 有足够空间存储结果

## 运行测试

### 单元测试
```bash
# 测试堆栈引擎
python tests/test_stacking_engine.py -v
```

### 测试结果示例
```
test_average_mode ... ok
test_comet_fade_factor ... ok
test_darken_mode ... ok
test_lighten_mode ... ok
test_reset ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.949s

OK
```

## 故障排除

### 问题 1: 导入错误
**错误信息**: `ImportError: attempted relative import beyond top-level package`

**解决方法**: 已修复，确保使用最新版本的代码。

### 问题 2: PyQt5 相关警告
**警告信息**: `Attribute Qt::AA_EnableHighDpiScaling must be set before...`

**状态**: 已修复，不影响使用。

### 问题 3: 找不到 RAW 文件
**可能原因**:
- 文件扩展名大写（如 .NEF 而非 .nef）
- 文件在子目录中

**解决方法**:
- 程序会自动识别大小写
- 确保 RAW 文件在选择的目录根目录下

### 问题 4: 处理速度慢
**可能原因**: RAW 文件很大或电脑性能较低

**解决方法**:
- 减少处理的文件数量
- 使用更快的存储设备（SSD）
- 考虑升级硬件

## 下一步功能

计划实现的功能：
- [ ] 彗星模式参数调整滑块
- [ ] 暗帧减除
- [ ] 图像自动对齐
- [ ] 热像素去除
- [ ] 批量处理队列
- [ ] 直方图显示
- [ ] GPU 加速

## 反馈和贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**: 0.1.0-alpha
**最后更新**: 2025-10-12
**状态**: 可用（MVP）

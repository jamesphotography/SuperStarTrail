# 帮助文档更新说明 / Help Documentation Update

## 更新时间 / Update Date
2025-11-18

## 更新内容 / Update Summary

### 1. 完全双语支持 / Full Bilingual Support
- ✅ 帮助文档现在支持中文和英文
- ✅ 根据用户在偏好设置中选择的语言自动切换
- ✅ Help documentation now supports Chinese and English
- ✅ Automatically switches based on language selected in preferences

### 2. 更新的文档结构 / Updated Documentation Structure

#### 步骤 1: 选择文件 / Step 1: Select Files
- 说明如何选择图片目录
- 列出支持的文件格式 (RAW, TIFF, JPG, PNG)

#### 步骤 2: 选择堆栈模式 / Step 2: Choose Stack Mode
详细说明四种堆栈模式：
- **Lighten (星轨)**: 传统星轨效果，保留最亮像素
- **Comet (彗星)**: 创造渐变尾巴效果
- **Average (降噪)**: 平均像素值，用于降噪
- **Darken (去光污)**: 保留最暗像素，去除光污染

#### 步骤 3: 调整参数 / Step 3: Adjust Parameters
包含所有新功能的说明：
- **彗星尾巴长度**: 短(0.96)/中(0.97)/长(0.98)
- **亮度拉伸**: 无/自动/自定义三种选项
- **间隙填充**: 形态学算法填补星轨断点
- **延时视频**: 自动生成 MP4 视频
- **白平衡**: 相机/日光/自动

#### 步骤 4: 选择输出目录 / Step 4: Select Output Directory
- 说明如何选择自定义输出目录
- 默认保存位置：原片目录/StarTrail/

#### 步骤 5: 开始处理 / Step 5: Start Processing
- 如何开始处理
- 如何监控进度
- 完成标志

### 3. 使用技巧 / Tips Section
新增专门的技巧章节，包括：
- RAW 格式推荐
- 彗星尾巴长度选择建议
- 亮度拉伸使用场景
- 间隙填充适用情况
- 延时视频处理时间
- 视频时长估算

### 4. 输出文件说明 / Output Files Section
新增输出文件命名规则：
- 星轨图片：`StarTrail_YYYYMMDD_HHMMSS.jpg/tif`
- 延时视频：`StarTrail_Timelapse_YYYYMMDD_HHMMSS.mp4`

## 技术实现 / Technical Implementation

### 文件修改 / Files Modified

1. **src/i18n/translations.py**
   - 添加完整的帮助文档翻译键
   - 中文键：`help_title`, `help_step1_title`, `help_step1_content`, 等
   - 英文键：相同的键，不同的翻译内容

2. **src/ui/dialogs.py**
   - 更新 `PreferencesDialog.__init__()`: 添加翻译器实例
   - 完全重写 `create_help_tab()`: 使用翻译系统
   - 帮助内容现在从翻译字典动态加载

### 翻译键列表 / Translation Keys

```python
# 帮助文档相关键
"help_title"           # 使用说明 / User Guide
"help_step1_title"     # 1. 选择文件 / 1. Select Files
"help_step1_content"   # 步骤1的详细内容
"help_step2_title"     # 2. 选择堆栈模式 / 2. Choose Stack Mode
"help_step2_content"   # 步骤2的详细内容
"help_step3_title"     # 3. 调整参数 / 3. Adjust Parameters
"help_step3_content"   # 步骤3的详细内容
"help_step4_title"     # 4. 选择输出目录 / 4. Select Output Directory
"help_step4_content"   # 步骤4的详细内容
"help_step5_title"     # 5. 开始处理 / 5. Start Processing
"help_step5_content"   # 步骤5的详细内容
"help_tips_title"      # 💡 使用技巧 / 💡 Tips
"help_tips_content"    # 技巧内容
"help_output_title"    # 📁 输出文件 / 📁 Output Files
"help_output_content"  # 输出文件说明
```

## 用户体验改进 / UX Improvements

1. **更全面的功能说明**
   - 详细说明所有四种堆栈模式
   - 包含最新的亮度拉伸功能
   - 更新了彗星尾巴参数值 (0.96/0.97/0.98)

2. **更清晰的步骤指引**
   - 5个明确的操作步骤
   - 每个步骤都有详细说明
   - 包含可选和必选操作的区分

3. **实用的使用技巧**
   - 针对不同场景的推荐设置
   - 处理时间预估
   - 输出结果预期

4. **完整的输出文件信息**
   - 文件命名规则
   - 文件格式说明
   - 如何访问输出结果

## 测试验证 / Testing

✅ 中文帮助文档加载正常
✅ 英文帮助文档加载正常
✅ 翻译系统切换正常
✅ HTML 格式渲染正常
✅ 滚动区域工作正常

## 后续维护 / Future Maintenance

如需添加新的帮助内容：
1. 在 `src/i18n/translations.py` 中添加新的翻译键（中英文）
2. 在 `src/ui/dialogs.py` 的 `create_help_tab()` 方法中使用新键
3. 遵循现有的 HTML 格式规范

---

**注意**: 语言切换需要重启应用才能生效。
**Note**: Language changes require application restart to take effect.

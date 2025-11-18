# 日志使用规范

## 日志级别说明

SuperStarTrail 使用 Python 标准库 logging 模块，遵循以下日志级别规范：

### DEBUG - 调试信息
用于开发和调试时的详细信息，生产环境通常不输出。

**使用场景**:
- 算法执行的详细步骤
- 函数参数和返回值
- 性能分析数据

**示例**:
```python
logger.debug(f"对齐成功: 平移 ({tx:.1f}, {ty:.1f}) 像素, 内点: {inliers}/{total}")
logger.debug(f"预览拉伸参数已缓存: low={p_low:.1f}, high={p_high:.1f}")
```

---

### INFO - 常规信息
记录程序正常运行的关键事件。

**使用场景**:
- 处理开始/完成
- 重要里程碑
- 配置信息

**示例**:
```python
logger.info(f"开始处理 {total} 张图片")
logger.info(f"输出目录: {output_dir}")
logger.info("✅ 对齐测试成功")
```

---

### WARNING - 警告信息
表示潜在问题，但程序可以继续运行。

**使用场景**:
- 降级处理（fallback）
- 可恢复的错误
- 资源不足但不影响核心功能

**示例**:
```python
logger.warning("SIFT 不可用，降级使用 ORB")
logger.warning(f"特征点不足 (图像: {len(kp_img)}, 参考: {len(kp_ref)})")
logger.warning(f"图像对齐功能不可用（OpenCV 未安装），已自动禁用")
```

---

### ERROR - 错误信息
表示严重问题，某个功能无法正常执行。

**使用场景**:
- 文件读取失败
- 算法执行异常
- 不可恢复的错误

**示例**:
```python
logger.error(f"处理失败: {e}")
logger.error(f"对齐失败: {e}")
logger.error("❌ 对齐测试失败")
```

---

## 使用规范

### 1. 导入 Logger

每个模块都应该创建自己的 logger：

```python
from utils.logger import setup_logger

logger = setup_logger(__name__)
```

### 2. 禁止使用 print()

**错误** ❌:
```python
print(f"警告: 特征点不足")
print("处理完成")
```

**正确** ✅:
```python
logger.warning("特征点不足")
logger.info("处理完成")
```

### 3. 异常处理

在捕获异常时，使用 `exc_info=True` 记录完整堆栈：

```python
try:
    process_image(path)
except Exception as e:
    logger.error(f"处理图像失败: {e}", exc_info=True)
```

### 4. 敏感信息

避免记录敏感信息（密码、密钥等）：

**错误** ❌:
```python
logger.info(f"API Key: {api_key}")
```

**正确** ✅:
```python
logger.info("API Key 已加载")
```

### 5. 性能考虑

避免在高频循环中使用 INFO 级别：

**不推荐** ⚠️:
```python
for i in range(10000):
    logger.info(f"处理第 {i} 项")  # 会产生大量日志
```

**推荐** ✅:
```python
for i in range(10000):
    if (i + 1) % 100 == 0:  # 每 100 次记录一次
        logger.info(f"处理进度: {i + 1}/10000")
```

---

## 日志配置

日志配置在 `src/utils/logger.py` 中：

```python
def setup_logger(name: str, level=logging.INFO):
    """设置日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # ... 配置 handler 和 formatter
    return logger
```

### 修改日志级别

在开发时临时启用 DEBUG 级别：

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

---

## 常见模式

### 1. 处理流程日志

```python
logger.info("=" * 60)
logger.info("开始星轨合成")
logger.info(f"文件数量: {total}")
# ... 处理 ...
logger.info("✅ 堆栈完成!")
logger.info(f"总耗时: {duration:.2f} 秒")
logger.info("=" * 60)
```

### 2. 功能降级日志

```python
try:
    feature = ImportOptionalFeature()
except ImportError:
    logger.warning("可选功能不可用，已禁用")
    feature = None
```

### 3. 性能监控日志

```python
import time
start = time.time()
# ... 处理 ...
duration = time.time() - start
logger.debug(f"预览更新完成，耗时: {duration:.3f}秒")
```

---

## 迁移检查清单

将 `print()` 迁移到 `logger` 时：

- [ ] 确保导入了 logger
- [ ] 选择正确的日志级别
- [ ] 删除或注释掉 `print()` 语句
- [ ] 测试日志输出是否正常
- [ ] 检查是否有敏感信息泄漏

---

## 参考

- [Python logging 官方文档](https://docs.python.org/3/library/logging.html)
- [Logging Best Practices](https://docs.python-guide.org/writing/logging/)

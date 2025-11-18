"""
测试图像对齐功能
"""

from pathlib import Path
import numpy as np
from core.raw_processor import RawProcessor
from core.stacking_engine import StackingEngine, StackMode
from utils.logger import setup_logger

# 设置日志
logger = setup_logger("TestAlignment")

# 测试数据目录
test_dir = Path("/Users/jameszhenyu/Desktop/Mark Ma")

# 获取前 5 张图片测试对齐功能
processor = RawProcessor()
raw_files = sorted([f for f in test_dir.iterdir() if processor.is_raw_file(f)])[:5]

logger.info(f"找到 {len(raw_files)} 张测试图片")

# 测试 1: 不启用对齐
logger.info("\n" + "=" * 60)
logger.info("测试 1: 禁用图像对齐")
logger.info("=" * 60)

import time

start_time = time.time()
engine_no_align = StackingEngine(StackMode.LIGHTEN, enable_alignment=False)

for i, path in enumerate(raw_files):
    logger.info(f"[{i+1}/{len(raw_files)}] 处理: {path.name}")
    img = processor.process(path, white_balance="camera")
    engine_no_align.add_image(img)

no_align_time = time.time() - start_time
result_no_align = engine_no_align.get_result()

logger.info(f"不启用对齐 - 总耗时: {no_align_time:.2f} 秒")
logger.info(f"平均速度: {no_align_time/len(raw_files):.2f} 秒/张")

# 测试 2: 启用对齐
logger.info("\n" + "=" * 60)
logger.info("测试 2: 启用图像对齐")
logger.info("=" * 60)

start_time = time.time()
engine_with_align = StackingEngine(StackMode.LIGHTEN, enable_alignment=True)

for i, path in enumerate(raw_files):
    logger.info(f"[{i+1}/{len(raw_files)}] 处理: {path.name}")
    img = processor.process(path, white_balance="camera")
    engine_with_align.add_image(img)

with_align_time = time.time() - start_time
result_with_align = engine_with_align.get_result()

logger.info(f"启用对齐 - 总耗时: {with_align_time:.2f} 秒")
logger.info(f"平均速度: {with_align_time/len(raw_files):.2f} 秒/张")

# 性能对比
logger.info("\n" + "=" * 60)
logger.info("性能对比")
logger.info("=" * 60)
logger.info(f"不启用对齐: {no_align_time:.2f} 秒")
logger.info(f"启用对齐:   {with_align_time:.2f} 秒")
logger.info(f"额外开销:   {with_align_time - no_align_time:.2f} 秒 ({(with_align_time - no_align_time)/len(raw_files):.2f} 秒/张)")

# 保存结果对比
from core.exporter import ImageExporter

exporter = ImageExporter()

output_dir = Path("test_output")
output_dir.mkdir(exist_ok=True)

logger.info("\n保存测试结果...")
exporter.save_tiff(result_no_align, output_dir / "test_no_alignment.tiff", compression=None)
logger.info(f"已保存: {output_dir / 'test_no_alignment.tiff'}")

exporter.save_tiff(result_with_align, output_dir / "test_with_alignment.tiff", compression=None)
logger.info(f"已保存: {output_dir / 'test_with_alignment.tiff'}")

logger.info("\n✅ 测试完成！")
logger.info("请在图像查看器中对比两个 TIFF 文件，观察对齐效果")

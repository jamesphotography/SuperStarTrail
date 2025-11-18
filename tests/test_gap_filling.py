"""
测试间隔填充功能
"""

from pathlib import Path
import numpy as np
from core.raw_processor import RawProcessor
from core.stacking_engine import StackingEngine, StackMode
from core.exporter import ImageExporter
from utils.logger import setup_logger

# 设置日志
logger = setup_logger("TestGapFilling")

# 测试数据目录
test_dir = Path("/Users/jameszhenyu/Desktop/Mark Ma")

# 获取前 10 张图片测试
processor = RawProcessor()
raw_files = sorted([f for f in test_dir.iterdir() if processor.is_raw_file(f)])[:10]

logger.info(f"找到 {len(raw_files)} 张测试图片")

# 读取并堆栈所有图片
logger.info("\n" + "=" * 60)
logger.info("步骤 1: 处理图片并堆栈")
logger.info("=" * 60)

import time

start_time = time.time()
engine = StackingEngine(StackMode.LIGHTEN, enable_gap_filling=False)

for i, path in enumerate(raw_files):
    logger.info(f"[{i+1}/{len(raw_files)}] 处理: {path.name}")
    img = processor.process(path, white_balance="camera")
    engine.add_image(img)

process_time = time.time() - start_time
logger.info(f"图片处理完成，耗时: {process_time:.2f} 秒")

# 获取堆栈结果（不填充）
result_no_fill = engine.get_result()
logger.info(f"堆栈结果形状: {result_no_fill.shape}")

# 测试不同的填充方法
fill_methods = [
    ("directional", "方向自适应（推荐弧形星轨）"),
    ("morphological", "形态学闭运算"),
    ("linear", "线性插值"),
    ("motion_blur", "运动模糊"),
]

fill_sizes = [3, 5, 7]

output_dir = Path("test_output/gap_filling")
output_dir.mkdir(parents=True, exist_ok=True)

exporter = ImageExporter()

# 保存不填充的版本
logger.info("\n保存原始结果（无填充）...")
exporter.save_tiff(result_no_fill, output_dir / "no_gap_filling.tiff", compression=None)
logger.info(f"已保存: {output_dir / 'no_gap_filling.tiff'}")

# 测试每种填充方法
logger.info("\n" + "=" * 60)
logger.info("步骤 2: 测试间隔填充方法")
logger.info("=" * 60)

from core.gap_filler import GapFiller

for method, method_name in fill_methods:
    logger.info(f"\n测试填充方法: {method_name} ({method})")

    for gap_size in fill_sizes:
        logger.info(f"  间隔大小: {gap_size} 像素")

        start_time = time.time()
        filler = GapFiller(method=method)
        result_filled = filler.fill_gaps(
            result_no_fill.copy(),
            gap_size=gap_size,
            intensity_threshold=0.1,
        )
        fill_time = time.time() - start_time

        logger.info(f"  填充完成，耗时: {fill_time:.3f} 秒")

        # 保存结果
        filename = f"gap_fill_{method}_size{gap_size}.tiff"
        exporter.save_tiff(result_filled, output_dir / filename, compression=None)
        logger.info(f"  已保存: {output_dir / filename}")

# 测试自适应填充
logger.info("\n" + "=" * 60)
logger.info("步骤 3: 测试自适应填充")
logger.info("=" * 60)

start_time = time.time()
filler_adaptive = GapFiller(method="morphological")
result_adaptive = filler_adaptive.adaptive_fill(
    result_no_fill.copy(),
    min_gap=1,
    max_gap=5,
    brightness_threshold=0.1,
)
adaptive_time = time.time() - start_time

logger.info(f"自适应填充完成，耗时: {adaptive_time:.3f} 秒")
exporter.save_tiff(result_adaptive, output_dir / "gap_fill_adaptive.tiff", compression=None)
logger.info(f"已保存: {output_dir / 'gap_fill_adaptive.tiff'}")

# 测试星轨平滑器
logger.info("\n" + "=" * 60)
logger.info("步骤 4: 测试星轨平滑器")
logger.info("=" * 60)

from core.gap_filler import StarTrailSmoother

smoother = StarTrailSmoother()

# 轻度平滑
start_time = time.time()
result_smooth_light = smoother.smooth_trails(
    result_no_fill.copy(), window_size=3, sigma=0.5
)
smooth_light_time = time.time() - start_time

logger.info(f"轻度平滑完成，耗时: {smooth_light_time:.3f} 秒")
exporter.save_tiff(
    result_smooth_light, output_dir / "smooth_light.tiff", compression=None
)
logger.info(f"已保存: {output_dir / 'smooth_light.tiff'}")

# 中度平滑
start_time = time.time()
result_smooth_medium = smoother.smooth_trails(
    result_no_fill.copy(), window_size=5, sigma=1.0
)
smooth_medium_time = time.time() - start_time

logger.info(f"中度平滑完成，耗时: {smooth_medium_time:.3f} 秒")
exporter.save_tiff(
    result_smooth_medium, output_dir / "smooth_medium.tiff", compression=None
)
logger.info(f"已保存: {output_dir / 'smooth_medium.tiff'}")

# 增强连续性
start_time = time.time()
result_enhanced = smoother.enhance_continuity(result_no_fill.copy(), iterations=2)
enhance_time = time.time() - start_time

logger.info(f"连续性增强完成，耗时: {enhance_time:.3f} 秒")
exporter.save_tiff(result_enhanced, output_dir / "enhanced_continuity.tiff", compression=None)
logger.info(f"已保存: {output_dir / 'enhanced_continuity.tiff'}")

# 性能总结
logger.info("\n" + "=" * 60)
logger.info("性能总结")
logger.info("=" * 60)
logger.info(f"图片处理: {process_time:.2f} 秒")
logger.info(f"形态学填充 (3px): ~{fill_time:.3f} 秒")
logger.info(f"自适应填充: {adaptive_time:.3f} 秒")
logger.info(f"轻度平滑: {smooth_light_time:.3f} 秒")
logger.info(f"连续性增强: {enhance_time:.3f} 秒")

logger.info("\n" + "=" * 60)
logger.info("✅ 测试完成！")
logger.info("=" * 60)
logger.info(f"\n所有结果已保存到: {output_dir}")
logger.info("\n对比建议:")
logger.info("1. 打开 Photoshop 或其他图像查看器")
logger.info("2. 加载所有 TIFF 文件")
logger.info("3. 放大到 100%-200%")
logger.info("4. 对比星轨的连续性和流畅度")
logger.info("5. 推荐方法: 形态学闭运算 (gap_fill_morphological_size3.tiff)")
logger.info("\n文件列表:")
logger.info("- no_gap_filling.tiff          : 原始堆栈（无填充）")
logger.info("- gap_fill_morphological_*.tiff: 形态学填充（推荐）")
logger.info("- gap_fill_linear_*.tiff       : 线性插值填充")
logger.info("- gap_fill_motion_blur_*.tiff  : 运动模糊填充")
logger.info("- gap_fill_adaptive.tiff       : 自适应填充")
logger.info("- smooth_*.tiff                : 平滑处理")
logger.info("- enhanced_continuity.tiff     : 连续性增强")

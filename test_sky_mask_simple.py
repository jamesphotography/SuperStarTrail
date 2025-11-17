"""
天空蒙版生成测试（简化版）

只测试核心功能：天空分割 + 蒙版导出
"""

import sys
from pathlib import Path
import time
import numpy as np
from PIL import Image
import rawpy

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.sky_detector import SkyDetector
from core.mask_utils import MaskUtils


def test_sky_mask_generation():
    """测试天空蒙版生成"""
    print("=" * 70)
    print("天空蒙版生成测试")
    print("=" * 70)

    # 测试目录
    test_dir = Path("/Users/jameszhenyu/PycharmProjects/SuperStarTrail/startrail-test")
    test_files = sorted(test_dir.glob("*.NEF"))

    if not test_files:
        print("❌ 未找到测试文件")
        return

    test_file = test_files[0]
    print(f"\n测试文件: {test_file.name}")

    # 读取 RAW 文件
    print("正在读取 RAW 文件...")
    with rawpy.imread(str(test_file)) as raw:
        rgb_array = raw.postprocess(use_camera_wb=True, output_bps=8)

    image = Image.fromarray(rgb_array)
    print(f"图像尺寸: {image.size[0]} × {image.size[1]}")

    # 初始化检测器
    print("\n初始化 SegFormer-B0 模型...")
    start_time = time.time()
    detector = SkyDetector(model_size="b0")

    # 生成天空蒙版
    print("正在生成天空蒙版...")
    sky_mask = detector.segment(image)
    elapsed = time.time() - start_time

    # 统计
    sky_pixels = np.sum(sky_mask > 127)
    total_pixels = sky_mask.size
    sky_percentage = (sky_pixels / total_pixels) * 100

    print(f"\n✅ 分割完成 (耗时: {elapsed:.2f}秒)")
    print(f"   天空占比: {sky_percentage:.1f}%")
    print(f"   地面占比: {100 - sky_percentage:.1f}%")

    # 创建输出目录
    output_dir = Path("test_output_simple")
    output_dir.mkdir(exist_ok=True)

    # 1. 保存天空蒙版（黑白）
    mask_file = output_dir / f"{test_file.stem}_sky_mask.png"
    Image.fromarray(sky_mask).save(mask_file)
    print(f"\n保存文件:")
    print(f"   1. {mask_file} (天空蒙版)")

    # 2. 获取天空和地面蒙版
    sky_mask_only, ground_mask = detector.get_sky_and_ground_masks(image)

    sky_file = output_dir / f"{test_file.stem}_sky_only.png"
    ground_file = output_dir / f"{test_file.stem}_ground_only.png"

    Image.fromarray(sky_mask_only).save(sky_file)
    Image.fromarray(ground_mask).save(ground_file)

    print(f"   2. {sky_file} (仅天空)")
    print(f"   3. {ground_file} (仅地面)")

    # 3. 创建预览叠加
    overlay = MaskUtils.create_preview_overlay(
        np.array(image),
        sky_mask,
        overlay_color=(0, 255, 255),  # 青色
        alpha=0.3
    )

    overlay_file = output_dir / f"{test_file.stem}_preview.png"
    Image.fromarray(overlay).save(overlay_file)
    print(f"   4. {overlay_file} (预览叠加)")

    # 4. 创建对比图
    comparison_file = output_dir / f"{test_file.stem}_comparison.png"
    MaskUtils.save_mask_comparison(
        np.array(image),
        sky_mask,
        str(comparison_file)
    )
    print(f"   5. {comparison_file} (对比图)")

    print(f"\n✅ 测试完成！")
    print(f"\n使用建议:")
    print(f"   - 在 Photoshop 中打开星轨图像")
    print(f"   - 加载 {mask_file.name} 作为选区")
    print(f"   - 使用选区对天空和地面分别调色")

    return sky_mask


def test_workflow_integration():
    """测试完整工作流集成"""
    print("\n" + "=" * 70)
    print("完整工作流测试：堆栈 + 蒙版")
    print("=" * 70)

    from core.stacking_engine import StackingEngine, StackMode
    from core.raw_processor import RawProcessor

    test_dir = Path("/Users/jameszhenyu/PycharmProjects/SuperStarTrail/startrail-test")
    raw_files = sorted(test_dir.glob("*.NEF"))

    if len(raw_files) < 3:
        print("⚠️  测试图片少于 3 张，跳过")
        return

    # 使用前 3 张快速测试
    test_files = raw_files[:3]
    print(f"\n使用 {len(test_files)} 张图片")

    # 堆栈
    print("\n步骤 1: 星轨堆栈")
    raw_processor = RawProcessor()
    stacking_engine = StackingEngine(mode=StackMode.LIGHTEN)

    start_time = time.time()
    for i, path in enumerate(test_files, 1):
        print(f"   处理 {i}/{len(test_files)}: {path.name}")
        img = raw_processor.process(path, white_balance="camera")
        stacking_engine.add_image(img)

    stacked = stacking_engine.get_result()
    stack_time = time.time() - start_time
    print(f"   ✅ 堆栈完成 (耗时: {stack_time:.2f}秒)")

    # 生成蒙版
    print("\n步骤 2: 生成天空蒙版")
    stacked_8bit = (stacked / 256).astype(np.uint8)
    image_pil = Image.fromarray(stacked_8bit)

    detector = SkyDetector(model_size="b0")
    sky_mask = detector.segment(image_pil)
    print(f"   ✅ 蒙版生成完成")

    # 保存结果
    output_dir = Path("test_output_simple")
    output_dir.mkdir(exist_ok=True)

    import tifffile

    stacked_file = output_dir / "star_trail.tiff"
    mask_file = output_dir / "star_trail_sky_mask.png"

    tifffile.imwrite(stacked_file, stacked, compression='deflate')
    Image.fromarray(sky_mask).save(mask_file)

    print(f"\n✅ 工作流测试完成！")
    print(f"   总耗时: {time.time() - start_time:.2f}秒")
    print(f"\n保存文件:")
    print(f"   1. {stacked_file} (星轨 16-bit TIFF)")
    print(f"   2. {mask_file} (天空蒙版)")

    print(f"\nPhotoshop 使用步骤:")
    print(f"   1. 打开 {stacked_file.name}")
    print(f"   2. 选择 > 载入选区 > {mask_file.name}")
    print(f"   3. 选区内（天空）: 调色、去光污染")
    print(f"   4. 反选 (Cmd+Shift+I): 调整地面")


def main():
    """运行测试"""
    print("\n" + "=" * 70)
    print("SuperStarTrail - 天空蒙版功能测试")
    print("=" * 70)

    # 测试 1: 天空蒙版生成
    test_sky_mask_generation()

    # 测试 2: 完整工作流
    test_workflow_integration()

    print("\n" + "=" * 70)
    print("✅ 所有测试完成！")
    print("=" * 70)

    print("\n核心功能:")
    print("  ✅ 天空分割 (SegFormer-B0)")
    print("  ✅ 蒙版导出 (PNG)")
    print("  ✅ 星轨堆栈 + 蒙版生成")

    print("\n简洁理念:")
    print("  • SuperStarTrail 专注于堆栈和蒙版")
    print("  • 调色和后期在 Photoshop 中完成")
    print("  • 提供高质量 16-bit TIFF + 精确蒙版")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
测试完整的星轨合成流程
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.raw_processor import RawProcessor
from core.stacking_engine import StackingEngine, StackMode
from core.exporter import ImageExporter

def test_stacking(num_images=10):
    """测试星轨合成"""
    test_dir = Path("/Users/jameszhenyu/Desktop/Mark Ma")
    output_path = Path("test_star_trail.tiff")

    print(f"=== SuperStarTrail 星轨合成测试 ===\n")

    # 初始化
    processor = RawProcessor()
    engine = StackingEngine(StackMode.LIGHTEN)
    exporter = ImageExporter()

    # 获取 NEF 文件
    nef_files = sorted(list(test_dir.glob("*.NEF")))[:num_images]
    print(f"✅ 找到 {len(nef_files)} 个 NEF 文件")
    print(f"📸 使用前 {num_images} 张进行测试\n")

    # 开始处理
    print("开始处理...")
    print("-" * 60)

    total_start = time.time()

    for i, raw_file in enumerate(nef_files, 1):
        try:
            start = time.time()

            # 读取 RAW
            img = processor.process(raw_file, white_balance="camera")

            # 添加到堆栈
            engine.add_image(img)

            duration = time.time() - start
            print(f"[{i:3d}/{num_images}] {raw_file.name} - {duration:.2f}秒")

        except Exception as e:
            print(f"❌ 处理失败: {raw_file.name} - {e}")
            return False

    total_duration = time.time() - total_start

    print("-" * 60)
    print(f"\n✅ 处理完成!")
    print(f"总耗时: {total_duration:.2f} 秒")
    print(f"平均: {total_duration/num_images:.2f} 秒/张\n")

    # 获取结果
    print("获取堆栈结果...")
    result = engine.get_result()
    print(f"结果形状: {result.shape}")
    print(f"数据类型: {result.dtype}")
    print(f"像素范围: {result.min()} - {result.max()}\n")

    # 保存结果
    print(f"保存结果到: {output_path}")
    success = exporter.save_tiff(result, output_path, bits=16, compression="lzw")

    if success:
        file_size = output_path.stat().st_size / 1024 / 1024
        print(f"✅ 保存成功! 文件大小: {file_size:.2f} MB\n")
        return True
    else:
        print("❌ 保存失败\n")
        return False

if __name__ == "__main__":
    # 先测试 10 张
    success = test_stacking(num_images=10)

    if success:
        print("=" * 60)
        print("🎉 测试成功! 代码运行正常!")
        print("=" * 60)
        print("\n提示:")
        print("- 可以在当前目录找到 test_star_trail.tiff")
        print("- 要处理所有 206 张图片，修改 num_images 参数")
        print("- 预计全部处理需要 5-10 分钟")
        sys.exit(0)
    else:
        print("❌ 测试失败")
        sys.exit(1)

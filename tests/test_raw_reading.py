#!/usr/bin/env python3
"""
测试 RAW 文件读取功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.raw_processor import RawProcessor

def test_read_nef():
    """测试读取 NEF 文件"""
    test_dir = Path("/Users/jameszhenyu/Desktop/Mark Ma")

    processor = RawProcessor()

    # 获取所有 NEF 文件
    nef_files = list(test_dir.glob("*.NEF"))
    print(f"找到 {len(nef_files)} 个 NEF 文件")

    if not nef_files:
        print("❌ 没有找到 NEF 文件")
        return False

    # 测试读取第一个文件
    test_file = nef_files[0]
    print(f"\n测试文件: {test_file.name}")
    print(f"文件大小: {test_file.stat().st_size / 1024 / 1024:.2f} MB")

    try:
        # 获取元数据
        print("\n读取元数据...")
        metadata = processor.get_metadata(test_file)
        print(f"相机: {metadata.get('camera', 'Unknown')}")
        print(f"ISO: {metadata.get('iso', 'Unknown')}")
        print(f"分辨率: {metadata.get('width', 0)} x {metadata.get('height', 0)}")

        # 读取缩略图
        print("\n读取缩略图...")
        thumb = processor.get_thumbnail(test_file, max_size=512)
        if thumb is not None:
            print(f"✅ 缩略图: {thumb.shape}")
        else:
            print("⚠️  无法获取缩略图")

        # 处理 RAW 文件
        print("\n处理 RAW 文件...")
        import time
        start = time.time()
        img = processor.process(test_file)
        duration = time.time() - start

        print(f"✅ 处理成功!")
        print(f"   输出形状: {img.shape}")
        print(f"   数据类型: {img.dtype}")
        print(f"   处理耗时: {duration:.2f} 秒")
        print(f"   像素范围: {img.min()} - {img.max()}")

        return True

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_read_nef()
    sys.exit(0 if success else 1)

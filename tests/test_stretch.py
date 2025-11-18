"""
测试亮度拉伸功能
"""
import numpy as np
from pathlib import Path
from core.exporter import ImageExporter

# 创建一个模拟的暗图像（大部分像素值很低）
print("创建测试图像...")
image = np.random.randint(0, 5000, (100, 100, 3), dtype=np.uint16)  # 大部分像素在 0-5000
image[40:60, 40:60, :] = 30000  # 添加一些亮区域

print(f"原始图像统计:")
print(f"  最小值: {image.min()}")
print(f"  最大值: {image.max()}")
print(f"  平均值: {image.mean():.0f}")

# 应用拉伸
stretched = ImageExporter.apply_stretch(image)

print(f"\n拉伸后图像统计:")
print(f"  最小值: {stretched.min()}")
print(f"  最大值: {stretched.max()}")
print(f"  平均值: {stretched.mean():.0f}")

# 测试保存
exporter = ImageExporter()
test_path = Path("/tmp/test_stretched.tif")

print(f"\n保存到: {test_path}")
success = exporter.save_tiff(stretched, test_path, apply_stretch=False)  # 已经拉伸过了
print(f"保存{'成功' if success else '失败'}")

print("\n✅ 测试完成！")

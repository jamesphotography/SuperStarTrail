#!/usr/bin/env python3
"""
放大图标内容，减少边距
"""
from PIL import Image

# 读取当前图标
img = Image.open('icon-logo.png').convert('RGBA')

# 计算裁剪区域 - 去掉周围更多的深色边框
# 原图是 1024x1024，裁剪掉周围 25% 的边距（保留中间 50%）
width, height = img.size

# 裁剪掉周围约 25% 的边距
crop_margin = int(width * 0.25)
crop_box = (crop_margin, crop_margin, width - crop_margin, height - crop_margin)

# 裁剪并放大
cropped = img.crop(crop_box)
enlarged = cropped.resize((width, height), Image.Resampling.LANCZOS)

# 保存
enlarged.save('logo-enlarged.png', 'PNG')
print("✓ 已创建放大版本图标: logo-enlarged.png")
print(f"  原始尺寸: {width}x{height}")
print(f"  裁剪区域: {crop_box}")
print(f"  最终尺寸: {enlarged.size}")

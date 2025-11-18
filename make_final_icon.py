#!/usr/bin/env python3
"""
创建最终的透明放大图标
"""
from PIL import Image
import numpy as np

# 读取放大后的图标
img = Image.open('logo-enlarged.png').convert('RGBA')
data = np.array(img)

# 获取 RGBA 通道
r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]

# 创建遮罩：深蓝色背景（RGB 值接近深蓝）
# 深蓝色定义为 R < 50, G < 50, B > 30
dark_blue_mask = (r < 50) & (g < 50) & (b > 30)

# 将深蓝色背景设置为透明
data[dark_blue_mask] = [0, 0, 0, 0]

# 创建新图像
result = Image.fromarray(data, 'RGBA')

# 保存为透明背景的 PNG
result.save('logo.png', 'PNG')
print("✓ 已创建最终透明放大图标: logo.png")

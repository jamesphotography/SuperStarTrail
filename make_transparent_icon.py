#!/usr/bin/env python3
"""
将图标的白色背景替换为透明背景
"""
from PIL import Image
import numpy as np

# 读取原始图标
img = Image.open('icon-logo.png').convert('RGBA')
data = np.array(img)

# 获取 RGB 通道
r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]

# 创建遮罩：接近白色的像素（考虑到可能有轻微的颜色偏差）
# 白色定义为 RGB 值都大于 240
white_mask = (r > 240) & (g > 240) & (b > 240)

# 将白色区域设置为完全透明
data[white_mask] = [255, 255, 255, 0]

# 创建新图像
result = Image.fromarray(data, 'RGBA')

# 保存为透明背景的 PNG
result.save('logo-transparent.png', 'PNG')
print("✓ 已创建透明背景图标: logo-transparent.png")

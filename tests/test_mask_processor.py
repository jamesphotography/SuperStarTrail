"""
MaskProcessor 单元测试
"""
import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.mask_processor import MaskProcessor


@pytest.fixture
def tmp_png(tmp_path):
    """创建临时 PNG 蒙版文件（白色天空，黑色地景）"""
    mask_array = np.zeros((100, 200), dtype=np.uint8)
    mask_array[:50, :] = 255  # 上半部分为白色（天空）
    img = Image.fromarray(mask_array, mode='L')
    path = tmp_path / "mask.png"
    img.save(path)
    return path


def test_load_returns_float32(tmp_png):
    """load() 应返回 float32 数组"""
    result = MaskProcessor.load(tmp_png, target_shape=(100, 200))
    assert result.dtype == np.float32


def test_load_value_range(tmp_png):
    """load() 返回的值应在 0.0~1.0 之间"""
    result = MaskProcessor.load(tmp_png, target_shape=(100, 200))
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_load_white_black_values(tmp_png):
    """白色区域=1.0，黑色区域=0.0"""
    result = MaskProcessor.load(tmp_png, target_shape=(100, 200))
    assert result[0, 0] == pytest.approx(1.0)    # 上半白色
    assert result[99, 0] == pytest.approx(0.0)   # 下半黑色


def test_load_resize_to_target(tmp_png):
    """load() 应将蒙版 resize 到 target_shape"""
    result = MaskProcessor.load(tmp_png, target_shape=(300, 600))
    assert result.shape == (300, 600)


def test_load_rotation_90_swaps_dims(tmp_path):
    """rotation=90 后蒙版宽高互换，与图像旋转保持一致"""
    mask_array = np.zeros((100, 200), dtype=np.uint8)
    img = Image.fromarray(mask_array, mode='L')
    path = tmp_path / "mask.png"
    img.save(path)
    # 竖向蒙版(100,200) + rotation=90 → 横向(200,100)
    result = MaskProcessor.load(path, target_shape=(200, 100), rotation=90)
    assert result.shape == (200, 100)


def test_load_file_not_found():
    """文件不存在时应抛出 FileNotFoundError"""
    with pytest.raises(FileNotFoundError):
        MaskProcessor.load(Path("/nonexistent/mask.png"), target_shape=(100, 200))


def test_load_non_png(tmp_path):
    """非 PNG 文件应抛出 ValueError"""
    jpg_path = tmp_path / "mask.jpg"
    img = Image.fromarray(np.zeros((100, 200), dtype=np.uint8), mode='L')
    img.save(jpg_path)
    with pytest.raises(ValueError):
        MaskProcessor.load(jpg_path, target_shape=(100, 200))


def test_load_soft_mask_reduces_transition_band(tmp_path):
    """软边蒙版应被收敛成较窄的过渡带，减少融合发灰"""
    gradient = np.tile(np.linspace(0, 255, 100, dtype=np.uint8), (20, 1))
    path = tmp_path / "soft_mask.png"
    Image.fromarray(gradient, mode="L").save(path)

    result = MaskProcessor.load(path, target_shape=(20, 100))

    transition_cols = np.where(
        np.any((result > 0.1) & (result < 0.9), axis=0)
    )[0]

    assert result[:, 0].max() < 0.05
    assert result[:, -1].min() > 0.95
    assert len(transition_cols) < 20

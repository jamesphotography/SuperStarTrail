"""
测试天空检测功能 (使用 SegFormer)
"""

import pytest
from PIL import Image
import rawpy
import numpy as np
from pathlib import Path

from src.core.sky_detector import SkyDetector

# --- 测试配置 ---
# 用户提供的 RAW 文件路径
RAW_FILE_PATH = "/Users/jameszhenyu/Desktop/Mark Ma/Z9L_8844-2.NEF"
# 定义输出蒙版的文件名
OUTPUT_MASK_FILENAME = "sky_mask_segformer_Z9L_8844-2.png"


@pytest.fixture(scope="module")
def sky_detector_instance():
    """提供一个 SkyDetector 的单例（SegFormer-B0）"""
    try:
        # 使用 B0 模型（快速）
        detector = SkyDetector(model_size="b0")
        print(f"\n✅ 创建 SkyDetector 实例 (model: SegFormer-{detector.model_size})")
        return detector
    except Exception as e:
        pytest.fail(f"创建 SkyDetector 失败: {e}")


@pytest.fixture(scope="module")
def source_image():
    """加载并解码 RAW 文件，提供 PIL 图像"""
    raw_path = Path(RAW_FILE_PATH)
    if not raw_path.exists():
        pytest.skip(f"测试文件未找到: {RAW_FILE_PATH}")

    try:
        print(f"\n正在读取 RAW 文件: {raw_path.name}")
        with rawpy.imread(str(raw_path)) as raw:
            # 解码 RAW 文件为 RGB numpy 数组
            rgb_array = raw.postprocess(use_camera_wb=True, output_bps=8)

        # 转换为 PIL 图像
        image = Image.fromarray(rgb_array)
        print(f"✅ 图像尺寸: {image.size[0]} × {image.size[1]}")
        return image
    except Exception as e:
        pytest.fail(f"处理 RAW 文件失败: {e}")


def test_sky_detector_initialization():
    """测试 SkyDetector 初始化（延迟加载模式）"""
    detector = SkyDetector(model_size="b0")

    assert detector is not None
    assert detector.sky_class_index == 2
    assert detector.model_size == "b0"
    # 模型应该还未加载（延迟加载）
    assert detector._model is None
    assert detector._processor is None


def test_sky_segmentation(sky_detector_instance, source_image):
    """
    测试天空分割功能，并保存结果用于目视检查
    """
    print(f"\n正在进行天空分割... (首次运行会下载模型，请稍候)")

    # 执行分割
    mask = sky_detector_instance.segment(source_image)

    # --- 断言检查 ---
    assert isinstance(mask, np.ndarray), "蒙版应该是 numpy 数组"
    assert mask.dtype == np.uint8, "蒙版数据类型应该是 uint8"
    assert mask.ndim == 2, "蒙版应该是 2D"
    assert mask.shape == (source_image.height, source_image.width), \
        f"蒙版尺寸应与原图一致: {mask.shape} vs {(source_image.height, source_image.width)}"

    # 检查蒙版值范围
    assert mask.min() >= 0 and mask.max() <= 255, \
        f"蒙版值应在 0-255 范围内，实际: {mask.min()}-{mask.max()}"

    # 统计天空占比
    sky_pixels = np.sum(mask > 127)
    total_pixels = mask.size
    sky_percentage = (sky_pixels / total_pixels) * 100

    print(f"✅ 分割完成:")
    print(f"   天空占比: {sky_percentage:.1f}%")
    print(f"   地面占比: {100 - sky_percentage:.1f}%")

    # 保存蒙版图像
    try:
        Image.fromarray(mask).save(OUTPUT_MASK_FILENAME)
        print(f"✅ 天空蒙版已保存: {OUTPUT_MASK_FILENAME}")
        print("   请打开该文件检查分割效果")
    except Exception as e:
        pytest.fail(f"保存蒙版文件失败: {e}")


def test_get_sky_and_ground_masks(sky_detector_instance, source_image):
    """测试同时获取天空和地面蒙版"""
    print(f"\n正在生成天空和地面蒙版...")

    sky_mask, ground_mask = sky_detector_instance.get_sky_and_ground_masks(source_image)

    # 检查返回值
    assert isinstance(sky_mask, np.ndarray)
    assert isinstance(ground_mask, np.ndarray)
    assert sky_mask.shape == ground_mask.shape

    # 检查互补性（天空 + 地面 = 全图）
    combined = sky_mask.astype(np.uint16) + ground_mask.astype(np.uint16)
    assert np.allclose(combined, 255), "天空和地面蒙版应该互补"

    # 保存
    sky_filename = "sky_mask_only.png"
    ground_filename = "ground_mask_only.png"

    Image.fromarray(sky_mask).save(sky_filename)
    Image.fromarray(ground_mask).save(ground_filename)

    print(f"✅ 保存天空蒙版: {sky_filename}")
    print(f"✅ 保存地面蒙版: {ground_filename}")


def test_model_loaded_after_first_use(sky_detector_instance, source_image):
    """测试模型在首次使用后已加载"""
    # 第一次使用
    _ = sky_detector_instance.segment(source_image)

    # 检查模型已加载
    assert sky_detector_instance._model is not None, "模型应该已加载"
    assert sky_detector_instance._processor is not None, "处理器应该已加载"

    print(f"✅ 模型已加载到设备: {sky_detector_instance.device}")


if __name__ == '__main__':
    """直接运行测试"""
    print("=" * 60)
    print("SegFormer 天空检测测试")
    print("=" * 60)

    # 手动运行测试
    detector = SkyDetector(model_size="b0")

    raw_path = Path(RAW_FILE_PATH)
    if raw_path.exists():
        with rawpy.imread(str(raw_path)) as raw:
            rgb_array = raw.postprocess(use_camera_wb=True, output_bps=8)

        image = Image.fromarray(rgb_array)

        print("\n正在进行天空分割...")
        mask = detector.segment(image)

        Image.fromarray(mask).save(OUTPUT_MASK_FILENAME)
        print(f"\n✅ 测试完成！蒙版已保存: {OUTPUT_MASK_FILENAME}")
    else:
        print(f"\n❌ 测试文件未找到: {RAW_FILE_PATH}")

    print("\n" + "=" * 60)

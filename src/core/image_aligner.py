"""
图像对齐模块

使用特征检测和配准算法对齐图像，解决相机抖动问题
"""

from typing import Optional, Tuple
import numpy as np
import cv2


class ImageAligner:
    """图像对齐器 - 用于修正相机抖动"""

    def __init__(self, method: str = "orb"):
        """
        初始化对齐器

        Args:
            method: 特征检测方法
                - 'orb': ORB (快速，适合大多数情况)
                - 'sift': SIFT (更精确但较慢)
                - 'akaze': AKAZE (平衡速度和精度)
        """
        self.method = method
        self.detector = None
        self.matcher = None
        self._init_detector()

    def _init_detector(self):
        """初始化特征检测器"""
        if self.method == "orb":
            # ORB - 最快，适合星轨
            self.detector = cv2.ORB_create(
                nfeatures=2000,  # 检测更多特征点
                scaleFactor=1.2,
                nlevels=8,
                edgeThreshold=15,
            )
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        elif self.method == "akaze":
            # AKAZE - 平衡性能
            self.detector = cv2.AKAZE_create()
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        elif self.method == "sift":
            # SIFT - 最精确但最慢
            try:
                self.detector = cv2.SIFT_create(nfeatures=2000)
                self.matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
            except AttributeError:
                # SIFT 在某些 OpenCV 版本中不可用
                print("SIFT 不可用，降级使用 ORB")
                self.method = "orb"
                self._init_detector()

        else:
            raise ValueError(f"不支持的方法: {self.method}")

    def align(
        self,
        image: np.ndarray,
        reference: np.ndarray,
        max_shift: int = 50,
    ) -> Tuple[np.ndarray, bool]:
        """
        将图像对齐到参考图像

        Args:
            image: 需要对齐的图像
            reference: 参考图像（通常是第一张或平均图像）
            max_shift: 最大允许偏移量（像素），超过则认为对齐失败

        Returns:
            (对齐后的图像, 是否成功)
        """
        # 转换为灰度图
        gray_img = self._to_gray(image)
        gray_ref = self._to_gray(reference)

        # 检测特征点
        kp_img, desc_img = self.detector.detectAndCompute(gray_img, None)
        kp_ref, desc_ref = self.detector.detectAndCompute(gray_ref, None)

        # 检查是否找到足够的特征点
        if len(kp_img) < 10 or len(kp_ref) < 10:
            print(f"警告: 特征点不足 (图像: {len(kp_img)}, 参考: {len(kp_ref)})")
            return image, False

        # 特征匹配
        if desc_img is None or desc_ref is None:
            return image, False

        matches = self.matcher.match(desc_img, desc_ref)

        # 检查匹配数量
        if len(matches) < 10:
            print(f"警告: 匹配点不足 ({len(matches)} 个)")
            return image, False

        # 按距离排序，取最好的匹配
        matches = sorted(matches, key=lambda x: x.distance)
        good_matches = matches[:min(len(matches), 200)]

        # 提取匹配点坐标
        src_pts = np.float32([kp_img[m.queryIdx].pt for m in good_matches]).reshape(
            -1, 1, 2
        )
        dst_pts = np.float32([kp_ref[m.trainIdx].pt for m in good_matches]).reshape(
            -1, 1, 2
        )

        # 计算变换矩阵（仿射变换）
        try:
            # 使用 RANSAC 估计变换矩阵，过滤异常点
            M, mask = cv2.estimateAffinePartial2D(
                src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=3.0
            )

            if M is None:
                print("警告: 无法计算变换矩阵")
                return image, False

            # 检查平移量是否合理
            tx, ty = M[0, 2], M[1, 2]
            shift = np.sqrt(tx**2 + ty**2)

            if shift > max_shift:
                print(f"警告: 偏移过大 ({shift:.1f} 像素，最大 {max_shift})")
                return image, False

            # 应用变换
            h, w = reference.shape[:2]
            aligned = cv2.warpAffine(
                image,
                M,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0,
            )

            # 输出对齐信息
            inliers = np.sum(mask)
            print(
                f"对齐成功: 平移 ({tx:.1f}, {ty:.1f}) 像素, "
                f"内点: {inliers}/{len(good_matches)}"
            )

            return aligned, True

        except Exception as e:
            print(f"对齐失败: {e}")
            return image, False

    def align_simple(
        self,
        image: np.ndarray,
        reference: np.ndarray,
    ) -> np.ndarray:
        """
        简单的ECC对齐（只处理小幅度平移和旋转）

        适合星空图像，计算更快

        Args:
            image: 需要对齐的图像
            reference: 参考图像

        Returns:
            对齐后的图像
        """
        # 转换为灰度图
        gray_img = self._to_gray(image)
        gray_ref = self._to_gray(reference)

        # 缩小图像以加速
        scale = 0.5
        small_img = cv2.resize(gray_img, None, fx=scale, fy=scale)
        small_ref = cv2.resize(gray_ref, None, fx=scale, fy=scale)

        # 定义变换类型（仅平移）
        warp_mode = cv2.MOTION_TRANSLATION

        # 初始化变换矩阵
        warp_matrix = np.eye(2, 3, dtype=np.float32)

        # ECC 算法参数
        criteria = (
            cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
            1000,  # 最大迭代次数
            1e-7,  # 收敛阈值
        )

        try:
            # 计算变换矩阵
            cc, warp_matrix = cv2.findTransformECC(
                small_ref, small_img, warp_matrix, warp_mode, criteria
            )

            # 将变换矩阵缩放回原始尺寸
            warp_matrix[0, 2] /= scale
            warp_matrix[1, 2] /= scale

            # 应用变换
            h, w = reference.shape[:2]
            aligned = cv2.warpAffine(
                image,
                warp_matrix,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REPLICATE,
            )

            tx, ty = warp_matrix[0, 2], warp_matrix[1, 2]
            print(f"ECC 对齐: 平移 ({tx:.2f}, {ty:.2f}) 像素, 相关系数: {cc:.4f}")

            return aligned

        except Exception as e:
            print(f"ECC 对齐失败: {e}, 返回原图")
            return image

    @staticmethod
    def _to_gray(image: np.ndarray) -> np.ndarray:
        """转换为灰度图"""
        if len(image.shape) == 3:
            # 对于 16-bit 图像，先归一化到 8-bit
            if image.dtype == np.uint16:
                img_8bit = (image / 256).astype(np.uint8)
            else:
                img_8bit = image
            return cv2.cvtColor(img_8bit, cv2.COLOR_RGB2GRAY)
        return image

    def detect_shift(
        self, image: np.ndarray, reference: np.ndarray
    ) -> Optional[Tuple[float, float]]:
        """
        检测图像相对于参考图像的偏移量

        Args:
            image: 图像
            reference: 参考图像

        Returns:
            (x_shift, y_shift) 或 None（如果检测失败）
        """
        gray_img = self._to_gray(image)
        gray_ref = self._to_gray(reference)

        # 使用相位相关进行偏移检测（快速）
        try:
            shift, response = cv2.phaseCorrelate(
                np.float32(gray_ref), np.float32(gray_img)
            )
            return shift
        except Exception as e:
            print(f"偏移检测失败: {e}")
            return None


# 示例用法
if __name__ == "__main__":
    # 创建对齐器
    aligner = ImageAligner(method="orb")

    # 生成测试图像（带随机偏移）
    reference = np.random.randint(0, 255, (1000, 1000, 3), dtype=np.uint8)

    # 模拟抖动：平移 5 像素
    M = np.float32([[1, 0, 5], [0, 1, 3]])
    shifted = cv2.warpAffine(reference, M, (1000, 1000))

    # 对齐
    aligned, success = aligner.align(shifted, reference)

    if success:
        print("✅ 对齐测试成功")
        # 计算差异
        diff = np.abs(aligned.astype(np.float32) - reference.astype(np.float32))
        print(f"平均差异: {np.mean(diff):.2f}")
    else:
        print("❌ 对齐测试失败")

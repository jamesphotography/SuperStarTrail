"""
主窗口模块

应用程序的主界面
"""

from pathlib import Path
from typing import List
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QListWidget,
    QComboBox,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QCheckBox,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import numpy as np

from core.raw_processor import RawProcessor
from core.stacking_engine import StackingEngine, StackMode
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ProcessThread(QThread):
    """处理线程，避免阻塞 UI"""

    progress = pyqtSignal(int, int)  # 当前, 总数
    finished = pyqtSignal(np.ndarray)  # 完成信号
    error = pyqtSignal(str)  # 错误信号
    preview_update = pyqtSignal(np.ndarray)  # 预览更新
    status_message = pyqtSignal(str)  # 状态消息

    def __init__(
        self,
        file_paths: List[Path],
        stack_mode: StackMode,
        raw_params: dict,
        enable_alignment: bool = False,
        enable_gap_filling: bool = False,
        gap_fill_method: str = "morphological",
        gap_size: int = 3,
        comet_fade_factor: float = 0.98,
    ):
        super().__init__()
        self.file_paths = file_paths
        self.stack_mode = stack_mode
        self.raw_params = raw_params
        self.enable_alignment = enable_alignment
        self.enable_gap_filling = enable_gap_filling
        self.gap_fill_method = gap_fill_method
        self.gap_size = gap_size
        self.comet_fade_factor = comet_fade_factor
        self._is_running = True

    def run(self):
        """执行处理"""
        import time
        from utils.logger import setup_logger

        logger = setup_logger("ProcessThread")

        try:
            processor = RawProcessor()
            engine = StackingEngine(
                self.stack_mode,
                enable_alignment=self.enable_alignment,
                enable_gap_filling=self.enable_gap_filling,
                gap_fill_method=self.gap_fill_method,
                gap_size=self.gap_size,
            )

            # 如果是彗星模式，设置衰减因子
            if self.stack_mode == StackMode.COMET:
                engine.set_comet_fade_factor(self.comet_fade_factor)
                logger.info(f"彗星模式: 衰减因子 = {self.comet_fade_factor}")

            total = len(self.file_paths)

            # 开始处理
            mode_name = self.stack_mode.value
            logger.info(f"=" * 60)
            logger.info(f"开始星轨合成")
            logger.info(f"文件数量: {total}")
            logger.info(f"堆栈模式: {mode_name}")
            logger.info(f"白平衡: {self.raw_params.get('white_balance', 'camera')}")
            logger.info(f"图像对齐: {'启用' if self.enable_alignment else '禁用'}")
            logger.info(f"间隔填充: {'启用' if self.enable_gap_filling else '禁用'}")
            if self.enable_gap_filling:
                logger.info(f"填充方法: {self.gap_fill_method}, 间隔大小: {self.gap_size}")
            logger.info(f"=" * 60)

            self.status_message.emit(f"开始处理 {total} 张图片...")

            start_time = time.time()

            for i, path in enumerate(self.file_paths):
                if not self._is_running:
                    logger.warning("用户取消处理")
                    break

                file_start = time.time()

                # 读取并处理 RAW 文件
                logger.info(f"[{i+1:3d}/{total}] 正在处理: {path.name}")
                img = processor.process(path, **self.raw_params)

                # 添加到堆栈
                engine.add_image(img)

                file_duration = time.time() - file_start
                logger.info(f"[{i+1:3d}/{total}] 完成: {path.name} ({file_duration:.2f}秒)")

                # 发送进度
                self.progress.emit(i + 1, total)

                # 计算预计剩余时间
                elapsed = time.time() - start_time
                avg_time = elapsed / (i + 1)
                remaining = avg_time * (total - i - 1)

                status = f"处理中 [{i+1}/{total}] - 预计剩余: {remaining:.0f}秒"
                self.status_message.emit(status)

                # 每处理 5 张图片更新一次预览（不应用填充，加快速度）
                if (i + 1) % 5 == 0 or i == total - 1:
                    logger.info(f"更新预览 ({i+1}/{total})")
                    preview = engine.get_result(apply_gap_filling=False)
                    self.preview_update.emit(preview)

            # 获取最终结果
            if self._is_running:
                total_duration = time.time() - start_time
                logger.info(f"-" * 60)
                logger.info(f"✅ 堆栈完成!")
                logger.info(f"总耗时: {total_duration:.2f} 秒")
                logger.info(f"平均速度: {total_duration/total:.2f} 秒/张")

                # 应用间隔填充（如果启用）
                if self.enable_gap_filling:
                    logger.info(f"-" * 60)
                    logger.info(f"正在应用间隔填充...")
                    gap_start = time.time()

                result = engine.get_result(apply_gap_filling=True)

                if self.enable_gap_filling:
                    gap_duration = time.time() - gap_start
                    logger.info(f"间隔填充完成，耗时: {gap_duration:.2f} 秒")

                logger.info(f"=" * 60)
                self.finished.emit(result)

        except Exception as e:
            logger.error(f"处理失败: {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

    def stop(self):
        """停止处理"""
        self._is_running = False


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("彗星星轨 by James Zhen Yu")
        self.setGeometry(100, 100, 1200, 800)

        # 数据
        self.raw_files: List[Path] = []
        self.result_image: np.ndarray = None
        self.process_thread: ProcessThread = None

        # 初始化 UI
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 左侧面板（文件列表和控制）
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # 右侧面板（预览）
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)

    def create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # 文件选择组
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout()

        self.btn_select_folder = QPushButton("选择目录")
        self.btn_select_folder.clicked.connect(self.select_folder)
        file_layout.addWidget(self.btn_select_folder)

        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.preview_single_file)  # 双击预览
        file_layout.addWidget(self.file_list)

        self.label_file_count = QLabel("已选择 0 个文件")
        file_layout.addWidget(self.label_file_count)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 参数设置组
        params_group = QGroupBox("参数设置")
        params_layout = QVBoxLayout()

        # 堆栈模式选择
        params_layout.addWidget(QLabel("堆栈模式:"))
        self.combo_stack_mode = QComboBox()
        self.combo_stack_mode.addItems(
            [
                "Lighten (星轨)",
                "Average (降噪)",
                "Darken (去光污染)",
                "Comet (彗星效果)",
            ]
        )
        self.combo_stack_mode.currentIndexChanged.connect(self.on_stack_mode_changed)
        params_layout.addWidget(self.combo_stack_mode)

        # 彗星尾巴长度（仅彗星模式显示）
        self.label_comet_tail = QLabel("彗星尾巴长度:")
        self.combo_comet_tail = QComboBox()
        self.combo_comet_tail.addItems(["短 (0.95)", "中 (0.98)", "长 (0.99)"])
        self.combo_comet_tail.setCurrentIndex(2)  # 默认"长"
        self.combo_comet_tail.setToolTip(
            "控制彗星尾巴的长度\n"
            "短: 快速消失，彗星感强\n"
            "中: 适中效果（推荐）\n"
            "长: 慢慢消失，接近星轨"
        )
        params_layout.addWidget(self.label_comet_tail)
        params_layout.addWidget(self.combo_comet_tail)
        # 默认隐藏彗星选项
        self.label_comet_tail.hide()
        self.combo_comet_tail.hide()

        # 白平衡选择
        params_layout.addWidget(QLabel("白平衡:"))
        self.combo_white_balance = QComboBox()
        self.combo_white_balance.addItems(["相机白平衡", "日光", "自动"])
        params_layout.addWidget(self.combo_white_balance)

        # 间隔填充选项（最简化）
        self.check_enable_gap_filling = QCheckBox("启用间隔填充")
        self.check_enable_gap_filling.setToolTip(
            "填补星点之间的间隔，使星轨更加连续流畅\n"
            "使用形态学算法，3像素间隔（适合大部分场景）\n"
            "性能影响：几乎无（仅在最后应用一次）"
        )
        self.check_enable_gap_filling.setChecked(True)  # 默认启用
        params_layout.addWidget(self.check_enable_gap_filling)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # 处理控制
        self.btn_start = QPushButton("开始合成")
        self.btn_start.clicked.connect(self.start_processing)
        self.btn_start.setEnabled(False)
        layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        layout.addWidget(self.btn_stop)

        # 状态标签
        self.label_status = QLabel("就绪")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet("padding: 5px; background: #e8f4f8; border-radius: 3px;")
        layout.addWidget(self.label_status)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% (%v/%m)")  # 显示百分比和进度
        layout.addWidget(self.progress_bar)

        # 保存结果
        self.btn_save = QPushButton("保存结果")
        self.btn_save.clicked.connect(self.save_result)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)

        layout.addStretch()
        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧预览面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        title = QLabel("预览")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.preview_label = QLabel("请选择文件并开始处理")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "border: 1px solid #555; "
            "background: #2b2b2b; "
            "color: #e0e0e0; "
            "font-size: 14px; "
            "padding: 20px;"
        )
        self.preview_label.setMinimumSize(800, 600)
        layout.addWidget(self.preview_label)

        return panel

    def select_folder(self):
        """选择包含 RAW 文件的文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择 RAW 文件目录")
        if not folder:
            return

        folder_path = Path(folder)
        processor = RawProcessor()

        # 扫描 RAW 文件
        self.raw_files = []
        for file in folder_path.iterdir():
            if processor.is_raw_file(file):
                self.raw_files.append(file)

        # 按文件名排序（重要！确保堆栈顺序正确）
        self.raw_files.sort(key=lambda x: x.name)

        # 更新 UI
        self.file_list.clear()
        for file in self.raw_files:
            self.file_list.addItem(file.name)

        self.label_file_count.setText(f"已选择 {len(self.raw_files)} 个文件")
        self.btn_start.setEnabled(len(self.raw_files) > 0)

        # 自动预览第一张图片
        if len(self.raw_files) > 0:
            self.label_status.setText(f"正在加载预览: {self.raw_files[0].name}...")
            try:
                raw_params = self.get_raw_params()
                image = processor.process(self.raw_files[0], **raw_params)
                self.update_preview(image)
                self.label_status.setText(f"预览: {self.raw_files[0].name}")
            except Exception as e:
                self.label_status.setText(f"预览失败: {str(e)}")
                logger.error(f"自动预览第一张失败: {e}")

    def on_stack_mode_changed(self, index):
        """堆栈模式改变时的回调"""
        # 只在彗星模式(index=3)时显示尾巴长度选项
        is_comet_mode = (index == 3)
        self.label_comet_tail.setVisible(is_comet_mode)
        self.combo_comet_tail.setVisible(is_comet_mode)

    def preview_single_file(self, item):
        """预览单个NEF文件（双击文件列表时触发）"""
        # 获取选中文件的索引
        index = self.file_list.row(item)
        if 0 <= index < len(self.raw_files):
            file_path = self.raw_files[index]

            # 在状态栏显示正在加载
            self.label_status.setText(f"正在加载预览: {file_path.name}...")

            try:
                # 读取RAW文件（注意：process 方法需要 Path 对象，不是字符串）
                processor = RawProcessor()
                raw_params = self.get_raw_params()
                image = processor.process(file_path, **raw_params)

                # 更新预览
                self.update_preview(image)
                self.label_status.setText(f"预览: {file_path.name}")

            except Exception as e:
                self.label_status.setText(f"预览失败: {str(e)}")
                logger.error(f"预览文件失败: {e}")

    def get_stack_mode(self) -> StackMode:
        """获取选择的堆栈模式"""
        mode_map = {
            0: StackMode.LIGHTEN,
            1: StackMode.AVERAGE,
            2: StackMode.DARKEN,
            3: StackMode.COMET,
        }
        return mode_map[self.combo_stack_mode.currentIndex()]

    def get_raw_params(self) -> dict:
        """获取 RAW 处理参数"""
        wb_map = {0: "camera", 1: "daylight", 2: "auto"}
        return {
            "white_balance": wb_map[self.combo_white_balance.currentIndex()],
            "exposure_compensation": 0.0,
        }

    def start_processing(self):
        """开始处理"""
        if not self.raw_files:
            return

        # 禁用开始按钮，启用停止按钮
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_save.setEnabled(False)

        # 重置进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.raw_files))
        self.label_status.setText("准备开始...")

        # 使用固定的最佳参数
        gap_fill_method = "morphological"  # 形态学算法，经过测试最佳
        gap_size = 3  # 3像素，适合大部分场景

        # 获取彗星模式参数
        comet_fade_map = {
            0: 0.95,  # 短
            1: 0.98,  # 中
            2: 0.99,  # 长
        }
        comet_fade_factor = comet_fade_map[self.combo_comet_tail.currentIndex()]

        # 创建并启动处理线程
        self.process_thread = ProcessThread(
            self.raw_files,
            self.get_stack_mode(),
            self.get_raw_params(),
            enable_alignment=False,  # 星轨摄影不需要对齐
            enable_gap_filling=self.check_enable_gap_filling.isChecked(),
            gap_fill_method=gap_fill_method,
            gap_size=gap_size,
            comet_fade_factor=comet_fade_factor,
        )
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.preview_update.connect(self.update_preview)
        self.process_thread.finished.connect(self.processing_finished)
        self.process_thread.error.connect(self.processing_error)
        self.process_thread.status_message.connect(self.update_status)
        self.process_thread.start()

    def stop_processing(self):
        """停止处理"""
        if self.process_thread:
            self.process_thread.stop()
            self.btn_stop.setEnabled(False)

    def update_progress(self, current: int, total: int):
        """更新进度条"""
        self.progress_bar.setValue(current)

    def update_status(self, message: str):
        """更新状态标签"""
        self.label_status.setText(message)

    def update_preview(self, image: np.ndarray):
        """更新预览图像（自动曝光优化）"""
        # 转换为 8-bit 用于显示，使用自动拉伸提升亮度
        if image.dtype == np.uint16:
            # 使用百分位数拉伸，避免过暗或过曝
            p_low = np.percentile(image, 1)   # 1% 最暗像素
            p_high = np.percentile(image, 99.5)  # 99.5% 最亮像素

            # 拉伸到 0-255
            img_stretched = np.clip((image - p_low) / (p_high - p_low) * 255, 0, 255)
            img_8bit = img_stretched.astype(np.uint8)
        else:
            img_8bit = image

        # 缩放以适应预览窗口
        h, w = img_8bit.shape[:2]
        max_size = 800
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            from PIL import Image

            pil_img = Image.fromarray(img_8bit)
            pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
            img_8bit = np.array(pil_img)

        # 转换为 QPixmap
        h, w, c = img_8bit.shape
        bytes_per_line = c * w
        q_img = QImage(img_8bit.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        self.preview_label.setPixmap(pixmap)

    def processing_finished(self, result: np.ndarray):
        """处理完成"""
        self.result_image = result
        self.update_preview(result)

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_save.setEnabled(True)

        self.label_status.setText("✅ 合成完成！")
        self.label_status.setStyleSheet("padding: 5px; background: #d4edda; border-radius: 3px; color: #155724;")

        QMessageBox.information(self, "完成", "星轨合成完成！")

    def processing_error(self, error_msg: str):
        """处理错误"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        self.label_status.setText("❌ 处理失败")
        self.label_status.setStyleSheet("padding: 5px; background: #f8d7da; border-radius: 3px; color: #721c24;")

        QMessageBox.critical(self, "错误", f"处理失败:\n{error_msg}")

    def generate_output_filename(self) -> str:
        """生成智能输出文件名"""
        if not self.raw_files or len(self.raw_files) == 0:
            return "star_trail.tiff"

        # 提取第一张和最后一张的文件名（去掉扩展名）
        first_name = self.raw_files[0].stem  # 例如：Z9L_8996
        last_name = self.raw_files[-1].stem  # 例如：Z9L_9211

        # 提取编号部分（假设格式为 PREFIX_NUMBER）
        # 例如：Z9L_8996 → Z9L, 8996
        try:
            # 尝试分割出前缀和数字
            first_parts = first_name.rsplit('_', 1)
            last_parts = last_name.rsplit('_', 1)

            if len(first_parts) == 2 and len(last_parts) == 2:
                prefix = first_parts[0]  # Z9L
                first_num = first_parts[1]  # 8996
                last_num = last_parts[1]   # 9211
                range_str = f"{prefix}_{first_num}-{last_num}"
            else:
                # 如果分割失败，使用完整文件名
                range_str = f"{first_name}-{last_name}"
        except:
            range_str = f"{first_name}-{last_name}"

        # 堆栈模式
        mode_map = {
            0: "Lighten",
            1: "Average",
            2: "Darken",
            3: "Comet",
        }
        mode_name = mode_map.get(self.combo_stack_mode.currentIndex(), "Lighten")

        # 彗星尾巴长度（仅彗星模式）
        tail_suffix = ""
        if self.combo_stack_mode.currentIndex() == 3:  # Comet模式
            tail_map = {0: "ShortTail", 1: "MidTail", 2: "LongTail"}
            tail_suffix = "_" + tail_map.get(self.combo_comet_tail.currentIndex(), "MidTail")

        # 白平衡
        wb_map = {0: "CameraWB", 1: "Daylight", 2: "AutoWB"}
        wb_name = wb_map.get(self.combo_white_balance.currentIndex(), "CameraWB")

        # 间隔填充
        gap_suffix = "_Gapped" if self.check_enable_gap_filling.isChecked() else ""

        # 组合文件名
        filename = f"{range_str}_StarTrail_{mode_name}{tail_suffix}_{wb_name}{gap_suffix}.tif"

        return filename

    def save_result(self):
        """保存结果"""
        if self.result_image is None:
            return

        # 生成智能文件名
        default_filename = self.generate_output_filename()

        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存结果",
            default_filename,
            "TIFF Files (*.tiff *.tif);;JPEG Files (*.jpg *.jpeg);;PNG Files (*.png)",
        )

        if not file_path:
            return

        # 导出图像
        from core.exporter import ImageExporter

        exporter = ImageExporter()
        success = exporter.save_auto(self.result_image, Path(file_path))

        if success:
            QMessageBox.information(self, "成功", f"结果已保存到:\n{file_path}")
        else:
            QMessageBox.critical(self, "错误", "保存失败")
